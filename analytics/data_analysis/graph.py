import networkx as nx
import matplotlib.pyplot as plt


class GraphTools:

    # Формирует итоговый граф
    @staticmethod
    def get_graph(data_list: list, node_attrs: dict) -> nx.classes.graph.Graph:
        # data_list: [[node1, node2, weight], [node2, node3, weight], ... ]
        # node_attrs: {node1: {'name': 'John', 'sex': 1}, node2: {...},... }


        G = nx.Graph()  # экземпляр класса Graph
        G.add_weighted_edges_from(data_list)
        #print(f'Всего узлов графа: {len(node_attrs)}')

        nx.set_node_attributes(G, node_attrs)  # Присваиваем нодам дополнительные параметры для будущей аналитики

        color_map = []
        labels = {}
        for node in G:  # формируем карту цветов из атрибутов нод
            labels[node] = G.nodes[node]['name']
            try:
                if G.nodes[node]['sex'] == 1:
                    color_map.append('red')
                elif G.nodes[node]['sex'] == 2:
                    color_map.append('blue')
                else:
                    color_map.append('blue')
            except Exception:
                color_map.append('gold')

        options = {  # Параметры для визуализации графа.
            'node_color': color_map,
            'node_size': 15,
            'width': 0.1,
            'labels': labels
        }
        try:  # Вообще хз, но только так работает!
            nx.draw(G, **options)
        except Exception:
            pass
        plt.show()  # вывод изображения через matplotlib. не обязателен
        return G  # Возвращает граф с которым дальше может работать networkx

# добавляет длину ребра (1) к парам ID для передачи в get_graph
    @staticmethod
    def graph_data_preparation(a):
        c = []
        for b in a:
            c.append([b[0], b[1], 1])

        return c  # возвращаем массив типа [[baseid, friendid, 1],...] и массив с перечнем всех уникальных юзеров

# Функция сохранения базы в gexf файле
    @staticmethod
    def save_data(G, filename="graph.gexf"):
        nx.write_gexf(G, filename, encoding='utf-8', prettyprint=True, version='1.2draft')