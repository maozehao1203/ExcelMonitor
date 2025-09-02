import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

from data_collect_utils.path_helper import get_project_root


class CacheManager:
    def __init__(self, cfg):
        self.cfg = cfg
        self.path_url = cfg['path_url']
        self.sheet_name = cfg['sheet_name']
        self.excel_path = get_project_root() / self.path_url
        self.excel_stem = self.excel_path.stem

        self.pq_root = get_project_root() / 'parquet_cache'
        self.today = datetime.today().strftime('%Y-%m-%d')
        self.yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        self.sheet_pq_map = {}

    def process_cache(self):
        with pd.ExcelFile(self.excel_path, engine='calamine') as xls:
            all_sheets = xls.sheet_names

        sheets_this_run = [self.sheet_name] if self.sheet_name else all_sheets

        for sht in sheets_this_run:
            pq_dir = self.pq_root / self.excel_stem / sht
            pq_dir.mkdir(parents=True, exist_ok=True)
            pq_file = pq_dir / f"{self.today}.parquet"

            df_sheet = pd.read_excel(self.excel_path, sheet_name=sht, engine='calamine')
            for track_col in df_sheet.columns:
                df_sheet[track_col] = df_sheet[track_col].astype(str)
            df_sheet.to_parquet(pq_file, index=False)
            print(f"[CACHE] 已更新 parquet：{pq_file}")

        self._backup_original()
        self._build_sheet_map(all_sheets)

    def _backup_original(self):
        backup_dir = self.pq_root / self.excel_stem
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_today = backup_dir / f"{self.excel_stem}_{self.today}.xlsx"
        backup_today.write_bytes(self.excel_path.read_bytes())

        for bk in backup_dir.glob(f"{self.excel_stem}_*.xlsx"):
            if bk.stem.split('_')[-1] not in {self.today, self.yesterday}:
                bk.unlink()

    def _build_sheet_map(self, all_sheets):
        target_sheets = [self.sheet_name] if self.sheet_name else all_sheets
        for sht in target_sheets:
            pq_dir = self.pq_root / self.excel_stem / sht
            if not pq_dir.exists():
                continue
            pq_files = sorted(pq_dir.glob("*.parquet"))
            self.sheet_pq_map[sht] = [(p.stem, p) for p in pq_files]