import yaml
import json
import hashlib
from pathlib import Path

class TagManager:
    def __init__(self, cfg):
        self.cfg = cfg
        self.last_tags_file = cfg['BASE_DIR'] / 'config' / 'last_tags.yaml'

    # 原 tag_sig 函数
    def tag_sig(self, group: dict) -> str:
        content = f"{group['tag']}:{json.dumps(group['conditions'], sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()

    # 原 4. + 4.x 整体搬入
    def check_tag_changes(self, filter_groups):
        last_tags = yaml.safe_load(open(self.last_tags_file, encoding='utf-8')) or {} \
            if self.last_tags_file.exists() else {}
        current_sigs = {self.tag_sig(g) for g in filter_groups}
        changed_or_new_tags = {g["tag"] for g in filter_groups if self.tag_sig(g) not in last_tags} or \
                              (last_tags.keys() - current_sigs and {"__ANY__"})
        run_history = bool(changed_or_new_tags)

        # 4.x 处理 tag 减少
        previous_tags = set(last_tags.values()) if last_tags else set()
        present_tags = {g["tag"] for g in filter_groups}
        if previous_tags is not None:
            removed_tags = [tag for tag in previous_tags if tag not in present_tags]
            if removed_tags:
                print(f"以下标签已缺失: {removed_tags}")
                out_file = self.cfg['BASE_DIR'] / 'result' / 'filter_result.json'
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

        return run_history