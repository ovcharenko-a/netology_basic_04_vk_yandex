"""Модуль описывающий класс VKDownload"""
import asyncio
import aiohttp
import logging


class VkDownload:
    """
    Класс, для получения данных из ВК
    """

    URL_GET_ALBUMS = "photos.getAlbums"
    URL_GET_PHOTOS = "photos.get"
    VERSION_API = "5.130"
    URL_METHODS = "https://api.vk.com/method/"

    def __init__(self, id_owner: int, token: str):
        """
        При создании класса будет открыта сессия aiohttp. Не забывать закрывать
        :param token: токен доступа к Яндекс-диску
        """
        self.id_owner = id_owner
        self.token = token
        self.albums = {}
        self.albums_links = {}
        self.albums_count = 0
        self.photos_sum = 0
        self.session = aiohttp.ClientSession()

    async def http_post_to_json(self, url: str, method: str, params: dict):
        """
        Метод для получения результатов POST запроса к vk
        :param url: базовый url
        :param method: суффикс url конкретного метода
        :param params: параметры POST-запроса
        :return:
        """
        async with self.session.post(url + method, params=params) as resp:
            if resp.status == 200:
                response = await resp.json()
                logging.debug(response)
                if response.get('error', ""):
                    logging.info(
                        f"Ошибка api({method}) {response['error']['error_code']}: {response['error']['error_msg']}")
                    return int(response['error']['error_code'])
                else:
                    logging.info(f"Метод {method} - успех!")
                    return response
            else:
                logging.info(f"Ошибка http-запроса({method}) к vk.com, статус {resp.status}")
                return resp.status

    async def get_albums_list(self):
        """
        Метод получения и сохранения списка альбомов пользователя
        :return: словарь с описанием альбомов или 0 в случае ошибки
        """
        params = {
            "access_token": self.token,
            "v": self.VERSION_API,
            "owner_id": self.id_owner,
            "need_system": 1
        }
        logging.info("Получение списков альбомов")
        self.albums = await self.http_post_to_json(self.URL_METHODS, self.URL_GET_ALBUMS, params=params)
        if type(self.albums) == dict:
            self.albums_count = self.albums['response']['count']
            self.photos_sum = sum([int(item['size']) for item in self.albums['response']['items']])
            logging.info(f"Найдено {self.photos_sum} фото в {self.albums_count} альбомах")
            logging.debug(self.albums)
            return 0
        else:
            logging.debug(self.albums)
            return self.albums

    async def add_urls_from_album(self, id_album):
        """
        Метод получения и сохранения url'ов, относящихся к заданному альбому
        :param id_album: идентификатор альбома
        :return:
        """
        params = {
            "access_token": self.token,
            "v": self.VERSION_API,
            "owner_id": self.id_owner,
            "need_system": 1,
            "extended": 1,
            "album_id": id_album,
            "count": 1000
        }
        # TODO - а ведь может быть больше 1000?
        logging.info(f"Запрос к альбому {id_album}")
        source_json = await self.http_post_to_json(self.URL_METHODS, self.URL_GET_PHOTOS, params=params)
        if type(source_json) == dict:
            logging.info(f"Разбор альбома {id_album}")
            # TODO - но вообще имя файла - это количество лайков
            one_album = {f"{one_img['id']}-{one_img['likes']['count']}": one_img['sizes'][-1]
                         for one_img in source_json['response']['items']}
            self.albums_links[id_album] = one_album
            logging.info(f"Альбом {id_album} разобран на url'ы изображений")
        logging.debug(source_json)
        return source_json

    async def parse_photo_from_albums(self):
        """
        Метод получения и сохранения полного перечня URLов фотографий по всем полученым альбомам.
        :return:
        """
        if self.albums_count == 0:
            logging.info("альбомов нет")
            return
        logging.info(f"Начало обработки альбомов ({self.albums_count})")
        tasks_pool = [asyncio.create_task(self.add_urls_from_album(album['id']))
                      for album in self.albums['response']['items']]

        for one_task in tasks_pool:
            await one_task

        logging.info(f"Конец обработки альбомов ")
