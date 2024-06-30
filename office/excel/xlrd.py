from pyxlsb import open_workbook


def read_excel(path, table_name):
    output_list = []
    with open_workbook(path) as wb:
        with wb.get_sheet(table_name) as sheet:
            for row in sheet.rows():
                tmp_list = []
                for item in row:
                    tmp_list.append(item.v)
                output_list.append(tmp_list)
    return output_list


if __name__ == '__main__':
   pass