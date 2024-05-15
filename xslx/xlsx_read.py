import xlrd

def read_xlsx(file_path):
    output_list = []  # Выходной список
    rb = xlrd.open_workbook(file_path)  # Читаем xlsx-файл
    sheet = rb.sheet_by_index(0)  # Указываем нужный лист
    for rownum in range(sheet.nrows):  # Считываем файл построчно
        output_list.append(sheet.row_values(rownum))  # Вносим в выходной список

    return output_list  # Возвращаем выходной список


if __name__ == "__main__":
    print(read_xlsx('test.xlsx'))
