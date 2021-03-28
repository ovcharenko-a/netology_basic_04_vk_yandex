"""Модуль описывающий класс YaUploader"""
import asyncio
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
        self.token = token
        self.session = aiohttp.ClientSession()
        self.pathes = []
        self.HEADERS["Authorization"] += token


    async def create_folder(self, path: str):
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
                        logging.info(f"ошибка {resp.status}" - self.RESULT_KEY.get(resp.status), "...")


    async def upload_from_url(self, input_file_url: str, remote_path: str="", remote_file: str="", overwrite: bool=True):
        """Метод загружает удалённый файл на яндекс диск"""
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
                logging.info(response)
                async with self.session.get(response['href'], headers=self.HEADERS) as resp_link:
                    logging.info(await resp_link.json())
            else:
                logging.info(resp.status)
                logging.info(await resp.json())
            return await resp.json()



