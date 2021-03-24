import asyncio
import logging
# from yandexupload import YaUploader
from vkdownload import VkDownload
import os


async def main():
    # logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)
    # Храните токены в переменных окружения
    VK_TOKEN = os.environ['VK_TOKEN']

    vk_data = VkDownload(1476954, VK_TOKEN)
    # vk_data = VkDownload(552934290, VK_TOKEN)
    if await vk_data.get_albums_list() or vk_data.albums_count == 0:
        await vk_data.session.close()
        logging.info("Продолжение невозможно")
        return
    await vk_data.parse_photo_from_albums()
    await vk_data.session.close()
    print(vk_data.albums_links)
    getted_urls = sum([len(one_album) for one_album in vk_data.albums_links.values()])
    print(getted_urls, vk_data.photos_sum)
    if not vk_data.photos_sum == getted_urls:
        logging.warning(f"ИЗ {vk_data.photos_sum} ПОЛУЧЕНО ТОЛЬКО {getted_urls} URL ДЛЯ СКАЧИВАНИЯ.")

    print("пока на этом всё")


if __name__ == '__main__':
    # main()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())