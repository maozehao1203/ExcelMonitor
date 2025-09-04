import json
import pandas as pd
from pathlib import Path
import yaml

class FilterEngine:
    def __init__(self, cfg, cache_manager, tag_manager):
        self.cfg = cfg
        self.cache = cache_manager
        self.tag_mgr = tag_manager
        self.out_file = cfg['BASE_DIR'] / 'result' / 'filter_result.json'
        self.out_file.parent.mkdir(parents=True, exist_ok=True)

    # 原 _calc_for_date 搬入
    def _calc_for_date(self, df, sheet_name, date_str, tag_set=None, records=None):
        if records is None:
            records = []
        for group in self.cfg['filter_groups']:
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
            records.append({
                "path_url": str(self.cfg['path_url']),
                "sheet_name": sheet_name,
                "date": date_str,
                "tag": group["tag"],
                "filter_conditions": group["conditions"],
                "matched_count": int(mask.sum())
            })

    # 原 6.1 读历史
    def _load_history(self):
        if not self.out_file.exists():
            return []
        try:
            history = json.load(open(self.out_file, encoding='utf-8'))
            return history if isinstance(history, list) else [history]
        except json.JSONDecodeError:
            return []

    # 主入口：原 6.2 + 历史补算（同之前给过的代码）
    def run_filter(self, run_history: bool):
        history = self._load_history()
        fresh_records = []

        today = self.cache.today
        target_sheets = [self.cfg['sheet_name']] if self.cfg['sheet_name'] else \
                       list(self.cache.sheet_pq_map.keys())

        # 1 算今天
        for sheet_name, date_path_list in self.cache.sheet_pq_map.items():
            for date_str, pq_path in date_path_list:
                if date_str == today:
                    df_today = pd.read_parquet(pq_path)
                    self._calc_for_date(df_today, sheet_name, today, None, fresh_records)
                    break

        # 2 补历史
        if run_history:
            changed_tags = {
                g["tag"] for g in self.cfg['filter_groups']
                if self.tag_mgr.tag_sig(g) not in
                (yaml.safe_load(open(self.tag_mgr.last_tags_file))
                 if self.tag_mgr.last_tags_file.exists() else {})
            }
            for sheet_name, date_path_list in self.cache.sheet_pq_map.items():
                for date_str, pq_path in date_path_list:
                    if date_str == today:
                        continue
                    df_hist = pd.read_parquet(pq_path)
                    self._calc_for_date(df_hist, sheet_name, date_str, changed_tags, fresh_records)

        # 3 去重 + 合并 + 写回
        history = [
            h for h in history
            if not (
                h.get("path_url") == str(self.cfg['path_url']) and
                h.get("sheet_name") in target_sheets and
                h.get("date") == today
            )
        ]
        history.extend(fresh_records)
        json.dump(history, open(self.out_file, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=2)
        print(f"[SUCCEED] 已输出 {len(fresh_records)} 条记录，结果已更新到 {self.out_file}")