from bokeh.plotting import figure, show

# https://docs.bokeh.org/en/latest/docs/gallery.html

def create_plot(*args):
    # create a new plot with a title and axis labels
    p = figure(title="Simple line example", x_axis_label="x", y_axis_label="y")

    # add a line renderer with legend and line thickness
    p.line(*args, legend_label="Temp.", line_width=2)

    # создаётся html файл

    # show the results html
    show(p)

if __name__ == '__main__':
    # prepare some data
    x = [1, 2, 3, 4, 5]
    y = [6, 7, 2, 4, 5]

    create_plot(x,y)