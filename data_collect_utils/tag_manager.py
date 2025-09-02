import yaml
import json
import hashlib
from pathlib import Path

from data_collect_utils.path_helper import get_project_root


def _handle_removed_tags(filter_groups, last_tags):
    previous_tags = set(last_tags.values()) if last_tags else set()
    present_tags = {g["tag"] for g in filter_groups}

    if previous_tags is not None:
        removed_tags = [tag for tag in previous_tags if tag not in present_tags]
        if removed_tags:
            print(f"以下标签已缺失: {removed_tags}")
            out_file = Path(__file__).parent / 'result' / 'filter_result.json'
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


def tag_sig(group: dict) -> str:
    import json
    content = f"{group['tag']}:{json.dumps(group['conditions'], sort_keys=True)}"
    return hashlib.md5(content.encode()).hexdigest()


class TagManager:
    def __init__(self, cfg):
        self.cfg = cfg
        self.last_tags_file = get_project_root() / 'config' / 'last_tags.yaml'

    def check_tag_changes(self, filter_groups):
        last_tags = yaml.safe_load(open(self.last_tags_file, encoding='utf-8')) or {} \
            if self.last_tags_file.exists() else {}

        current_sigs = {tag_sig(g) for g in filter_groups}
        changed_or_new_tags = {g["tag"] for g in filter_groups
                               if tag_sig(g) not in last_tags} or \
                              (last_tags.keys() - {tag_sig(g) for g in filter_groups} and {"__ANY__"})
        run_history = bool(changed_or_new_tags)

        _handle_removed_tags(filter_groups, last_tags)

        if run_history:
            print("[INFO] 检测到新增/变更 tag，将补算历史日期")
        else:
            print("[INFO] 无新增/变更 tag，仅计算今天")

        return run_history

    def update_last_tags(self, filter_groups, changed_or_new_tags):
        if changed_or_new_tags:
            new_tags = {tag_sig(g): g["tag"] for g in filter_groups}
            yaml.dump(new_tags,
                      open(self.last_tags_file, 'w', encoding='utf-8'),
                      allow_unicode=True)