import seaborn as sns
import matplotlib.pyplot as matplotlib
import pandas as pd

# https://seaborn.pydata.org/examples/index.html

def visualise(df: pd.DataFrame, main_data: str):
    # Визуализация с использованием seaborn
    sns_plot = sns.pairplot(df, hue=main_data)  # hue - столбец по которому строим данные. остальные столбцы будут осями координат

    #matplotlib.show()  # показать график
    return sns_plot  # возвращаем график для дальнейшего использования или сохранения


def save_plot(plot):
    # fig = plot.get_figure()  'PairGrid' object has no attribute 'get_figure'
    fig = plot.fig.get_figure()  # добавляем .fig. и всё работает
    # fig.savefig("out.png", format='png')
    # fig.savefig("out.svg", format='svg')
    # fig.savefig("out.pdf", format='pdf')
    fig.savefig("out.png")



if __name__ == '__main__':
    df = sns.load_dataset("penguins")  # pandas dataframe
    plot = visualise(df, 'species')
    save_plot(plot)
