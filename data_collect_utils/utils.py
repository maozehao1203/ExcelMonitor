import pandas as pd
import json
from pathlib import Path

from data_collect_utils.path_helper import get_project_root


def diff_rows(path1, path2, track_key, track_key2, column_name, details=False):
    df1 = pd.read_parquet(path1, columns=[column_name])
    df2 = pd.read_parquet(path2, columns=[column_name])

    df_key = pd.read_parquet(path2, columns=[track_key])
    df_key2 = pd.read_parquet(path2, columns=[track_key2])

    if column_name not in df1.columns or column_name not in df2.columns:
        raise KeyError(f"列 '{column_name}' 不存在于某个 parquet 文件中")

    min_rows = min(len(df1), len(df2))
    df1 = df1.iloc[:min_rows]
    df2 = df2.iloc[:min_rows]

    mask = df1[column_name] != df2[column_name]
    diff_idx = mask[mask].index

    if not details:
        return diff_idx.tolist()

    records = [
        {
            "row": int(i) + 2,
            "key": df_key2.loc[i, track_key2] if df_key.loc[i, track_key] == "nan" else df_key.loc[i, track_key],
            "from": df1.loc[i, column_name],
            "to": df2.loc[i, column_name],
        }
        for i in diff_idx
    ]
    return records


def save_changes(cfg, cache_manager):
    pq_files = []
    for _, date_path_list in cache_manager.sheet_pq_map.items():
        pq_files.extend([p for _, p in date_path_list])

    if len(pq_files) >= 2:
        path1 = pq_files[-2]
        path2 = pq_files[-1]

        changes = diff_rows(
            path1, path2,
            cfg["track_key"],
            cfg["track_key2"],
            cfg["track_column"],
            details=True
        )

        changes_output_path = get_project_root() / 'result' / 'filter_changes.json'
        changes_output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(changes_output_path, 'w', encoding='utf-8') as f:
            json.dump(changes, f, ensure_ascii=False, indent=2)

        print(changes)