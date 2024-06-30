import asyncio

async def first_async_function():
    while True:
        # Simulate an asynchronous operation
        await asyncio.sleep(2)
        return 'First function finished'

async def second_async_function():
    while True:
        # Simulate an asynchronous operation
        await asyncio.sleep(10)
        return 'Second function finished'

async def third_function():
    while True:
        # Simulate an asynchronous operation
        await asyncio.sleep(1)

async def third_async_function():
    task1 = asyncio.create_task(first_async_function())
    task2 = asyncio.create_task(second_async_function())

    while True:
        # Wait for the first function to finish
        data1 = await asyncio.wait_for(task1, timeout=None)
        print(data1)

        # Start the third function while the second function is still running
        if data1 == 'First function finished':
            print('Third function started')
            task3 = asyncio.create_task(third_function())
            await asyncio.sleep(1)  # Simulating some work
            print('Third function finished')

        # Wait for the second function to finish
        data2 = await asyncio.wait_for(task2, timeout=None)
        print(data2)

async def main():
    while True:
        await third_async_function()

asyncio.run(main())