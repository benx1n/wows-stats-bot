from typing import List
import httpx
import traceback
import json
import jinja2
import re
import asyncio
from pathlib import Path
from hoshino.typing import MessageSegment
from .data_source import servers,set_shipparams,set_shipRecentparams,tiers,number_url_homes
from .utils import match_keywords,bytes2b64
from.publicAPI import get_ship_byName,get_AccountIdByName
from collections import defaultdict, namedtuple
from .html_render import html_to_pic,text_to_pic
from bs4 import BeautifulSoup
from datetime import datetime

dir_path = Path(__file__).parent
template_path = dir_path / "template"
cfgpath = dir_path / 'config.json'
config = json.load(open(cfgpath, 'r', encoding='utf8'))
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_path), enable_async=True
)

headers = {
    'Authorization': config['token']
}

ShipSlectState = namedtuple("ShipSlectState", ['state','SlectIndex','SelectList'])
ShipSecletProcess = defaultdict(lambda: ShipSlectState(False, None, None))

async def get_ShipInfo(qqid,info,bot,ev):
    try:
        params = None
        if isinstance(info,List):
            for flag,i in enumerate(info):              #是否包含me或@，包含则调用平台接口
                if i == 'me':
                    url = 'https://api.wows.shinoaki.com/public/wows/account/v2/ship/info'
                    params = {
                    "server": "QQ",
                    "accountId": int(qqid),
                    }
                    info.remove("me")
                match = re.search(r"CQ:at,qq=(\d+)",i)
                if match:
                    url = 'https://api.wows.shinoaki.com/public/wows/account/v2/ship/info'
                    params = {
                    "server": "QQ",
                    "accountId": int(match.group(1)),
                    }
                    info[flag] = str(i).replace(f"[{match.group(0)}]",'')
                    print(f"info删除前{info}")
                    if not info[flag]:
                        info.remove('')
                        print(f"info删除后{info}")
                    break
            if not params and len(info) == 3:
                param_server,info = await match_keywords(info,servers)
                if param_server:
                    param_accountid = await get_AccountIdByName(param_server,str(info[0]))      #剩余列表第一个是否为游戏名
                    if isinstance(param_accountid,int):
                        info.remove(info[0])
                        url = 'https://api.wows.shinoaki.com/public/wows/account/v2/ship/info'
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
                    msg = f'存在多条名字相似的船\n请在20秒内选择对应的序号\n================\n'
                    flag = 0
                    for each in shipList:
                        flag += 1
                        msg += f"{flag}：{tiers[each[3]-1]} {each[1]}\n"
                    ShipSecletProcess[qqid] = ShipSlectState(False, None, shipList)
                    img = await text_to_pic(text=msg,css_path = template_path/"text-ship.css",width=250)
                    await bot.send(ev,str(MessageSegment.image(bytes2b64(img))))
                    a = 0
                    while a < 40 and not ShipSecletProcess[qqid].state:
                        a += 1
                        await asyncio.sleep(0.5)
                    if ShipSecletProcess[qqid].state and ShipSecletProcess[qqid].SlectIndex <= len(shipList):
                        params["shipId"] = shipList[ShipSecletProcess[qqid].SlectIndex-1][0]
                        ShipSecletProcess[qqid] = ShipSlectState(False, None, None)
                    else:
                        ShipSecletProcess[qqid] = ShipSlectState(False, None, None)
                        return '已超时退出'
            else:
                return '找不到船'
        else:
            return '参数似乎出了问题呢'
        print(f"下面是本次请求的参数，如果遇到了问题，请将这部分连同报错日志一起发送给麻麻哦\n{params}")
        ranking = await get_MyShipRank_yuyuko(params)
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=None)
            result = resp.json()
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
        traceback.print_exc()
        return    
    
    
async def get_MyShipRank_yuyuko(params):
    try:
        url = 'https://api.wows.shinoaki.com/upload/numbers/data/upload/user/ship/rank'
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=None)
            result = resp.json()
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
        traceback.print_exc()
        return None
    
async def get_MyShipRank_Numbers(url,server):
    try:
        data = None
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=None)
            if resp.content:
                result = resp.json()
                page_url = str(result['url']).replace("\\","")
                nickname = str(result['nickname'])
                my_rank_url = f"{number_url_homes[server]}{page_url}"
                async with httpx.AsyncClient() as client:
                    resp = await client.get(my_rank_url, timeout=None)
                    soup = BeautifulSoup(resp.content, 'html.parser')
                    data = soup.select_one(f'tr[data-nickname="{nickname}"]').select_one('td').string
        if data and data.isdigit():
            print(data)
            return data
        else:
            return None
    except Exception:
        traceback.print_exc()
        return None    
    
async def post_MyShipRank_yuyuko(accountId,ranking,serverId,shipId):
    try:
        async with httpx.AsyncClient(headers=headers) as client:
            url = 'https://api.wows.shinoaki.com/upload/numbers/data/upload/user/ship/rank'
            post_data = {
                "accountId": int(accountId),
                "ranking": int(ranking),
                "serverId": serverId,
                "shipId":int(shipId)
            }
            resp = await client.post(url, json = post_data, timeout=None)
            result = resp.json()
            return
    except Exception:
        traceback.print_exc()
        return
    
async def get_ShipInfoRecent(qqid,info,bot,ev):
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
                    url = 'https://api.wows.shinoaki.com/api/wows/recent/v2/recent/info/ship'
                    params = {
                    "server": "QQ",
                    "accountId": int(qqid),
                    "day": day
                    }
                    info.remove("me")
                match = re.search(r"CQ:at,qq=(\d+)",i)
                if match:
                    url = 'https://api.wows.shinoaki.com/api/wows/recent/v2/recent/info/ship'
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
                        url = 'https://api.wows.shinoaki.com/api/wows/recent/v2/recent/info/ship'
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
                    msg = f'存在多条名字相似的船\n请在20秒内选择对应的序号\n================\n'
                    flag = 0
                    for each in shipList:
                        flag += 1
                        msg += f"{flag}：{tiers[each[3]-1]} {each[1]}\n"
                    ShipSecletProcess[qqid] = ShipSlectState(False, None, shipList)
                    img = await text_to_pic(text=msg,css_path = template_path/"text-ship.css",width=250)
                    await bot.send(ev,str(MessageSegment.image(bytes2b64(img))))
                    a = 0
                    while a < 40 and not ShipSecletProcess[qqid].state:
                        a += 1
                        await asyncio.sleep(0.5)
                    if ShipSecletProcess[qqid].state and ShipSecletProcess[qqid].SlectIndex <= len(shipList):
                        params["shipId"] = shipList[ShipSecletProcess[qqid].SlectIndex-1][0]
                        ShipSecletProcess[qqid] = ShipSlectState(False, None, None)
                    else:
                        ShipSecletProcess[qqid] = ShipSlectState(False, None, None)
                        return '已超时退出'
            else:
                return '找不到船'
        else:
            return '参数似乎出了问题呢'
        print(f"下面是本次请求的参数，如果遇到了问题，请将这部分连同报错日志一起发送给麻麻哦\n{params}")
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=None)
            result = resp.json()
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
        traceback.print_exc()
        return