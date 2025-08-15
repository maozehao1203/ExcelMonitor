import json, pandas as pd, plotly.graph_objects as go
import sys
from pathlib import Path
from datetime import date

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent  # PyInstaller 打包后的 .exe 所在目录
else:
    BASE_DIR = Path(__file__).parent  # 脚本运行时所在目录
# 1. 读 JSON
records = json.loads(Path(BASE_DIR / 'result' / 'filter_result.json').read_text(encoding='utf-8'))

# 2. 转 DataFrame
df = pd.DataFrame(records)
df['date'] = pd.to_datetime(df['date'])

# === 新增：今日饼图所需数据 ===
today = pd.Timestamp('today').normalize()
prev = df[df['date'] < today]['date'].max()

prev_df = df[df['date'] == prev].set_index('tag')['matched_count']
delta = {t: df[df['date'] == today].set_index('tag').loc[t, 'matched_count'] - prev_df.get(t, 0)
         for t in df[df['date'] == today]['tag']}


# 颜色映射
def sign_color(d):
    if d > 0:
        return 'red'
    elif d < 0:
        return 'green'
    return 'black'


fig = go.Figure()
for tag, g in df.groupby('tag'):
    g = g.sort_values('date')
    cur = df[df['date'] == today].set_index('tag').loc[tag, 'matched_count']
    d = delta[tag]

    if d > 0:
        sign = '+'
        color = 'red'
    elif d < 0:
        sign = '-'
        color = 'green'
    else:
        sign = ''
        color = 'black'

    legend = f'{tag} ({cur} |  <span style="color:{color};">{sign}{abs(d)}</span>)'
    fig.add_trace(go.Scatter(
        x=g['date'], y=g['matched_count'],
        mode='lines+markers', name=legend,
        hovertemplate='%{fullData.name}<br>%{y}<extra></extra>'
    ))
fig.update_layout(
    title='匹配数量 随 日期 变化',
    xaxis_title='日期', yaxis_title='匹配数量'
)

pie_df = df[df['date'] == today].groupby('tag', as_index=False)['matched_count'].sum()

from plotly.subplots import make_subplots

fig2 = make_subplots(
    rows=2, cols=1,
    specs=[[{"type": "scatter"}], [{"type": "pie"}]],
    subplot_titles=['匹配数量随日期变化', '今日各标签数量'],
    vertical_spacing=0.15
)
# 把折线图的所有 trace 搬到 fig2
for trace in fig.data:
    fig2.add_trace(trace, row=1, col=1)
# 加饼图
fig2.add_trace(
    go.Pie(labels=pie_df['tag'], values=pie_df['matched_count'],
           textinfo='label+percent', showlegend=False), row=2, col=1
)
fig2.update_layout(height=900)

# 4. 输出离线 HTML（文件名不变，覆盖）
fig2.write_html('trend.html', auto_open=True)
