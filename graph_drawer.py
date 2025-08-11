import json, pandas as pd, plotly.graph_objects as go
import sys
from pathlib import Path
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent  # PyInstaller 打包后的 .exe 所在目录
else:
    BASE_DIR = Path(__file__).parent  # 脚本运行时所在目录
# 1. 读 JSON
records = json.loads(Path(BASE_DIR/'result'/'filter_result.json').read_text(encoding='utf-8'))

# 2. 转 DataFrame
df = pd.DataFrame(records)
df['date'] = pd.to_datetime(df['date'])

# 3. 画图
fig = go.Figure()
for tag, g in df.groupby('tag'):
    g = g.sort_values('date')
    fig.add_trace(go.Scatter(
        x=g['date'], y=g['matched_count'],
        mode='lines+markers', name=tag
    ))

fig.update_layout(
    title='匹配数量 随 日期 变化',
    xaxis_title='日期', yaxis_title='匹配数量'
)

# 4. 输出离线 HTML
fig.write_html('trend.html', auto_open=True)