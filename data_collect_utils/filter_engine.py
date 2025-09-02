import json
import pandas as pd
from pathlib import Path

from data_collect_utils.path_helper import get_project_root


class FilterEngine:
    def __init__(self, cfg, cache_manager, tag_manager):
        self.cfg = cfg
        self.cache_manager = cache_manager
        self.tag_manager = tag_manager
        self.out_file = get_project_root() / 'result' / 'filter_result.json'
        self.out_file.parent.mkdir(parents=True, exist_ok=True)

    def run_filter(self, run_history):
        history = self._load_history()
        fresh_records = []

        # 计算今天
        for sheet_name, date_path_list in self.cache_manager.sheet_pq_map.items():
            today_path = None
            for date_str, pq_path in date_path_list:
                if date_str == self.cache_manager.today:
                    today_path = pq_path
                    break
            if today_path is None:
                continue

            df_today = pd.read_parquet(today_path)
            self._calc_for_date(df_today, sheet_name, self.cache_manager.today, None, fresh_records)

        # 计算历史
        if run_history:
            for sheet_name, date_path_list in self.cache_manager.sheet_pq_map.items():
                for date_str, pq_path in date_path_list:
                    if date_str == self.cache_manager.today:
                        continue
                    df = pd.read_parquet(pq_path)
                    changed_or_new_tags = {g["tag"] for g in self.cfg['filter_groups']
                                           if self.tag_manager.tag_sig(g) not in
                                           (self.tag_manager.last_tags_file.exists() and
                                            json.load(open(self.tag_manager.last_tags_file)) or {})}
                    self._calc_for_date(df, sheet_name, date_str, changed_or_new_tags, fresh_records)

        # 更新历史记录
        target_sheets = [self.cfg['sheet_name']] if self.cfg['sheet_name'] else \
            list(self.cache_manager.sheet_pq_map.keys())

        history = [
            h for h in history
            if not (
                    h.get("path_url") == str(self.cfg['path_url']) and
                    h.get("sheet_name") in target_sheets and
                    h.get("date") == self.cache_manager.today
            )
        ]

        history.extend(fresh_records)
        json.dump(history, open(self.out_file, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=2)

        print(f"[SUCCEED] 已输出 {len(fresh_records)} 条记录，结果已更新到 {self.out_file}")

    def _load_history(self):
        if self.out_file.exists():
            try:
                history = json.load(open(self.out_file, encoding='utf-8'))
                return history if isinstance(history, list) else [history]
            except json.JSONDecodeError:
                return []
        return []

    def _calc_for_date(self, df, sheet_name, date_str, tag_set, fresh_records):
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

            fresh_records.append({
                "path_url": str(self.cfg['path_url']),
                "sheet_name": sheet_name,
                "date": date_str,
                "tag": group["tag"],
                "filter_conditions": group["conditions"],
                "matched_count": int(mask.sum())
            })