from typing import List
import httpx
import traceback
import json
import os
import gzip
import asyncio
from .data_source import nations,shiptypes,levels
from .utils import match_keywords,bytes2b64
from base64 import b64encode
from httpx import ConnectTimeout
from asyncio.exceptions import TimeoutError
from loguru import logger

cfgpath = os.path.join(os.path.dirname(__file__), 'config.json')
config = json.load(open(cfgpath, 'r', encoding='utf8'))

headers = {
    'Authorization': config['token']
}
if config['proxy']:
    proxy={
        'https://': config['proxy']
    }
else:
    proxy={
    }

async def get_nation_list():
    try:
        msg = ''
        url = 'https://api.wows.shinoaki.com/public/wows/encyclopedia/nation/list'
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, timeout=None)
            result = resp.json()
        for nation in result['data']:
            msg: str = msg + f"{nation['cn']}：{nation['nation']}\n"
        return msg
    except Exception:
        logger.error(traceback.format_exc())
        
async def get_ship_name(infolist:List,bot,ev):
    try:
        msg = ''
        param_nation,infolist = await match_keywords(infolist,nations)
        if not param_nation:
            return '请检查国家名是否正确'
        
        param_shiptype,infolist = await match_keywords(infolist,shiptypes)
        if not param_shiptype:
            return '请检查船只类别是否正确'
        
        param_level,infolist = await match_keywords(infolist,levels)
        if not param_level:
            return '请检查船只等级是否正确'
        params = {
            "county":param_nation,
            "level":param_level,
            "shipName":'',
            "shipType":param_shiptype
        }
        url = 'https://api.wows.shinoaki.com/public/wows/encyclopedia/ship/search'
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=None)
            result = resp.json()
        if result['data']:
            for ship in result['data']:
                msg += f"{ship['shipNameCn']}：{ship['shipNameNumbers']}\n"
        else:
            msg = '没有符合的船只'
        return msg
    except Exception:
        logger.error(traceback.format_exc())
        return msg
    
async def get_ship_byName(shipname:str):
    try:
        url = 'https://api.wows.shinoaki.com/public/wows/encyclopedia/ship/search'
        params = {
        "county":'',
        "level":'',
        "shipName":shipname,
        "shipType":''
    }
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=None)
            result = resp.json()
        List = []
        if result['code'] == 200 and result['data']:
            for each in result["data"]:
                List.append(
                    [
                        each["id"],
                        each["shipNameCn"],
                        each["shipNameNumbers"],
                        each["tier"],
                        each['shipType']
                    ]
                )
            return List
        else:
            return None
    except Exception:
        logger.error(traceback.format_exc())
        return None
    
async def get_AccountIdByName(server:str,name:str):
    try:
        url = 'https://api.wows.shinoaki.com/public/wows/account/search/user'
        params = {
            "server": server,
            "userName": name
        }
        print(f"下面是本次请求的参数，如果遇到了问题，请将这部分连同报错日志一起发送给麻麻哦\n{params}")
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=None)
            result = resp.json()
        if result['code'] == 200 and result['data']:
            return result['data']['accountId']
        else:
            return result['message']
    except (TimeoutError, ConnectTimeout):
        logger.error(traceback.format_exc())
        return '请求超时了，请过一会儿重试哦~'
    except Exception:
        logger.error(traceback.format_exc())
        return '好像出了点问题呢，可能是网络问题，如果重试几次还不行的话，请联系麻麻解决'
    
async def get_ClanIdByName(server:str,tag:str):
    try:
        url = 'https://api.wows.shinoaki.com/public/wows/clan/search'
        params = {
            "server": server,
            "tag": tag,
            "type": 1
        }
        print(f"下面是本次请求的参数，如果遇到了问题，请将这部分连同报错日志一起发送给麻麻哦\n{params}")
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=None)
            result = resp.json()
        List = []
        if result['code'] == 200 and result['data']:
            #for each in result['data']:
            #    List.append([each['clanId'],each['name'],each['serverName'],each['tag']])
            return result['data']
        else:
            return None
    except Exception:
        logger.error(traceback.format_exc())
        return None
    
async def check_yuyuko_cache(server,id):
    try:
        if config['check_cache']:
            yuyuko_cache_url = 'https://api.wows.shinoaki.com/api/wows/cache/check'
            params = {
                "accountId": id,
                "server": server
            }
            print(f"下面是本次请求的参数，如果遇到了问题，请将这部分连同报错日志一起发送给麻麻哦\n{params}")
            async with httpx.AsyncClient(headers=headers) as client:
                resp = await client.post(yuyuko_cache_url, json=params, timeout=5)
                result = resp.json()
            cache_data = {}
            if result['code'] == 201:
                if 'DEV' in result['data']:
                    await get_wg_info(cache_data,'DEV',result['data']['DEV'])
                elif 'pvp' in result['data']:
                    tasks = []
                    loop = asyncio.get_running_loop()
                    for key in result['data']:
                        tasks.append(asyncio.ensure_future(get_wg_info(cache_data,key, result['data'][key])))
                    await asyncio.gather(*tasks)
                if not cache_data:
                    return False
                print(type(gzip.compress(json.dumps(cache_data).encode('utf-8'))))
                data_base64 = b64encode(gzip.compress(json.dumps(cache_data).encode('utf-8'))).decode()
                params['data'] = data_base64
                async with httpx.AsyncClient(headers=headers) as client:
                    resp = await client.post(yuyuko_cache_url, json=params, timeout=5)
                    result = resp.json()
                    print(result)
                if result['code'] == 200:
                    return True
                else:
                    return False
            return False
        return False
    except Exception:
        logger.error(traceback.format_exc())
        return False
    
async def get_wg_info(params,key,url):
    try:
        async with httpx.AsyncClient(headers=headers,proxies=proxy) as client:
            resp = await client.get(url, timeout=5, follow_redirects = True)
            wg_result = resp.json()
        if resp.status_code == 200 and wg_result['status'] == 'ok':
            params[key] = resp.text
    except Exception:
        logger.error(traceback.format_exc())
        return
        