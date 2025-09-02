from graph_draw_utils.data_loader import load_data
from graph_draw_utils.html_writer import write_html
from graph_draw_utils.plot_generator import build_figure

if __name__ == "__main__":
    df = load_data()
    fig = build_figure(df)
    write_html(fig)
