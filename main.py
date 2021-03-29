import asyncio
import logging
from yandexupload import YaUploader
from vkdownload import VkDownload
import os


async def from_vk_to_ya_disk(vk_id, root_path="", vk_token="", yandex_token=""):
    # logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)
    # Набрать ссылки
    vk_data = VkDownload(vk_id, vk_token)
    if await vk_data.get_albums_list() or vk_data.albums_count == 0:
        await vk_data.session.close()
        logging.info("Продолжение невозможно, ошибка получения информации об альбомах")
        return
    await vk_data.parse_photo_from_albums()
    await vk_data.session.close()
    logging.debug(vk_data.albums_links)
    getted_urls = sum([len(one_album) for one_album in vk_data.albums_links.values()])
    logging.debug(getted_urls, vk_data.photos_sum)
    if not vk_data.photos_sum == getted_urls:
        logging.warning(f"ИЗ {vk_data.photos_sum} ПОЛУЧЕНО ТОЛЬКО {getted_urls} URL ДЛЯ СКАЧИВАНИЯ.")
    # Закачать
    pre_path = ""
    if root_path:
        pre_path = root_path.strip("/") + "/"
    ya_uploader = YaUploader(yandex_token)
    upload_status = {}
    taskes = []
    # Перебрали и отправили грузиться. Заодно подготовм отчёт
    for album_id, album in vk_data.albums_links.items():
        for name_jpg, prop_jpg in album.items():
            path_url = pre_path + str(vk_id) + "/" + str(album_id) + "/"
            name_url_jpg = name_jpg + ".jpg"
            upload_status[name_url_jpg] = {"file_name": name_url_jpg,
                                           "size": prop_jpg['type'],
                                           "status": 0,
                                           }
            taskes.append(asyncio.create_task(
                ya_uploader.upload_from_url(prop_jpg['url'], remote_path=path_url, remote_file=name_jpg + ".jpg")))
    logging.info("Собираем результаты загрузки")
    # json_list = []
    for task_ in taskes:
        _jpg, _url = await task_
        logging.info(_jpg, await ya_uploader.get_status_from_url(_url))
    await ya_uploader.session.close()


async def main():
    VK_TOKEN = os.environ['VK_TOKEN']
    YANDEX_TOKEN = os.environ['YANDEX_TOKEN']
    await from_vk_to_ya_disk(552934290, "netology-async", VK_TOKEN, YANDEX_TOKEN)


async def main_vk():
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


async def main_ya():
    # logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)
    # Храните токены в переменных окружения
    YANDEX_TOKEN = os.environ['YANDEX_TOKEN']
    ya_uploader = YaUploader(YANDEX_TOKEN)
    url_ = "https://sun9-24.userapi.com/c9275/u1476954/-6/w_9cce7ccb.jpg"
    await ya_uploader.upload_from_url(url_, remote_path="zh/op/ka/", remote_file="go.jpg")
    # await ya_uploader.create_folder("go/vna/po/el")
    # print(q)
    await ya_uploader.session.close()


if __name__ == '__main__':
    # main()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
