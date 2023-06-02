import asyncio
import traceback
from pathlib import Path

import httpx
import jinja2
import orjson
from hoshino.typing import MessageSegment
from loguru import logger

from ..data_source import (config, number_url_homes, servers, set_shipparams,
                           set_ShipRank_Numbers, set_shipSelectparams,
                           template_path, tiers)
from ..utils import bytes2b64, match_keywords
from .wws_ship import ShipSecletProcess, ShipSlectState

from.publicAPI import get_ship_byName
from bs4 import BeautifulSoup

from ..html_render import html_to_pic, text_to_pic
from ..HttpClient_pool import client_default, client_yuyuko

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_path), enable_async=True
)

async def get_ShipRank(info,bot,ev):
    try:
        if len(info) == 2:
            param_server,info = await match_keywords(info,servers)
            if param_server:
                number_url = number_url_homes[param_server] + "/ship/"
            else:
                return '请检查服务器是否正确'
        else:
            return '参数似乎出了问题呢'
        shipList = await get_ship_byName(str(info[0]))
        print(shipList)
        if shipList:
            if len(shipList) < 2:
                select_shipId = shipList[0][0]
                shipInfo = {"shipNameCn": shipList[0][1], "tier": shipList[0][3]}
                number_url += f"{select_shipId},{shipList[0][2]}"
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
                    select_shipId = int(shipList[ShipSecletProcess[ev['user_id']].SlectIndex-1][0])
                    shipInfo = {
                        "shipNameCn": shipList[ShipSecletProcess[ev['user_id']].SlectIndex - 1][1],
                        "tier": shipList[ShipSecletProcess[ev['user_id']].SlectIndex - 1][3]
                    }
                    number_url += f"{select_shipId},{shipList[ShipSecletProcess[ev['user_id']].SlectIndex-1][2]}"
                    ShipSecletProcess[ev['user_id']] = ShipSlectState(False, None, None)
                    print(number_url)
                else:
                    ShipSecletProcess[ev['user_id']] = ShipSlectState(False, None, None)
                    return '已超时退出'
        else:
            return '找不到船，请确认船名是否正确，可以使用【wws 查船名】查询船只中英文'
        if not param_server == 'cn':
            content = await search_ShipRank_Yuyuko(select_shipId,param_server,shipInfo)
            if content:                                         #存在缓存，直接出图
                return await html_to_pic(content, wait=0, viewport={"width": 1300, "height": 100})
            else:                                               #无缓存，去Number爬
                content,numbers_data = await search_ShipRank_Numbers(number_url,param_server,select_shipId,shipInfo)
                if content:
                    await post_ShipRank(numbers_data)     #上报Yuyuko
                    return await html_to_pic(content, wait=0, viewport={"width": 1300, "height": 100})
                else:
                    return 'wuwuu好像出了点问题，可能是网络问题，过一会儿还是不行的话请联系麻麻~'   
        else:
            content = await search_cn_rank(select_shipId,param_server,1,shipInfo)
            if content:                                         
                return await html_to_pic(content, wait=0, viewport={"width": 1300, "height": 100})
            else:
                return 'wuwuu好像出了点问题，可能是网络问题，过一会儿还是不行的话请联系麻麻~' 
    except Exception:
        logger.error(traceback.format_exc())
        ShipSecletProcess[ev['user_id']] = ShipSlectState(False, None, None)
        return 'wuwuu好像出了点问题，过一会儿还是不行的话请联系麻麻~'    
   
async def search_ShipRank_Yuyuko(shipId,server,shipInfo):
    try:
        content = None                              #查询是否有缓存  
        url = 'https://api.wows.shinoaki.com/upload/numbers/data/v2/upload/ship/rank'
        params = {
            "server":server,
            "shipId":int(shipId)
        }
        resp = await client_yuyuko.get(url, params=params,timeout=None)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['data']:
            result_data = {"data": result["data"], "shipInfo": shipInfo}
            template = env.get_template("ship-rank.html")
            content = await template.render_async(result_data)
            return content
        else:
            return None
    except Exception:
        logger.error(traceback.format_exc())
        return None 
        
async def search_ShipRank_Numbers(url,server,shipId,shipInfo):
    try:
        content = None
        print(url)
        resp = await client_default.get(url, timeout=None)
        soup = BeautifulSoup(resp.content, 'html.parser')
        data = soup.select('tr[class="cells-middle"]')
        infoList = await set_ShipRank_Numbers(data,server,shipId)
        if infoList:
            result_data = {"data": infoList, "shipInfo": shipInfo}
            template = env.get_template("ship-rank.html")
            content = await template.render_async(result_data)
            return content,infoList
        else:
            return None,None
    except Exception:
        logger.error(traceback.format_exc())
        return None,None
            
async def post_ShipRank(data):
    try:
        url = 'https://api.wows.shinoaki.com/upload/numbers/data/v2/upload/ship/rank'
        resp = await client_yuyuko.post(url, json = data, timeout=None)
        result = orjson.loads(resp.content)
    except Exception:
        logger.error(traceback.format_exc())
                
        
async def search_cn_rank(shipId,server,page,shipInfo):
    try:
        content = None       #查询是否有缓存
        url = 'https://api.wows.shinoaki.com/wows/rank/ship/server'
        params = {
            "server":server,
            "shipId":int(shipId),
            "page":int(page)
        }
        logger.success(f"下面是本次请求的参数，如果遇到了问题，请将这部分连同报错日志一起发送给麻麻哦\n{url}\n{params}")
        resp = await client_yuyuko.get(url, params=params,timeout=None)
        result = orjson.loads(resp.content)
        if result['code'] == 200 and result['data']:
            template = env.get_template("ship-rank.html")
            result_data = {"data": result["data"], "shipInfo": shipInfo}
            content = await template.render_async(result_data)
            return content
        else:
            return None
    except Exception:
        logger.error(traceback.format_exc())
        return None 