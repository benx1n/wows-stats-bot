from typing import List
import httpx
import traceback
import json
import jinja2
import time
from pathlib import Path

from requests import head

from .data_source import servers
from .wws_info import get_AccountIdByName
dir_path = Path(__file__).parent
cfgpath = dir_path / 'config.json'
config = json.load(open(cfgpath, 'r', encoding='utf8'))
headers = {
    'Authorization': config['token']
}

async def set_BindInfo(user,info):
    try:
        param_server = None
        if isinstance (info,List):
            for server in servers :
                for kw in server.keywords:
                    for match_kw in info:
                        if match_kw == kw or match_kw.upper() == kw.upper() or match_kw.lower() == kw.lower():
                            param_server = server.match_keywords
                            info.remove(match_kw)
            if not param_server:
                return '请检查服务器名是否正确'
            params_accountId = await get_AccountIdByName(param_server,str(info[0]))
            if params_accountId:
                url = 'https://api.wows.linxun.link/api/wows/bind/account/platform/bind/put'
                params = {
                "platformType": "QQ",
                "platformId": str(user),
                "accountId": params_accountId
                }
            else:
                return '无法查询该游戏昵称Orz，请检查昵称是否存在'
        else:
            return 'wuwuwu出了点问题，可能是参数不正确，请检查后重新尝试'
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=10)
            result = resp.json()
        if result['code'] == 200 and result['message'] == "success":
            return '绑定成功'
        elif result['code'] == 500:
            return result['message']
        else:
            return 'wuwuwu出了点问题，请联系麻麻解决'
    except Exception:
        traceback.print_exc()
        return 'wuwuwu出了点问题，请联系麻麻解决'
    
async def get_BindInfo(user):
    try:
        url = 'https://api.wows.linxun.link/api/wows/bind/account/platform/bind/list'
        params = {
        "platformType": "QQ",
        "platformId": str(user)
        }
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=10)
            result = resp.json()
        if result['code'] == 200 and result['message'] == "success":
            if result['data']:
                msg1 = f'当前绑定账号\n'
                msg2 = f'绑定账号列表\n'
                for bindinfo in result['data']:
                    msg2 += f"{bindinfo['serverType']} {bindinfo['userName']}\n"
                    if bindinfo['defaultId']:
                        msg1 += f"{bindinfo['serverType']} {bindinfo['userName']}\n"
                msg = msg1+msg2
                return msg
            else:
                return '该用户似乎还没绑定窝窝屎账号'
    except Exception:
        traceback.print_exc()
        return 'wuwuwu出了点问题，请联系麻麻解决'