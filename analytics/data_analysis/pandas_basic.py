import pandas as pd


def load_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    return df

def preprocess_data(df: pd.DataFrame):
    # df['Name'] или df.Name вернёт все данные из колонки name в виде df.Series
    print(df.Name)
    print(df.columns)  # выведет названия столбцов
    print(df.shape)  # выведет количество строк и столбцов

    print(df.iloc[0:3])  # выведет первые три строки
    print(df.loc[df['Age'] > 25])  # выведет все строчки, в которых возраст > 25)

    print(df.dropna(inplace=True))  # Удаляем все пропущенные значения)
    print(df.sort_values(by='Age'))

def analyse_data(df: pd.DataFrame):
    print(df.describe())  # выведет статистические данные по числовым столбцам
    print(df.corr())  # выведет корреляционную матрицу

    print(df.groupby('Survived')['Age'].mean())  # выведет средний возраст пассажиров, которые погибли или выжили
    print(df.pivot_table(index='Pclass', columns='Survived', values='Age', aggfunc='mean'))  # выведет сводную таблицу средних возрастов пассажиров в зависимости от класса и статуса погибли/выжил

    print(df['Age'].value_counts())  # выведет распределение возрастов пассажиров
    print(df['Age'].hist())  # строит гистограмму распределения возрастов пассажиров






if __name__ == '__main__':

    data = '../example_data/titanic.csv'
    df = load_data(data)