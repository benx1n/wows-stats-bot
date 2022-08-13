from typing import List
import httpx
import traceback
import json
import jinja2
import re
import time
import asyncio
import gzip
import io
from pathlib import Path
from hoshino import get_bot
import paho.mqtt.client as mqtt
from threading import Thread
from .data_source import servers,set_infoparams,set_damageColor,set_winColor,set_upinfo_color
from .publicAPI import get_AccountIdByName
from .utils import match_keywords
from .html_render import html_to_pic
from loguru import logger
from .mqtt import mqtt_run

dir_path = Path(__file__).parent
template_path = dir_path / "template"
cfgpath = dir_path / 'config.json'
config = json.load(open(cfgpath, 'r', encoding='utf8'))
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_path), enable_async=True
)
env.globals.update(set_damageColor=set_damageColor,set_winColor=set_winColor,set_upinfo_color=set_upinfo_color,time=time,int=int,abs=abs,enumerate=enumerate)

headers = {
    'Authorization': config['token']
}   
is_first_run = True
async def mqtt_test(info,bot,ev):
    try:
        global is_first_run
        if is_first_run:
            mqtt_run()
            is_first_run = False
        return '测试'
    except Exception:
        logger.error(traceback.format_exc())
        return 'wuwuwu出了点问题，请联系麻麻解决'