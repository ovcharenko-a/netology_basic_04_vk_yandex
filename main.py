import asyncio
import os
from fromvktoyadisk import from_vk_to_ya_disk

def main():
    """Пример применения программы для тестовго vk id"""
    loop = asyncio.get_event_loop()
    VK_TOKEN = os.environ['VK_TOKEN']
    YANDEX_TOKEN = os.environ['YANDEX_TOKEN']
    loop.run_until_complete(from_vk_to_ya_disk(552934290, "netology-async", VK_TOKEN, YANDEX_TOKEN))


if __name__ == '__main__':
    main()
