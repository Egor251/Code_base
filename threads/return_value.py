import sys
from concurrent.futures import ThreadPoolExecutor

pool = ThreadPoolExecutor()

def f(n):

    return n


feature1 = pool.submit(f, 2023) # создаем поток для функции
feature2 = pool.submit(f, 2020)

result1 = feature1.result() # забираем результат вычисления
result2 = feature2.result()

result = result1 + result2
print(result)