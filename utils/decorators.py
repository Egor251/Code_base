import time
import functools
def benchmark(func):  # Декоратор для вычисления времени работы функции. полезен при оптимизации
    # Вызывать @benchmark
    @functools.wraps(func)  # Сохраняем дескрипторы и атрибуты функции, чтобы они сохранились в выходной функции calc_time. Сильно упрощает отладку
    def calc_time(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        full_time = time.time() - start_time
        print(f'Function {func.__name__}() finished in {full_time} sec')
        return result
    return calc_time


def retry(num_retries, exception_to_check, sleep_time=0):
    """
    Decorator that retries the execution of a function if it raises a specific exception.
    """
    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(1, num_retries+1):
                try:
                    return func(*args, **kwargs)
                except exception_to_check as e:
                    print(f"{func.__name__} raised {e.__class__.__name__}. Retrying...")
                    if i < num_retries:
                        time.sleep(sleep_time)
            # Raise the exception if the function was not successful after the specified number of retries
            raise e
        return wrapper
    return decorate

