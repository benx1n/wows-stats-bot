import time
import httpx
import traceback
import json
from base64 import b64encode
from loguru import logger
from pathlib import Path


dir_path = Path(__file__).parent
cfgpath = dir_path / 'config.json'
config = json.load(open(cfgpath, 'r', encoding='utf8'))
ocr_url = config['ocr_url']

async def pic2txt_byOCR(img_path):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(img_path)
            img_base64 = str(b64encode(resp.content),encoding='utf-8')
            start = time.time()
            params = {
                "image":img_base64
            }
            resp = await client.post(ocr_url, data=params, timeout=5,follow_redirects=True)
        end = time.time()
        logger.success(f"OCR结果：{resp.text},耗时{end-start:.4f}s\n图片url:{img_path}")
        return resp.text
    except:
        logger.error(traceback.format_exc())
        return ''