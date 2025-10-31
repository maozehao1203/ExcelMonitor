from pathlib import Path
from data_collect_utils import config_loader
from data_collect_utils.cache_manager import CacheManager
from data_collect_utils.tag_manager import TagManager
from data_collect_utils.filter_engine import FilterEngine
from data_collect_utils.utils import diff_rows_and_save, update_last_tags


def main():
    cfg = config_loader.load_config()
    cache = CacheManager(cfg)
    cache.process_cache()

    tag_mgr = TagManager(cfg)
    run_hist = tag_mgr.check_tag_changes(cfg['filter_groups'])

    engine = FilterEngine(cfg, cache, tag_mgr)
    engine.run_filter(run_hist)

    diff_rows_and_save(cfg, cache)
    update_last_tags(cfg, tag_mgr)


if __name__ == "__main__":
    main()
