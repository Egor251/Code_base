import multiprocessing
import os

# https://habr.com/ru/articles/789904/


def info(title):
    print(title)
    print('module name:', __name__)
    print('parent process:', os.getppid())
    print('process id:', os.getpid())

def hello(name):
    info('function f')
    print('hello', name)

def pool_use():
    with multiprocessing.Pool(5) as p:
        print(p.map(hello, [1, 2, 3]))

def basic_use():
    info('main line')
    p = multiprocessing.Process(target=hello, args=('bob',))
    p.start()
    p.join()

if __name__ == '__main__':
    basic_use()
    pool_use()