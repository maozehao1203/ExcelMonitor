import yaml
import sys
from pathlib import Path

from data_collect_utils.path_helper import get_project_root


def load_config():
    # ---------- 0. 获取程序根目录 ----------
    base_dir = get_project_root()
    # ---------- 1. 读取外部 YAML 配置 ----------
    config_name = 'config.yaml'
    general_group = 'general_group.yaml'

    config_file_dir = base_dir / 'config' / config_name
    filter_group_dir = base_dir / 'config' / 'groups' / general_group

    with open(config_file_dir, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    with open(filter_group_dir, "r", encoding="utf-8") as f:
        custom_filters = yaml.safe_load(f)

    cfg["filter_groups"] = custom_filters
    return cfg
