from graph_draw_utils.data_loader import load_data
from graph_draw_utils.html_writer import write_html
from graph_draw_utils.plot_generator import build_figure

if __name__ == "__main__":
    data_frame = load_data()
    fig = build_figure(data_frame)
    write_html(fig)
