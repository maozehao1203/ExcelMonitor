import json, pandas as pd, plotly.graph_objects as go
import sys
from pathlib import Path
from datetime import datetime


exclude_tags = {}

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

    legend = f'{tag} (今日值 {cur} |  较昨日 <span style="color:{color};">{sign}{abs(d)}</span>)'
    fig.add_trace(go.Scatter(
        x=g['date'], y=g['matched_count'],
        mode='lines+markers', name=legend,
        hovertemplate='%{fullData.name}<br>%{y}<extra></extra>'
    ))
fig.update_layout(
    title='匹配数量 随 日期 变化',
    xaxis_title='日期', yaxis_title='匹配数量'
)

pie_df = (df[df['date'] == today]
          .groupby('tag', as_index=False)['matched_count']
          .sum()
          .query("tag not in @exclude_tags"))

today_count_df = (df[df['date'] == today]
          .groupby('tag', as_index=False)['matched_count']
          .sum())

# ===== 今日合计 =====
today_total = int(today_count_df['matched_count'].sum())          # 今日匹配总数
update_time=datetime.now().replace(second=0, microsecond=0).strftime('%Y-%m-%d %H:%M')
prev_total  = int(prev_df.sum())                          # 昨日匹配总数
total_delta = today_total - prev_total                    # 增减量

sign = '+' if total_delta > 0 else ('' if total_delta == 0 else '-')
delta_color = 'red' if total_delta > 0 else ('black' if total_delta == 0 else 'green')
delta_str = f'{sign}{abs(total_delta)}'                   # 例如 “+23” 或 “-5”

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
    go.Pie(
        labels=pie_df['tag'],
        values=pie_df['matched_count'],
        textinfo='label+percent',
        textposition='auto',
        insidetextorientation='horizontal',
        showlegend=False
    ),
    row=2, col=1
)
fig2.update_layout(height=900)
# 在图最上方插入今日合计
fig2.add_annotation(
    text=f"于{update_time}更新，今日合计：<b>{today_total}</b> 条（较昨日 <span style='color:{delta_color};'>{delta_str}</span>）",
    x=0.5, y=1.08,                       # 相对整个画布的坐标
    xref="paper", yref="paper",
    showarrow=False,
    font=dict(size=16)
)

fig2.update_layout(height=950)           # 稍微拉高画布，避免文字被截

# 4. 输出离线 HTML（文件名不变，覆盖）
fig2.write_html('trend.html', auto_open=True)
