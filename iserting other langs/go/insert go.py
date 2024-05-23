import ctypes

# Обязательно в импорт добавить "C"

# перед импортируемой функцией в go обязательно добавить комментарий
# //export hello_go

# go build -o this_is_go.so -buildmode=c-shared this_is_go.go

lib = ctypes.cdll.LoadLibrary("./this_is_go.so")
#lib.hello_go.argtypes = [ctypes.c_longlong, ctypes.c_longlong]  # Если функция принимает аргументы, то указываем их типы
print(lib.hello_go())