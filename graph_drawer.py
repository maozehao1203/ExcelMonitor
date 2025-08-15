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
pie_df = df[df['date'] == today].groupby('tag', as_index=False)['matched_count'].sum()

# 3. 折线图（原逻辑不变）
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

# === 新增：在折线图下方追加饼图 ===
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
           textinfo='label+percent', showlegend=False),
    row=2, col=1
)
# 计算今天 vs 前一天
prev = df[df['date'] < today]['date'].max()
# 去重后再算环比
pie_df = df[df['date'] == today].groupby('tag', as_index=False)['matched_count'].sum()
prev_df = df[df['date'] == prev].groupby('tag')['matched_count'].sum()
delta = pie_df.set_index('tag')['matched_count'] - prev_df.reindex(pie_df['tag'], fill_value=0)

delta_html = '<br>'.join(
    f"<span>{k}:</span> <span style='color:red'>+{v}</span>" if v > 0 else
    f"<span>{k}:</span> <span style='color:green'>-{abs(v)}</span>" if v < 0 else
    f"<span>{k}:</span> --"
    for k, v in delta.items()
)

fig2.add_annotation(text=delta_html, xref='paper', yref='paper',
                    x=1, y=1, showarrow=False, align='left')

fig2.update_layout(height=900)

# 4. 输出离线 HTML（文件名不变，覆盖）
fig2.write_html('trend.html', auto_open=True)
