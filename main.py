from __future__ import annotations

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import sys
import yaml
import hashlib

# ---------- 0. 获取程序根目录 ----------
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent  # PyInstaller 打包后的 .exe 所在目录
else:
    BASE_DIR = Path(__file__).parent  # 脚本运行时所在目录

# ---------- 1. 读取外部 YAML 配置 ----------
config_file = BASE_DIR / 'config' / 'config.yaml'   # 改成 .yaml
with open(config_file, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)       # 读取 YAML

path_url = cfg['path_url']
sheet_name = cfg['sheet_name']
filter_groups = cfg['filter_groups']

excel_path = BASE_DIR / Path(path_url)
excel_stem = excel_path.stem

# ---------- 2. 工具 ----------
def tag_sig(group: dict) -> str:
    content = f"{group['tag']}:{json.dumps(group['conditions'], sort_keys=True)}"
    return hashlib.md5(content.encode()).hexdigest()

# ---------- 3. 新的三级目录缓存 ----------
pq_root = BASE_DIR / 'parquet_cache'
today   = datetime.now().strftime('%Y-%m-%d')

with pd.ExcelFile(excel_path, engine='calamine') as xls:
    all_sheets = xls.sheet_names

# 需要处理的 sheet
sheets_this_run = [sheet_name] if sheet_name else all_sheets

for sht in sheets_this_run:
    pq_dir  = pq_root / excel_stem / sht
    pq_dir.mkdir(parents=True, exist_ok=True)
    pq_file = pq_dir / f"{today}.parquet"

    # 始终更新今天的缓存
    df_sheet = pd.read_excel(excel_path, sheet_name=sht, engine='calamine')
    for col in df_sheet.columns:
        df_sheet[col] = df_sheet[col].astype(str)
    df_sheet.to_parquet(pq_file, index=False)
    print(f"[CACHE] 已更新 parquet：{pq_file}")

# ---------- 4. 判断是否有新增/变更/减少 tag ----------
last_tags_file = BASE_DIR / 'config' / 'last_tags.yaml'
last_tags = yaml.safe_load(open(last_tags_file, encoding='utf-8')) or {} \
            if last_tags_file.exists() else {}

current_sigs = {tag_sig(g) for g in filter_groups}
changed_or_new_tags = {g["tag"] for g in filter_groups if tag_sig(g) not in last_tags} or \
                      (last_tags.keys() - {tag_sig(g) for g in filter_groups} and {"__ANY__"})
run_history = bool(changed_or_new_tags)

# 4.x 处理 tag 减少
# 读 last_tags.yaml，直接拿到上次所有的 tag 名
previous_tags = set(last_tags.values()) if last_tags else set()
present_tags= {g["tag"] for g in filter_groups}
if len(previous_tags)> len(present_tags):
    removed_tags = previous_tags - present_tags
    if removed_tags:
        print(f"[INFO] 检测到减少的 tag：{removed_tags}，将删除所有历史记录")
        out_file = BASE_DIR / 'result' / 'filter_result.json'
        if out_file.exists():
            try:
                history = json.load(open(out_file, encoding='utf-8'))
                history = history if isinstance(history, list) else [history]
            except json.JSONDecodeError:
                history = []
        else:
            history = []
        history = [h for h in history if h.get("tag") not in removed_tags]
        json.dump(history, open(out_file, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=2)
if run_history:
    print("[INFO] 检测到新增/变更 tag，将补算历史日期")
else:
    print("[INFO] 无新增/变更 tag，仅计算今天")

# ---------- 5. 找出同一表格、同一 sheet 的所有历史 parquet ----------
target_sheets = [sheet_name] if sheet_name else all_sheets
sheet_pq_map = {}            # {sheet: [(date, Path)]}
for sht in target_sheets:
    pq_dir = pq_root / excel_stem / sht
    if not pq_dir.exists():
        continue
    pq_files = sorted(pq_dir.glob("*.parquet"))
    sheet_pq_map[sht] = [(p.stem, p) for p in pq_files]

if not sheet_pq_map:
    print("[WARN] 找不到任何 parquet，请先确保 Excel 能被读取")
    sys.exit(1)

# ---------- 6. 结果文件 ----------
out_file = BASE_DIR / 'result' / 'filter_result.json'
out_file.parent.mkdir(parents=True, exist_ok=True)

# 6.1 读历史
if out_file.exists():
    try:
        history = json.load(open(out_file, encoding='utf-8'))
        history = history if isinstance(history, list) else [history]
    except json.JSONDecodeError:
        history = []
else:
    history = []

# 6.2 需要写入的新增/变更记录
fresh_records = []

def calc_for_date(df: pd.DataFrame, sheet_name: str, date_str: str, tag_set: set | None = None):
    """
    对给定日期数据计算过滤结果
    :param tag_set: 只计算这些 tag；None 表示所有 filter_groups
    """
    for group in filter_groups:
        if tag_set is not None and group["tag"] not in tag_set:
            continue
        mask = pd.Series([True] * len(df))
        skip = 0
        for col, vals in group["conditions"].items():
            if col not in df.columns:
                skip += 1
                continue
            vals = [str(v) for v in (vals if isinstance(vals, list) else [vals])]
            mask &= df[col].isin(vals)
        if skip == len(group["conditions"]):
            continue
        fresh_records.append({
            "path_url": str(path_url),
            "sheet_name": sheet_name,
            "date": date_str,
            "tag": group["tag"],
            "filter_conditions": group["conditions"],
            "matched_count": int(mask.sum())
        })

# （1）无论有没有新增/变更 tag，先算今天
for sheet_name, date_path_list in sheet_pq_map.items():
    today_path = None
    for date_str, pq_path in date_path_list:
        if date_str == today:
            today_path = pq_path
            break
    if today_path is None:
        continue
    df_today = pd.read_parquet(today_path)
    calc_for_date(df_today, sheet_name, today)

# （2）如果需要跑历史，再算历史（不含今天）
if run_history:
    for sheet_name, date_path_list in sheet_pq_map.items():
        for date_str, pq_path in date_path_list:
            if date_str == today:
                continue
            df = pd.read_parquet(pq_path)
            calc_for_date(df, sheet_name, date_str, tag_set=changed_or_new_tags)

# 6.3 删除这些新增/变更 tag 在对应 sheet 的旧记录（不含今天）
if run_history:
    history = [
        h for h in history
        if not (
            h.get("path_url") == str(path_url) and
            h.get("tag") in changed_or_new_tags and
            h.get("sheet_name") in target_sheets and
            h.get("date") != today          # 保留今天的记录
        )
    ]

history.extend(fresh_records)
json.dump(history, open(out_file, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)

# ---------- 7. 更新 last_tags ----------
if changed_or_new_tags:
    new_tags = {tag_sig(g): g["tag"] for g in filter_groups}  # 值写 tag 名
    yaml.dump(new_tags,
              open(last_tags_file, 'w', encoding='utf-8'),
              allow_unicode=True)

print(f"[SUCCEED] 已输出 {len(fresh_records)} 条记录，结果已更新到 {out_file}")