import asyncio
import re
import time
import traceback
from pathlib import Path
from typing import List

import httpx
import jinja2
import orjson
from hoshino.typing import MessageSegment
from loguru import logger

from ..data_source import (config, number_url_homes, servers, set_damageColor,
                           set_shipparams, set_shipRecentparams,
                           set_shipSelectparams, set_upinfo_color,
                           set_winColor, template_path, tiers)
from ..utils import bytes2b64, match_keywords

from.publicAPI import get_ship_byName,get_AccountIdByName,check_yuyuko_cache
from collections import defaultdict, namedtuple
from datetime import datetime

from bs4 import BeautifulSoup

from ..html_render import html_to_pic, text_to_pic
from ..HttpClient_pool import client_default, client_yuyuko

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_path), enable_async=True
)
env.globals.update(set_damageColor=set_damageColor,set_winColor=set_winColor,set_upinfo_color=set_upinfo_color,time=time,int=int,abs=abs,enumerate=enumerate)


ShipSlectState = namedtuple("ShipSlectState", ['state','SlectIndex','SelectList'])
ShipSecletProcess = defaultdict(lambda: ShipSlectState(False, None, None))

async def get_ShipInfo(info,bot,ev):
    try:
        params = None
        if isinstance(info,List):
            for flag,i in enumerate(info):              #是否包含me或@，包含则调用平台接口
                if i == 'me':
                    params = {
                    "server": "QQ",
                    "accountId": int(ev['user_id']),
                    }
                    info.remove("me")
                match = re.search(r"CQ:at,qq=(\d+)",i)
                if match:
                    params = {
                    "server": "QQ",
                    "accountId": int(match.group(1)),
                    }
                    info[flag] = str(i).replace(f"[{match.group(0)}]",'')
                    if not info[flag]:
                        info.remove('')
                    break
            if not params and len(info) == 3:
                param_server,info = await match_keywords(info,servers)
                if param_server:
                    param_accountid = await get_AccountIdByName(param_server,str(info[0]))      #剩余列表第一个是否为游戏名
                    if isinstance(param_accountid,int):
                        info.remove(info[0])
                        params = {
                        "server": param_server,
                        "accountId": param_accountid,
                        }
                    else:
                        return f"{param_accountid}"
                else:
                    return '服务器参数似乎输错了呢'
            elif params and len(info) == 1:
                print(f"{params}")
            elif params:
                return '您似乎准备用查询自己的单船战绩，请检查参数中是否带有船名，以空格区分'
            else:
                return '您似乎准备用游戏昵称查询单船战绩，请检查参数中是否包含服务器、游戏昵称和船名，以空格区分'
            shipList = await get_ship_byName(str(info[0]))
            print(shipList)
            if shipList:
                if len(shipList) < 2:
                    params["shipId"] = shipList[0][0]
                else:
                    ShipSecletProcess[ev['user_id']] = ShipSlectState(
                        False, None, shipList
                    )
                    template = env.get_template("select-ship.html")
                    template_data = await set_shipSelectparams(shipList)
                    content = await template.render_async(template_data)
                    img = await html_to_pic(
                        content, wait=0, viewport={"width": 360, "height": 100}
                    )
                    await bot.send(ev,str(MessageSegment.image(bytes2b64(img))))
                    a = 0
                    while a < 40 and not ShipSecletProcess[ev['user_id']].state:
                        a += 1
                        await asyncio.sleep(0.5)
                    if ShipSecletProcess[ev['user_id']].state and ShipSecletProcess[ev['user_id']].SlectIndex <= len(shipList):
                        params["shipId"] = shipList[ShipSecletProcess[ev['user_id']].SlectIndex-1][0]
                        ShipSecletProcess[ev['user_id']] = ShipSlectState(False, None, None)
                    else:
                        ShipSecletProcess[ev['user_id']] = ShipSlectState(False, None, None)
                        return '已超时退出'
            else:
                return '找不到船，请确认船名是否正确，可以使用【wws 查船名】查询船只中英文'
        else:
            return '参数似乎出了问题呢'
        is_cache = await check_yuyuko_cache(params['server'],params['accountId'])
        if is_cache:
            logger.success('上报数据成功')
        else:
            logger.success('跳过上报数据，直接请求')
        url = 'https://api.wows.shinoaki.com/public/wows/account/ship/info'
        ranking = await get_MyShipRank_yuyuko(params)
        resp = await client_yuyuko.get(url, params=params, timeout=None)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['data']:
            if not result['data']['shipInfo']['battles'] and not result['data']['rankSolo']['battles']:
                return '查询不到战绩数据'
            template = env.get_template("wws-ship.html")
            template_data = await set_shipparams(result['data'])
            template_data['shipRank'] = ranking
            content = await template.render_async(template_data)
            return await html_to_pic(content, wait=0, viewport={"width": 800, "height": 100})
        elif result['code'] == 403:
            return f"{result['message']}\n请先绑定账号"
        elif result['code'] == 500:
            return f"{result['message']}\n这是服务器问题，请联系雨季麻麻"
        else:
            return f"{result['message']}"
    except Exception:
        logger.error(traceback.format_exc())
        ShipSecletProcess[ev['user_id']] = ShipSlectState(False, None, None)
        return    
    
    
async def get_MyShipRank_yuyuko(params):
    try:
        url = 'https://api.wows.shinoaki.com/upload/numbers/data/upload/user/ship/rank'
        resp = await client_yuyuko.get(url, params=params, timeout=None)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['data']:
            if result['data']['ranking']:
                return result['data']['ranking']
            elif not result['data']['ranking'] and not result['data']['serverId'] == 'cn':
                ranking = await get_MyShipRank_Numbers(result['data']['httpUrl'],result['data']['serverId']) 
                if ranking:
                    await post_MyShipRank_yuyuko(result['data']['accountId'],ranking,result['data']['serverId'],result['data']['shipId'])
                return ranking
            else:
                return None
        else:
            return None
    except Exception:
        logger.error(traceback.format_exc())
        return None
    
async def get_MyShipRank_Numbers(url,server):
    try:
        data = None
        resp = await client_default.get(url, timeout=10)
        if resp.content:
            result = orjson.loads(resp.content)
            page_url = str(result['url']).replace("\\","")
            nickname = str(result['nickname'])
            my_rank_url = f"{number_url_homes[server]}{page_url}"
            resp = await client_default.get(my_rank_url, timeout=10)
            soup = BeautifulSoup(resp.content, 'html.parser')
            data = soup.select_one(f'tr[data-nickname="{nickname}"]').select_one('td').string
        if data and data.isdigit():
            print(data)
            return data
        else:
            return None
    except Exception:
        logger.error(traceback.format_exc())
        return None    
    
async def post_MyShipRank_yuyuko(accountId,ranking,serverId,shipId):
    try:
        url = 'https://api.wows.shinoaki.com/upload/numbers/data/upload/user/ship/rank'
        post_data = {
            "accountId": int(accountId),
            "ranking": int(ranking),
            "serverId": serverId,
            "shipId":int(shipId)
        }
        resp = await client_yuyuko.post(url, json = post_data, timeout=None)
        result = orjson.loads(resp.content)
        return
    except Exception:
        logger.error(traceback.format_exc())
        return
    
async def get_ShipInfoRecent(info,bot,ev):
    try:
        params,day = None,0
        if datetime.now().hour < 7:
            day = 1
        if isinstance(info,List):
            for i in info:              #查找日期,没找到默认一天
                if str(i).isdigit():
                    if int(i) <= 30:
                        day = int(i)
                    else:
                        day = 30
                    info.remove(i)
            for flag,i in enumerate(info):              #是否包含me或@，包含则调用平台接口
                if i == 'me':
                    params = {
                    "server": "QQ",
                    "accountId": int(ev['user_id']),
                    "day": day
                    }
                    info.remove("me")
                match = re.search(r"CQ:at,qq=(\d+)",i)
                if match:
                    params = {
                    "server": "QQ",
                    "accountId": int(match.group(1)),
                    "day": day
                    }
                    info[flag] = str(i).replace(f"[{match.group(0)}]",'')
                    if not info[flag]:
                        info.remove('')
                    break
            if not params and len(info) == 3:
                param_server,info = await match_keywords(info,servers)
                if param_server:
                    param_accountid = await get_AccountIdByName(param_server,str(info[0]))      #剩余列表第一个是否为游戏名
                    if isinstance(param_accountid,int):
                        info.remove(info[0])
                        params = {
                        "server": param_server,
                        "accountId": param_accountid,
                        "day": day
                        }
                    else:
                        return f"{param_accountid}"
                else:
                    return '服务器参数似乎输错了呢'
            elif params and len(info) == 1:
                print(f"{params}")
            elif params:
                return '您似乎准备用查询自己的单船近期战绩，请检查参数中是否带有船名，以空格区分'
            else:
                return '您似乎准备用游戏昵称查询单船近期战绩，请检查参数中是否包含服务器、游戏昵称和船名，以空格区分'
            shipList = await get_ship_byName(str(info[0]))
            print(shipList)
            if shipList:
                if len(shipList) < 2:
                    params["shipId"] = shipList[0][0]
                else:
                    ShipSecletProcess[ev['user_id']] = ShipSlectState(
                        False, None, shipList
                    )
                    template = env.get_template("select-ship.html")
                    template_data = await set_shipSelectparams(shipList)
                    content = await template.render_async(template_data)
                    img = await html_to_pic(
                        content, wait=0, viewport={"width": 360, "height": 100}
                    )
                    await bot.send(ev,str(MessageSegment.image(bytes2b64(img))))
                    a = 0
                    while a < 40 and not ShipSecletProcess[ev['user_id']].state:
                        a += 1
                        await asyncio.sleep(0.5)
                    if ShipSecletProcess[ev['user_id']].state and ShipSecletProcess[ev['user_id']].SlectIndex <= len(shipList):
                        params["shipId"] = shipList[ShipSecletProcess[ev['user_id']].SlectIndex-1][0]
                        ShipSecletProcess[ev['user_id']] = ShipSlectState(False, None, None)
                    else:
                        ShipSecletProcess[ev['user_id']] = ShipSlectState(False, None, None)
                        return '已超时退出'
            else:
                return '找不到船，请确认船名是否正确，可以使用【wws 查船名】查询船只中英文'
        else:
            return '参数似乎出了问题呢'
        is_cache = await check_yuyuko_cache(params['server'],params['accountId'])
        if is_cache:
            logger.success('上报数据成功')
        else:
            logger.success('跳过上报数据，直接请求')
        url = 'https://api.wows.shinoaki.com/api/wows/recent/v2/recent/info/ship'
        resp = await client_yuyuko.get(url, params=params, timeout=None)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['data']:
            template = env.get_template("wws-ship-recent.html")
            template_data = await set_shipRecentparams(result['data'])
            content = await template.render_async(template_data)
            return await html_to_pic(content, wait=0, viewport={"width": 800, "height": 100})
        elif result['code'] == 403:
            return f"{result['message']}\n请先绑定账号"
        elif result['code'] == 500:
            return f"{result['message']}\n这是服务器问题，请联系雨季麻麻"
        else:
            return f"{result['message']}"
    except Exception:
        logger.error(traceback.format_exc())
        ShipSecletProcess[ev['user_id']] = ShipSlectState(False, None, None)
        return