import json
import pandas as pd
from graph_draw_utils.constants import BASE_DIR


def load_data():
    records = json.loads(
        (BASE_DIR / 'result' / 'filter_result.json').read_text(encoding='utf-8')
    )
    df = pd.DataFrame(records)
    df['date'] = pd.to_datetime(df['date'])
    return df
