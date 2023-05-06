#import asyncio
#import gzip
#import io
#import json
#import re
#import time
#import traceback
#from pathlib import Path
#from threading import Thread
#from typing import List
#
#import httpx
#import jinja2
#import paho.mqtt.client as mqtt
#from hoshino import get_bot
#from loguru import logger
#
#from .data_source import (servers, set_damageColor, set_infoparams,
#                          set_upinfo_color, set_winColor)
#from .html_render import html_to_pic
#from .mqtt import mqtt_run
#from .publicAPI import get_AccountIdByName
#from .utils import match_keywords
#
#dir_path = Path(__file__).parent
#template_path = dir_path / "template"
#cfgpath = dir_path / 'config.json'
#config = json.load(open(cfgpath, 'r', encoding='utf8'))
#env = jinja2.Environment(
#    loader=jinja2.FileSystemLoader(template_path), enable_async=True
#)
#env.globals.update(set_damageColor=set_damageColor,set_winColor=set_winColor,set_upinfo_color=set_upinfo_color,time=time,int=int,abs=abs,enumerate=enumerate)
#
#headers = {
#    'Authorization': config['token']
#}   
#is_first_run = True
#async def mqtt_test(info,bot,ev):
#    try:
#        global is_first_run
#        if is_first_run:
#            mqtt_run()
#            is_first_run = False
#        return '测试'
#    except Exception:
#        logger.error(traceback.format_exc())
#        return 'wuwuwu出了点问题，请联系麻麻解决'