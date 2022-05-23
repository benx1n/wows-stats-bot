from typing import List
import httpx
import traceback
import json
import os
from .data_source import nations,shiptypes,levels

cfgpath = os.path.join(os.path.dirname(__file__), 'config.json')
config = json.load(open(cfgpath, 'r', encoding='utf8'))

headers = {
    'Authorization': config['token']
}

async def get_nation_list():
    try:
        msg = ''
        url = 'https://api.wows.linxun.link/public/wows/encyclopedia/nation/list'
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, timeout=10)
            result = resp.json()
        for nation in result['data']:
            msg: str = msg + f"{nation['cn']}：{nation['nation']}\n"
        return msg
    except Exception:
        traceback.print_exc()
        
async def get_ship_name(infolist:List):
    try:
        msg,param_nation,param_shiptype,param_level = '','','',''
        for nation in nations :
            for kw in nation.keywords:
                for match_kw in infolist:
                    if match_kw == kw or match_kw.upper() == kw.upper() or match_kw.lower() == kw.lower():
                        param_nation = nation.match_keywords
                        infolist.remove(match_kw)
        if not param_nation:
            return '请检查国家名是否正确'
        for shiptype in shiptypes :
            for kw in shiptype.keywords:
                for match_kw in infolist:
                    if match_kw == kw or match_kw.upper() == kw.upper() or match_kw.lower() == kw.lower():
                        param_shiptype = shiptype.match_keywords
                        infolist.remove(match_kw)
        if not param_shiptype:
            return '请检查船只类别是否正确'
        for level in levels :
            for kw in level.keywords:
                for match_kw in infolist:
                    if kw == match_kw:
                        param_level = level.match_keywords
        if not param_level:
            return '请检查船只等级是否正确'
        params = {
            "county":param_nation,
            "level":param_level,
            "shipName":'',
            "shipType":param_shiptype
        }
        url = 'https://api.wows.linxun.link/public/wows/encyclopedia/ship/search'
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=10)
            result = resp.json()
        if result['data']:
            for ship in result['data']:
                msg += f"{ship['shipNameCn']}：{ship['shipNameNumbers']}\n"
        else:
            msg = '没有符合的船只'
        return msg
    except Exception:
        traceback.print_exc()
        return msg