import threading
import time


def greet(sec):
    time.sleep(sec)
    print('sleep: ', sec)


if __name__ == '__main__':
    t1 = threading.Thread(target=greet, args=(5,), daemon=True)
    t2 = threading.Thread(target=greet, args=(3,), daemon=True)
    start_time = time.time()
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    end_time = time.time() - start_time
    print(end_time)