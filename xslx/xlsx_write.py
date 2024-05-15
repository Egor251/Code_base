import xlsxwriter

def make_xlsx(input_data, name="excel.xlsx"):

    workbook = xlsxwriter.Workbook(name)  # Создаем xlsx-файл

    head = ['Столбец 1', 'Столбец 2', 'Столбец 3']

    header = workbook.add_format({'bold': True, 'font_size': 11, 'border': True})  # Формат шрифта для шапки
    header.set_text_wrap()
    usual = workbook.add_format({'border': True})  # Формат шрифта для всех остальных записей
    usual.set_text_wrap()

    worksheet = workbook.add_worksheet('Лист1')  # Название листа
    worksheet.set_column('A:B', 15)  # Ширина столбцов
    worksheet.set_column('C:C', 30)
    worksheet.set_column('D:D', 10)
    worksheet.set_column('E:E', 30)
    worksheet.set_column('F:F', 15)

    row = 0  # Счётчик строк
    for i in range(len(head)):  # Записываем заголовок
        worksheet.write(row, i, head[i], header)
    row += 1

    for item in input_data:

        for count, value in enumerate(item):
            worksheet.write(row, count, value, usual)  # Основные записи

        row += 1
    workbook.close()  # Закрываем xlsx-файл. Важно не забыть!


if __name__ == "__main__":
    input_data = [[1, 2, 3], [4, 5, 6]]  # На вход принимается Список столбцов в списке строк
    make_xlsx(input_data, 'test.xlsx')
