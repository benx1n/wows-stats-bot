import time
import traceback
from base64 import b64decode, b64encode
from pathlib import Path

import httpx
import orjson
from hikari_core.config import hikari_config
from hikari_core.data_source import __version__
from hikari_core.HttpClient_Pool import get_client_yuyuko
from httpx import TimeoutException
from loguru import logger

from ..data_source import config

dir_path = Path(__file__).parent.parent
game_path = Path(__file__).parent
ocr_url = config['ocr_url']
ocr_data_path = game_path / 'ocr_data.json'
upload_url = 'https://v3-api.wows.shinoaki.com:8443/api/wows/cache/image/ocr'
download_url = 'https://v3-api.wows.shinoaki.com:8443/api/wows/cache/image/ocr'

headers = {
    'Authorization': config['token'],
    'accept': 'application/json',
    'Content-Type': 'application/json',
    'Yuyuko-Client-Type': f'{hikari_config.yuyuko_type};{__version__}',
}

try:
    with open(ocr_data_path, 'w', encoding='UTF-8') as f:
        resp = httpx.get(download_url, headers=headers)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['data']:
            f.write(orjson.dumps(result['data']).decode())
            # json.dump(result['data'], f)
    global ocr_filename_data
    with open(ocr_data_path, 'rb') as f:
        ocr_filename_data = orjson.loads(f.read())
    # ocr_filename_data = json.load(open(ocr_data_path, 'r', encoding='utf8'))

except Exception:
    logger.error(traceback.format_exc())


async def pic2txt_byOCR(img_path, filename):
    try:
        if filename in ocr_filename_data:
            logger.success(f'filename匹配，跳过OCR:{filename}')
            return b64decode(ocr_filename_data[filename]).decode('utf-8')
        if config['ocr_offline']:
            return ''
        logger.success(f'图片地址{img_path}')
        start = time.time()
        params = {'url': img_path}
        async with httpx.AsyncClient() as client:
            resp = await client.post(f'{ocr_url}/OCR/', data=params, timeout=5, follow_redirects=True)
            end = time.time()
            result = orjson.loads(resp.content)
            if result['code'] == 200:
                logger.success(f"OCR结果：{result['data']['msg']},耗时{end-start:.4f}s\n图片url:{img_path}")
                return result['data']['msg']
    except TimeoutException:
        logger.error('ocr超时，请确认OCR服务是否在线')
        return ''
    except Exception:
        logger.error(traceback.format_exc())
        return ''


async def upload_OcrResult(result_text, filename):
    try:
        params = {'md5': filename, 'text': b64encode(result_text.encode('utf-8')).decode('utf-8')}
        client = await get_client_yuyuko()
        resp = await client.post(upload_url, json=params)
        result = orjson.loads(resp.content)
        if result['code'] == 200:
            logger.info('OCR表情包上报成功')
            await downlod_OcrResult()
    except Exception:
        logger.error(traceback.format_exc())


async def downlod_OcrResult():
    try:
        client = await get_client_yuyuko()
        resp = await client.get(download_url)
        result = orjson.loads(resp.content)
        with open(ocr_data_path, 'w', encoding='UTF-8') as f:
            if result['code'] == 200 and result['data']:
                f.write(orjson.dumps(result['data']).decode())
                # json.dump(result['data'], f)
                global ocr_filename_data
                ocr_filename_data = result['data']
            else:
                logger.error(result)
                with open(ocr_data_path, 'rb') as f:  # noqa: PLW2901
                    ocr_filename_data = orjson.loads(f.read())
                # ocr_filename_data = json.load(open(ocr_data_path, 'r', encoding='utf8'))
            return
    except Exception:
        logger.error('请检查token是否配置正确，如无问题请尝试重启，可能是网络波动或服务器原因')
        with open(ocr_data_path, 'rb') as f:
            ocr_filename_data = orjson.loads(f.read())
        # ocr_filename_data = json.load(open(ocr_data_path, 'r', encoding='utf8'))
        logger.error(traceback.format_exc())


async def get_Random_Ocr_Pic():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(f'{ocr_url}/ImageRandom/')
            img = b64decode(resp.text)
            return img
    except Exception:
        logger.error(traceback.format_exc())
        return 'OCR服务器出了点问题，请稍后再试哦'
