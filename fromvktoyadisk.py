import asyncio
import logging
from yandexupload import YaUploader
from vkdownload import VkDownload
import json


async def get_status_upload(ya_uploader: YaUploader, collector: dict, key: str):
    """
    Функция получения статуса асинхронной загрузки по возвращенной яндексом ссылке
    :param ya_uploader: объект uploader'а, содержащий открытую сессию
    :param collector: словарь, содержащий ссылки, и куда сохранить результат
    :param key: ключ конкретной загрузки
    :return:
    """
    collector[key]['status'] = await ya_uploader.get_status_from_url(collector[key]['status'])
    logging.info(f"Для {key} результат загрузки - {collector[key]['status']}")


async def from_vk_to_ya_disk(vk_id: int, root_path="", vk_token="", yandex_token=""):
    """
    Асинхронная функция, собирающая ссылки из альбомов заданного пользователя, и осуществляющая их загруку в Я.Диск
    :param vk_id: id пользователя
    :param root_path: папка на Я.Диске, в которой будет создана папка с фотографиями пользователя поальбомно
    :param vk_token: токен vk
    :param yandex_token: токен yandex
    :return:
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
    logging.info("Начало выполнения программы")

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
    # Собрать результаты загрузки
    for task_ in taskes:
        _jpg, _url = await task_
        logging.info(f"Для изображения {_jpg} получен {_url}")
        upload_status[_jpg]["status"] = _url

    logging.info('Техническая пауза в пять секунд, подождать, как там загрузка')
    await asyncio.sleep(5)
    logging.info('Спасибо за ожидание. Проверим загрузку')
    taskes_2 = [asyncio.create_task(get_status_upload(ya_uploader, upload_status, key)) for key in upload_status]
    for task_ in taskes_2:
        await task_
    await ya_uploader.session.close()
    logging.info('Сохранение отчёта')

    with open("result.json", "w", encoding="UTF-8") as f:
        json.dump(upload_status, f, indent=4)
    logging.info("Конец выполнения программы")
