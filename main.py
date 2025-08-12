import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import sys
import yaml

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

# ---------- 2. 读取 Excel ----------
df = pd.read_excel(BASE_DIR / Path(path_url), sheet_name=sheet_name, engine='calamine')

# ---------- 3. 统一转字符串 ----------
cols_needed = {col for g in filter_groups for col in g["conditions"]}
for col in cols_needed:
    if col in df.columns:
        df[col] = df[col].astype(str)

# ---------- 4. 统计 ----------
today = datetime.now().strftime('%Y-%m-%d')
output_file = BASE_DIR / 'result' / 'filter_result.json'
output_file.parent.mkdir(parents=True, exist_ok=True)  # 若 result 目录不存在则创建

results = []
for group in filter_groups:
    mask = pd.Series([True] * len(df))
    skip_count = 0
    for col, vals in group["conditions"].items():
        if col not in df.columns:
            print("[FAILED]", "【tag:" + group["tag"] + "】", "column", col, "not exist,skip")
            skip_count += 1
            continue
        vals = [str(v) for v in (vals if isinstance(vals, list) else [vals])]
        mask &= df[col].isin(vals)
        print("[SUCCEED]", "【tag:" + group["tag"] + "】", "column", col, "exist")
    count = int(mask.sum())
    if skip_count < len(group["conditions"]):
        results.append({
            "path_url": str(path_url),
            "sheet_name": sheet_name,
            "date": today,
            "tag": group["tag"],
            "filter_conditions": group["conditions"],
            "matched_count": count
        })
        print("[SUCCEED]", "【tag:" + group["tag"] + "】", "count is", count)
    else:
        print("[FAILED]", "【tag:" + group["tag"] + "】", "all condition skipped,invalid query")

# ---------- 5. 追加写并去重 ----------
if output_file.exists():
    with open(output_file, 'r', encoding='utf-8') as f:
        try:
            history = json.load(f)
            if not isinstance(history, list):
                history = [history]
        except json.JSONDecodeError:
            history = []
else:
    history = []

history = [
    h for h in history
    if not (
            h.get("path_url") == str(path_url) and
            h.get("date") == today and
            h.get("sheet_name") == sheet_name and
            h.get("tag") in {g["tag"] for g in filter_groups}
    )
]

history.extend(results)
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

print(f'[SUCCEED] 已处理 {len(filter_groups)} 组条件（支持多选），结果已追加至 {output_file}')