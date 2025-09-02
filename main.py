from data_collect_utils.config_loader import load_config
from data_collect_utils.cache_manager import CacheManager
from data_collect_utils.tag_manager import TagManager
from data_collect_utils.filter_engine import FilterEngine
from data_collect_utils.utils import save_changes


def main():
    # 加载配置
    cfg = load_config()

    # 初始化管理器
    cache_manager = CacheManager(cfg)
    tag_manager = TagManager(cfg)

    # 处理缓存
    cache_manager.process_cache()

    # 检查标签变更
    run_history = tag_manager.check_tag_changes(cfg['filter_groups'])

    # 执行过滤计算
    filter_engine = FilterEngine(cfg, cache_manager, tag_manager)
    filter_engine.run_filter(run_history)

    # 保存变更数据
    save_changes(cfg, cache_manager)


if __name__ == "__main__":
    main()