import aiogram
import re, sys, time, json
import asyncio
import string
import moodle5
import requests
import user_agent
import mediafire
import urllib3.util
import uploaderclass
import nanogram.bot
import functools
from functools import partial
from concurrent.futures import ThreadPoolExecutor

__version__ = '0.4'
bottoken = open("token", "r").read().strip("\r\n")
bot = nanogram.bot.Bot(bottoken, verifyToken=False)
#  pll = nanogram.api.PollingUpdater(bot)
#  pll.clearUpdates()
admins = [1800975390, 5258763564] 
cfgs = json.loads(open("config.json").read())
limit = cfgs["limit"]

# lm limite de descarga 
lm = 5000000

filters = []
actual = None
__bot__ = aiogram.Bot(bottoken)
dp = aiogram.Dispatcher(__bot__)
exc = ThreadPoolExecutor(max_workers=1)
cache: dict[int, int] = {1047046816: 5000}
executor = ThreadPoolExecutor(max_workers=2)


def _round(number: int):
    if number <= 0:
        return "Out of range"

    elif number <= 1024:
        return str(round(number, 2)) + " Mb"

    elif number >= 1024:
        return str(round(number / 1024, 2)) + " Gb"

    elif number >= 1024 * 1024:
        return str(round(number / 1024 / 1024, 2)) + " Tb"

    else:
        return str(round(number / 1024 / 1024 / 1024, 2)) + " Pb"


def parseurl(url):
    try:
        data = urllib3.util.parse_url(url)

    except Exception:
        return None
    out = ""

    if data[0] is None:
        out = "https://"
    else:
        out = data[0] + "://"

    if data[2] is None:
        return None
    else:
        out += data[2]

    if data[3]:
        out += ":" + str(data[3])

    if data[4]:
        out += data[4]

    if data[5]:
        out += "?" + data[5]

    return out


def parsename(url):
    name = url.rsplit('/', maxsplit=1)[1]
    o = ''

    if name.strip(" ") == "":
        return "noname"

    for i in name:
        if str(i.lower()) in string.ascii_lowercase + string.digits + ".":
            o += i
        else:
            o += '_'

    if len(o) >= 100:
        try:
            ext = o.rsplit('.', maxsplit=1)
            if len(ext) >= 2:
                if len(ext[len(ext)-1]) >= 10:
                    ext = 'temp'
                else:
                    ext = ext[len(ext)-1]
            else:
                ext = 'temp'

            o = o.rsplit('.', maxsplit=1)[0][0:20]+'.'+ext
        except Exception:
            o = o[0:20]+'.temp'

    return o


class CloseEx(Exception):
    pass


class Downloader:
    args = {
        "filters": [],
        "headers": {"User-Agent": user_agent.generate_user_agent()},
        "cookies": None,
        "data": None,
        "method": "GET",
        "chunk_size": 8024 * 1024,
        "filename": None
    }

    def __init__(self, chat_id, url, **kwargs):
        try:
            url = parseurl(url)
            if url is None:
                bot.sendMessage(text="Link invalido", chat_id=chat_id)
                raise CloseEx("")

            self.args = type(self).args.copy()
            for arg in [*self.args.keys()]:
                if arg in [*kwargs.keys()]:
                    self.args[arg] = kwargs[arg]

            print(self.args)
            if self.args["filters"] != []:
                if len(self.args["filters"]) == 0:
                    print("Fails")
                    pass

                else:
                    for f in self.args["filters"]:
                        print(f)
                        for fil in f[0]:
                            print(fil)
                            if re.search(fil, url):
                                self.i = f[1](chat_id, url, kwargs)
                                return

            self.url = url
            self.cht = chat_id

            if self.args["filename"] is None:
                self.args["filename"] = parsename(self.url)

            self.exc = ThreadPoolExecutor(max_workers=7)

        except CloseEx:
            raise CloseEx(str(CloseEx))

        except Exception as e:
            bot.sendMessage(**{"chat_id": self.cht, "text": f"Downloader ERR\r\n{str(type(e).__name__)} ~ {str(e)}\r\nLine: {sys.exc_info()[2].tb_lineno}"})
            raise CloseEx("")

    def do(self):
        if hasattr(self, "i"):
            self = self.i

        print(self.cht, self.args["filename"])
        bot.sendMessage(chat_id=self.cht, text=str(self.args["filename"]))
        try:
            print("starting")
            with requests.get(
                self.url,
                headers=self.args["headers"],
                cookies=self.args["cookies"],
                data=self.args["data"],
                stream=True
            ) as req:
                print("started")
                id = bot.sendMessage(
                    chat_id=self.cht,
                    text="Iniciando..."
                )["message_id"]
                downloaded = []
                data = b''
                content_length = None\
                    if "Content-Length" not in [*req.headers.keys()]\
                    else int(req.headers["Content-Length"])

                if content_length is not None:
                    if self.cht in cache:
                        if content_length >= cache[self.cht] * 1024 * 1024:
                            bot.sendMessage(
                                text=f"El archivo solicitado excede la cuota\r\nSu cuota actual es de: {round(cache[self.cht], 2)}.Mb",
                                chat_id=self.cht
                            )
                            return None

                    if content_length >= lm * 1024 * 1024:
                        bot.sendMessage(
                            text=f"El archivo no puede ser de mas de {lm}MB",
                            chat_id=self.cht
                        )
                        return None

                asize = 0  # The actual downloaded data size
                _time = time.time()
                file = open(self.args["filename"], "wb")

                for d in req.iter_content(chunk_size=self.args["chunk_size"]):
                    if asize is not None:
                        if self.cht in cache:
                            if asize >= cache[self.cht] * 1024 * 1024:
                                del(data, d)
                                bot.sendMessage(
                                    text=f"El archivo solicitado excede la cuota\r\nSu cuota actual es de: {round(cache[self.cht], 2)}.Mb",
                                    chat_id=self.cht
                                )
                                return None

                        if asize >= lm * 1024 * 1024:
                            del(data, d)
                            bot.sendMessage(
                                text=
                                f"El archivo no puede ser de mas de {lm}MB",
                                chat_id=self.cht
                            )
                            return None

                    asize += len(d)
                    data += d
                    _time_ = time.time()
                    vel = len(d) / 1024 / 1024 / ((_time_ - _time))
                    _time = _time_

                    if type(content_length) == int:
                        percent = round(asize, 2) * 100 / (content_length)
                    else:
                        percent = "Unknow"

                    self.exc.submit(
                        functools.partial(
                            edit_progress_message,
                            "Descargando",
                            vel,
                            percent,
                            round(asize, 2),
                            round(
                                content_length / 1024 / 1024,
                                2
                            ) if content_length is not None else "Unknow",
                            id,
                            self.cht
                        )
                    )

                    # Limit = int: (bytes len) and len(data) = int: (bytes len)
                    if len(data) >= limit * 1024 * 1024:
                        file.write(data)
                        downloaded.append(file.name)
                        file.close()
                        data = b""
                        file = open(
                            f'{self.args["filename"]}.{len(downloaded)}',
                            "wb"
                        )

                self.exc.shutdown(wait=True, cancel_futures=True)
                if self.cht in cache:
                    cache[self.cht] = cache[self.cht] - (asize / 1024 / 1024)
                bot.editMessageText(
                    message_id=id,
                    chat_id=self.cht,
                    text="Descargado..."
                )
                downloaded.append(file.name)
                file.write(data)
                file.close()

            self.args["filename"] = None
            return downloaded

        except Exception as e:
            bot.sendMessage(**{"chat_id": self.cht, "text": "Un error ocurrio en el descargador, mas informacion en instantes"})
            bot.sendMessage(**{"chat_id": self.cht, "text": f"Downloader ERR\r\n{str(type(e).__name__)} ~ {str(e)}\r\nLine: {sys.exc_info()[2].tb_lineno}"})
            raise CloseEx("")


class DownloaderMD(Downloader):
    def __init__(self, chat_id, url, *args, **kwargs):
        # super().__init__(*args, **kwargs)
        print(self)
        try:
            print("Callback")
            url = mediafire.get(url)
            self.url = url[0]
            self.args["cookies"] = url[1]
            self.args["headers"].update(url[2])
            self.cht = chat_id

            if self.args["filename"] is None:
                self.args["filename"] = parsename(self.url)

            self.exc = ThreadPoolExecutor(max_workers=7)

        except Exception as e:
            print(e)

    def do(self):
        return Downloader.do(self)


class Uploader:
    def __init__(self, downloaded_list, chat_id):
        self.downloaded_list = downloaded_list
        self.cht = chat_id
        self.time = time.time()

    def __callback__(self, b, monitor, msg_id, selfc, *args, **kwargs):
        time_ = time.time()
        vel = (b / 1024 / 1024) / (time_ - self.time)
        percent = b * 100 / kwargs["encoder"].len
        selfc.exc.submit(
            functools.partial(
                edit_progress_message,
                "Subiendo",
                vel,
                percent,
                b,
                round(
                    kwargs["encoder"].len / 1024 / 1024,
                    2
                ),
                message_id=msg_id,
                chat_id=self.cht,
                up=True
            )
        )
        selfc.time = time.time()

    def do(self):
        timing = time.time()
        try:
            for c in range(0, len(self.downloaded_list)):
                while True:
                    try:
                        t = time.time()
                        upldr = uploaderclass.Progress(chunk_size=8024 * 1024)
                        upldr.chunk_callback = self.__callback__
                        callback = upldr.callback

                        sess = moodle5.login()
                        msg = bot.sendMessage(
                            chat_id=self.cht,
                            text="Subida iniciada..."
                        )["message_id"]

                        self.exc = ThreadPoolExecutor(max_workers=7)
                        url = moodle5.upload(
                            session=sess,
                            file=self.downloaded_list[c],
                            percent_callback=partial(
                                callback,
                                selfc=self,
                                msg_id=msg
                            )
                        )

                        t2 = (time.time() - t) / 60 / 60
                        self.exc.shutdown(wait=True, cancel_futures=True)
                        bot.editMessageText(
                            chat_id=self.cht,
                            message_id=msg,
                            text=f'ℹ️ Parte {c + 1}\r\n🕑 {round(t2, 2)}m\r\n\r\n🔗 {url["url"]}'
                        )

                        break

                    except Exception as e:
                        try:
                            retry_c += 1
                        except Exception:
                            retry_c = 1

                        try:
                            url
                        except Exception:
                            url = None

                        if retry_c >= 5:
                            bot.sendMessage(
                                text=f"Subida cancelada (El bot excedio el numero maximo de intentos)\r\n\r\nInformacion acerca del error:\r\n{'No hay' if url == None else str(url)}",
                                chat_id=self.cht
                            )
                            break

                        bot.sendMessage(
                            text="Ocurrio un error, reintentando...",
                            chat_id=self.cht
                        )

        except Exception as e:
            bot.sendMessage(
                **{
                    "chat_id": self.cht,
                    "text": f"Downloader ERR\r\n{str(type(e).__name__)} ~ {str(e)}\r\nLine: {sys.exc_info()[2].tb_lineno}"
                }
            )

        timing = time.time() - timing
        bot.sendMessage(
            chat_id=self.cht,
            text=f"Tardo {round(timing / 60, 2)} minutos"
        )


@dp.message_handler(commands=["delete"])
async def delete(message):
    try:
        data = message.text.split(" ")
        if len(data) == 1:
            await message.answer(
                "Por favor mande el link que quiere eliminar!"
            )
            return

        url = data[1]
        if parseurl(url) is None:
            message.answer("URL Invalida")
            return

        if re.match(
            f"(http|https)://{moodle5.default_server['server']['url']}/draftfile\.php/[0-9]*/user/draft/[0-9]*/.*",
            url
        ) is None:
            message.answer("URL de moodle Invalida")
            return

        session = moodle5.login()
        data = moodle5.parse_uploaded_url(url)
        message.answer(
            str(
                moodle5.delete(
                    session=session,
                    item_id=data[1],
                    filename=data[2]
                )
            )
        )

    except Exception as e:
        await __bot__.send_message(
            text=f"Deletion ERR\r\n{str(type(e).__name__)} ~ {str(e)}\r\nLine: {sys.exc_info()[2].tb_lineno}",
            chat_id=message["from"].id
        )


def edit_progress_message(
        status,
        vel,
        percent,
        filestat,
        filesize,
        message_id,
        chat_id,
        up=False):

    try:
        bot.editMessageText(
            text=f"ℹ️ Info..  {status}\r\n" +
            f"⏩  Vel   {round(vel, 2)}/Mbps\r\n" +
            f"☑️ %       {int(percent) if type(percent) != str else percent}%\r\n" +
            ("⬆️ Sub." if up else "⬇️ Desc") +
            f"  {round(filestat/1024/1024, 2)} Mb\r\n" +
            f"#️⃣ Total   {filesize} Mb",
            message_id=message_id,
            chat_id=chat_id
        )

    except Exception:
        bot.editMessageText(
            text=f"ℹ️ {status}\r\n" +
            f"⏩Size   {filestat} Mb\r\n" +
            f"#️⃣ Total   {filesize} Mb\r\n",
            message_id=message_id,
            chat_id=chat_id
        )


@dp.message_handler(commands=["quota"])
async def quota(message):
    if message["from"]["id"] in cache:
        await message.answer(
            f"Cuota: {_round(cache[message['from']['id']])}"
        )

    else:
        await message.answer(
            "Usted es un usuario ilimitado!"
        )


async def runner(message):
    global action
    action = executor.submit(
        functools.partial(
            get,
            message
        )
    )


@dp.message_handler(commands=["add_to_quota"])
async def add_to_quota(message):
    if "-" in str(message["chat"].id):
        return

    if message["from"].id in admins:
        data = message.text.split(" ")
        if len(data) <= 2:
            await message.answer("Error")
            return

        if int(data[1]) not in cache:
            await message.answer("Tht user doesn't are in the quota cache")
            return

        try:
            int(data[2])

        except Exception:
            await message.answer("Invalid number")
            return

        cache[int(data[1])] = cache[int(data[1])] + int(data[2])
        await message.answer("Quota changed: " + _round(cache[int(data[1])]))


@dp.message_handler(commands=["del_from_quota"])
async def del_quota(message):
    if "-" in str(message["chat"].id):
        return

    if message["from"].id in admins:
        data = message.text.split(" ")
        if len(data) <= 2:
            await message.answer("Error")
            return

        if int(data[1]) not in cache:
            await message.answer("Tht user doesn't are in the quota cache")
            return

        try:
            int(data[2])

        except Exception:
            await message.answer("Invalid number")
            return

        cache[int(data[1])] = cache[int(data[1])] - int(data[2])
        await message.answer("Quota changed: " + _round(cache[int(data[1])]))


@dp.message_handler()
async def get(message):
    if "-" in str(message["chat"].id):
        return

    if message["from"].id in admins:
        try:
            url = message.text
            d = Downloader(
                message["chat"].id,
                url,
                filters=[
                    [
                        [
                            r"[w]*\.mediafire\.com",
                            r"download[0-9]*\.mediafire\.com"
                        ],
                        DownloaderMD
                    ]
                ]
            )
            downloaded = d.do()
            if downloaded == None:
                return

            u = Uploader(downloaded, message["chat"].id)
            u.do()

            del(d)
            del(u)

        except CloseEx:
            return

        except Exception as e:
            bot.sendMessage(
                text=f"{str(type(e).__name__)} ~ {str(e)}\r\nLine: {sys.exc_info()[2].tb_lineno}",
                chat_id=message["chat"]["id"]
            )

aiogram.executor.start_polling(dp)
