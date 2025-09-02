from plotly.graph_objects import Figure


def write_html(fig: Figure, filename='index.html', auto_open=True):
    fig.write_html(filename, auto_open=auto_open)
