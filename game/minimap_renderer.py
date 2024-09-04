import asyncio
import base64
import hashlib
import os

import requests
from hoshino.typing import MessageSegment, NoticeSession
from requests.auth import HTTPBasicAuth
from concurrent.futures import ThreadPoolExecutor

from ..data_source import config

minimap_renderer_url = config['minimap_renderer_url']
minimap_renderer_user_name = config['minimap_renderer_user_name']
minimap_renderer_password = config['minimap_renderer_password']

minimap_renderer_temp = "minimap_renderer_temp"
executor = ThreadPoolExecutor()


async def get_rep(wows_rep_file_base64: str, session: NoticeSession):
    if wows_rep_file_base64.__contains__(".wowsreplay"):
        wowsrepla_file = wows_rep_file_base64
    else:
        file_hex = hashlib.sha256(wows_rep_file_base64.encode('utf-8')).hexdigest()
        file_bytes = base64.b64decode(wows_rep_file_base64)
        file_path_temp = os.getcwd() + os.sep + minimap_renderer_temp + os.sep + file_hex
        f_d = os.getcwd() + os.sep + minimap_renderer_temp
        if not os.path.exists(f_d):
            os.makedirs(f_d)
        wowsrepla_file = file_path_temp + ".wowsreplay"
        with open(wowsrepla_file, 'wb') as f:
            f.write(file_bytes)
            f.close()
    if not os.path.exists(wowsrepla_file):
        await session.send(MessageSegment.text("文件不存在，ll和nc 部署的请检查服务是否在一个服务器上，否则请开启base64功能"))
    else:
        await session.send(MessageSegment.text("正在处理replays文件.预计耗时1分钟"))
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(executor, lambda: upload_http(wowsrepla_file))
        if result is None:
            await session.send(MessageSegment.text("生成视频文件异常！请检查 minimap_renderer 是否要更新."))
        else:
            await send_video(session, result)


def upload_http(wowsrepla_file: str):
    upload_url = f'{minimap_renderer_url}/upload_replays_video_url'
    with open(wowsrepla_file, 'rb') as file:
        files = {'file': file}
        response = requests.post(upload_url, files=files, auth=HTTPBasicAuth(minimap_renderer_user_name, minimap_renderer_password), timeout=600)
        if response.status_code == 200:
            return response.text
    return None


async def send_video(session: NoticeSession, url: str):
    # 构造视频文件消息
    data = str(minimap_renderer_url + "/video_url?file_name=" + url.replace("\"", ""))
    await  session.send(MessageSegment.video(data))


def get_file(url: str):
    response = requests.get(url)
    # 确保请求成功
    if response.status_code == 200:
        # 获取文件内容
        file_content = response.content

        # 对文件内容进行 Base64 编码
        encoded_content = base64.b64encode(file_content)

        # 将编码后的内容转换为字符串
        return encoded_content.decode('utf-8')