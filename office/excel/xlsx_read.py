import xlrd  # Обязательно версия 1.2.0

def read_xlsx(file_path, list_index):
    output_list = []  # Выходной список
    rb = xlrd.open_workbook(file_path)  # Читаем xlsx-файл
    sheet = rb.sheet_by_index(list_index)  # Указываем нужный лист 0, 1, 2 и т.д.
    for row_num in range(sheet.nrows):  # Считываем файл построчно
        output_list.append(sheet.row_values(row_num))  # Вносим в выходной список

    return output_list  # Возвращаем выходной список


if __name__ == "__main__":
    print(read_xlsx('test.xlsx', 0))
