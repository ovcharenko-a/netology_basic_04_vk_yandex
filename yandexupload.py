"""Модуль описывающий класс YaUploader"""
import aiohttp
import logging


class YaUploader:
    """
    Класс, реализующий загрузку файла на Яндекс диск.
    """
    HOST = "https://cloud-api.yandex.net/v1/disk/resources"
    HEADERS = {
        "Authorization": "OAuth ",
        "User-Agent": "netology-student",
        "Content - Type": "application/json",
    }
    RESULT_KEY = {
        200: "Успех",
        201: "Файл был загружен без ошибок.",
        202: "Accepted — файл принят сервером, но еще не был перенесен непосредственно в Яндекс.Диск.",
        412: "Precondition Failed — при дозагрузке файла был передан неверный диапазон в заголовке Content-Range.",
        413: "Payload Too Large — размер файла превышает 10 ГБ.",
        500: "Internal Server Error или 503 Service Unavailable — ошибка сервера, попробуйте повторить загрузку.",
        507: "Insufficient Storage — для загрузки файла не хватает места на Диске пользователя."
    }

    def __init__(self, token: str):
        """
        При создании класса будет открыта сессия aiohttp. Не забывать закрывать
        :param token: токен доступа к Яндекс-диску
        """
        self.token = token
        self.session = aiohttp.ClientSession()
        self.pathes = []
        self.HEADERS["Authorization"] += token

    async def get_status_from_url(self, _url):
        """
        Метод получения результата асинхронной загрузки на Яндекс.Диск
        :param _url: Ссылка проверки результат, возвращенная Яндекс Диском
        :return:
        """
        async with self.session.get(_url, headers=self.HEADERS) as resp:
            response = await resp.json()
            return response["status"]

    async def create_folder(self, path: str):
        """
        Метод, создающий произвольную папку со всеми родительскими папками. Кэширует результаты в рамках одной сессии
        :param path: Путь, который нужно создать на Яндекс Диске
        :return:
        """
        path = path.strip("/").split("/")
        if path in self.pathes:
            return
        temp_path = []
        for one_step in path:
            temp_path.append(one_step)
            if temp_path not in self.pathes:
                temp_folder = "/".join(temp_path)
                host_get = self.HOST
                params = {
                    "path": temp_folder
                }
                async with self.session.put(host_get, headers=self.HEADERS, params=params) as resp:
                    if resp.status in (409, 201):
                        self.pathes.append(temp_path.copy())
                        logging.info(f'Создана папка {temp_folder}')
                    elif resp.status == 409:
                        self.pathes.append(temp_path.copy())
                        logging.info(f'Найдена папка {temp_folder}')
                    else:
                        logging.info(f"ошибка создания папки {resp.status} - {self.RESULT_KEY.get(resp.status)}...")

    async def upload_from_url(self, input_file_url: str, remote_path: str = "", remote_file: str = ""):
        """
        Метод, вызывающий загрузку на ЯндексДиск удаленного ресурса по URL
        :param input_file_url: URL загружаемого файла
        :param remote_path: целевая папка на Яндекс. Диске
        :param remote_file: Имя итогового файла
        :return: Возвращает имя файла и URL, по которому можно узнать результат асинхронной загрузки
        """
        host_get = self.HOST + "/upload"
        params = {
            "url": input_file_url,
            "path": remote_path + remote_file,
        }
        if remote_path:
            await self.create_folder(remote_path)
        async with self.session.post(host_get, headers=self.HEADERS, params=params) as resp:
            if resp.status == 202:
                response = await resp.json()
                logging.info(f"URL {input_file_url} успешно поставлен на загрузку ({response['href']})")
                ret_res = response.get('href', None)
                return remote_file, ret_res
            else:
                logging.debug(resp.status)
                logging.info(f"URL {input_file_url} ОШИБКА:{await resp.json()}")
                return None, None
