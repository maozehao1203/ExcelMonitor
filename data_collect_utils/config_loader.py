import sys
import yaml
from pathlib import Path

from data_collect_utils.path_helper import get_project_root


def load_config():
    """按原main.py逻辑加载yaml并返回cfg字典"""
    config_name = 'config.yaml'
    general_group = 'general_group.yaml'
    filter_group_name = general_group

    config_file_dir = get_project_root() / 'config' / config_name
    filter_group_dir = get_project_root() / 'config' / 'groups' / filter_group_name

    with open(config_file_dir, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    with open(filter_group_dir, "r", encoding="utf-8") as f:
        custom_filters = yaml.safe_load(f)

    cfg["filter_groups"] = custom_filters
    cfg['BASE_DIR'] = get_project_root()  # 向后传递
    return cfg
