# plot_generator.py
import pandas as pd
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

from graph_draw_utils.constants import BASE_DIR, exclude_tags


# -------------------------------------------------
# 1. 折线图
# -------------------------------------------------
def _build_line(df, today, prev_df, delta):
    fig = go.Figure()
    for tag, g in df.groupby('tag'):
        g = g.sort_values('date')
        cur = df[df['date'] == today].set_index('tag').loc[tag, 'matched_count']
        d = delta[tag]
        sign = '+' if d > 0 else ('' if d == 0 else '-')
        color = 'red' if d > 0 else ('black' if d == 0 else 'green')
        legend = (f'{tag} (今日值 {cur} | 较昨日 '
                  f'<span style="color:{color};">{sign}{abs(d)}</span>)')
        fig.add_trace(go.Scatter(
            x=g['date'], y=g['matched_count'],
            mode='lines+markers', name=legend,
            hovertemplate='%{fullData.name}<br>%{y}<extra></extra>'
        ))
    return fig


# -------------------------------------------------
# 2. 饼图
# -------------------------------------------------
def _build_pie(df, today):
    return (
        df[df['date'] == today]
            .groupby('tag', as_index=False)['matched_count']
            .sum()
            .query("tag not in @exclude_tags")
    )


# -------------------------------------------------
# 3. 变更项表格
# -------------------------------------------------
def _build_table():
    filter_changes_path = BASE_DIR / 'result' / 'filter_changes.json'
    if filter_changes_path.exists():
        with open(filter_changes_path, 'r', encoding='utf-8') as f:
            changes_data = json.load(f)
    else:
        changes_data = []

    if changes_data:
        ch_df = pd.DataFrame(changes_data)
        table_header = ['行号', '检查项', '原始值', '修改后']
        table_cells = [
            ch_df['row'].astype(str).tolist(),
            ch_df['key'].tolist(),
            ch_df['from'].tolist(),
            ch_df['to'].tolist()
        ]
    else:
        table_header = ['行数', '检查项', '原始值', '修改后']
        table_cells = [['无数据'], ['无数据'], ['无数据'], ['无数据']]

    return table_header, table_cells


# -------------------------------------------------
# 4. 主函数：拼装所有子图
# -------------------------------------------------
def build_figure(df):
    today = pd.Timestamp('today').normalize()
    prev = df[df['date'] < today]['date'].max()
    prev_df = df[df['date'] == prev].set_index('tag')['matched_count']
    delta = {
        t: df[df['date'] == today].set_index('tag').loc[t, 'matched_count'] - prev_df.get(t, 0)
        for t in df[df['date'] == today]['tag']
    }

    # 1. 折线图
    line_fig = _build_line(df, today, prev_df, delta)

    # 2. 饼图数据
    pie_df = _build_pie(df, today)

    # 3. 合计信息
    today_count_df = df[df['date'] == today].groupby('tag', as_index=False)['matched_count'].sum()
    today_total = int(today_count_df['matched_count'].sum())
    update_time = datetime.now().replace(second=0, microsecond=0).strftime('%Y-%m-%d %H:%M')
    prev_total = int(prev_df.sum())
    total_delta = today_total - prev_total
    sign = '+' if total_delta > 0 else ('' if total_delta == 0 else '-')
    delta_color = 'red' if total_delta > 0 else ('black' if total_delta == 0 else 'green')
    delta_str = f'{sign}{abs(total_delta)}'

    # 4. 变更表
    table_header, table_cells = _build_table()

    # 5. 组合子图
    fig2 = make_subplots(
        rows=3, cols=1,
        specs=[[{"type": "scatter"}], [{"type": "table"}], [{"type": "pie"}]],
        subplot_titles=['匹配数量随日期变化', '今日变化', '今日各标签数量'],
        vertical_spacing=0.1,
        row_heights=[0.4, 0.2, 0.4]
    )

    # 折线图
    for trace in line_fig.data:
        fig2.add_trace(trace, row=1, col=1)

    # 表格
    fig2.add_trace(go.Table(
        header=dict(values=table_header, font=dict(size=12), align='center'),
        cells=dict(values=table_cells, font=dict(size=11), align='center'),
        columnwidth=[0.15, 0.3, 0.3, 0.3]
    ), row=2, col=1)

    # 饼图
    fig2.add_trace(go.Pie(
        labels=pie_df['tag'],
        values=pie_df['matched_count'],
        textinfo='label+percent',
        textposition='auto',
        insidetextorientation='horizontal',
        showlegend=False
    ), row=3, col=1)

    # 顶部注释
    fig2.add_annotation(
        text=f"于{update_time}更新，今日合计：<b>{today_total}</b> 条（较昨日 <span style='color:{delta_color};'>{delta_str}</span>）",
        x=0.5, y=1.08, xref="paper", yref="paper",
        showarrow=False, font=dict(size=16)
    )

    fig2.update_layout(height=1300)
    return fig2
