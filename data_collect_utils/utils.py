import json
import pandas as pd
from pathlib import Path
import yaml


# 原 diff_rows 函数原样搬入
def diff_rows(path1: str, path2: str, track_key: str, track_key2: str,
              column_name: str, details: bool = False):
    df1 = pd.read_parquet(path1, columns=[column_name])
    df2 = pd.read_parquet(path2, columns=[column_name])
    df_key = pd.read_parquet(path2, columns=[track_key])
    df_key2 = pd.read_parquet(path2, columns=[track_key2])

    if column_name not in df1.columns or column_name not in df2.columns:
        raise KeyError(f"列 '{column_name}' 不存在于某个 parquet 文件中")

    min_rows = min(len(df1), len(df2))
    df1, df2 = df1.iloc[:min_rows], df2.iloc[:min_rows]
    mask = df1[column_name] != df2[column_name]
    diff_idx = mask[mask].index

    if not details:
        return diff_idx.tolist()

    return [
        {
            "row": int(i) + 2,
            "key": df_key2.loc[i, track_key2] if df_key.loc[i, track_key] == "nan" else df_key.loc[i, track_key],
            "from": df1.loc[i, column_name],
            "to": df2.loc[i, column_name],
        }
        for i in diff_idx
    ]


# 原“保存差异”段
def diff_rows_and_save(cfg, cache):
    pq_files = []
    for _, date_path_list in cache.sheet_pq_map.items():
        pq_files.extend([p for _, p in date_path_list])
    if len(pq_files) < 2:
        return
    path1, path2 = pq_files[-2], pq_files[-1]
    changes = diff_rows(path1, path2,
                        cfg["track_key"], cfg["track_key2"],
                        cfg["track_column"], details=True)
    changes_output_path = cfg['BASE_DIR'] / 'result' / 'filter_changes.json'
    changes_output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(changes_output_path, 'w', encoding='utf-8') as f:
        json.dump(changes, f, ensure_ascii=False, indent=2)
    print(changes)


# 原“更新 last_tags”段
def update_last_tags(cfg, tag_mgr):
    # 这里直接用 cfg 里已经算出的 changed_or_new_tags 标记位即可
    # 为了最小改动，沿用原逻辑
    last_tags_file = cfg['BASE_DIR'] / 'config' / 'last_tags.yaml'
    new_tags = {tag_mgr.tag_sig(g): g["tag"] for g in cfg['filter_groups']}
    yaml.dump(new_tags, open(last_tags_file, 'w', encoding='utf-8'),
              allow_unicode=True)
