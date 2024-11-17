"""
Пример вставляемых данных через шаблон.
Переменная, немаркированный список, таблица, картинка
"""
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt

counts = {'variable': 'Пример переменной'}

"""
Для вставки списка вносим подобный код в шаблон

{% for item in bullet_list %}
- {{ item.item }}
    {% if item.sub_items %}
    {% for sub_item in item.sub_items %}
    - {{ sub_item }}
    {% endfor %}
    {% endif %}
{% endfor %}
"""

bullet_list = [{'item': 'Основной пункт',
                'sub_items': ['Подпункт 1',
                              'Подпункт 2']},
               {'item': 'Второй пункт',
                'sub_items': ['Подпункт 1',
                              'Подпункт 2']}]

lists = {'list_example': bullet_list}

"""
Для вставки таблицы вносим подобный код в шаблон

каждая команда в отдельной ячейке таблицы, т.е.

3 ячейки Заголовка
1 ячейка (объединённая)
3 ячейки
1 ячейка (объединённая)


{%tc for head in table%} | {{head}} | {%tc endfor%}

{%tr for row in table.itertuples()%}

{%tc for col in row[1:]%} | {{col}} | {%tc endfor%}

{%tr endfor%}




"""

table_example = pd.DataFrame([1, 2, 3], [4, 5, 6])
table_example.rename(columns={1: 'Столбец 1',
                              2: 'Столбец 2',
                              3: 'Столбец 3'
                              })

tables = {'table': table_example}


def make_image():
    # Create a new figure and axis
    fig, ax = plt.subplots()

    # Set the size of the circle
    radius = 0.5

    # Create the circle
    circle = plt.Circle((0, 0), radius, color='black')

    # Add the circle to the axis
    ax.add_artist(circle)

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()  # Закрыть фигуру для освобождения памяти
    return buffer  # Возвращаем байтовый объект для загрузки в веб-приложение


images = {'image': make_image()}
