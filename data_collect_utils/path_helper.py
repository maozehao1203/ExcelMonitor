import sys
from pathlib import Path


def get_project_root() -> Path:
    """返回运行时根目录（即 main.py 所在目录）"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        return Path(sys.executable).parent
    else:
        # 普通运行
        return Path.cwd()
