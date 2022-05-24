from sqlite3 import paramstyle
from typing import List
import httpx
import traceback
import json
import jinja2
import re
from pathlib import Path
from .data_source import servers,set_infoparams
from .utils import html_to_pic,match_keywords


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

async def get_AccountInfo(info):
    try:
        param_server = None
        if isinstance (info,int):
            url = 'https://api.wows.linxun.link/public/wows/account/platform/user/info'
            params = {
            "platformType": "QQ",
            "platformId": info
            }
        elif isinstance (info,List):
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
                url = 'https://api.wows.linxun.link/public/wows/account/user/info'
                params = {
                "server": param_server,
                "accountId": params_accountId
                }
            else:
                return '无法查询该游戏昵称Orz，请检查昵称是否存在'
        else:
            return 'wuwuwu出了点问题，可能是参数不正确，请检查后重新尝试'
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=10)
            result = resp.json()
        if result['data']:
            template = env.get_template("wws-info.html")
            template_data = await set_infoparams(result['data'])
            print('template_data',template_data)
            content = await template.render_async(template_data)
            return await html_to_pic(content, wait=0, viewport={"width": 920, "height": 1000})
        else:
            return '查询不到对应信息哦~可能是游戏昵称不正确或QQ未绑定'
    except Exception:
        traceback.print_exc()
        return 'wuwuwu出了点问题，请联系麻麻解决'
    
async def get_AccountIdByName(server:str,name:str):
    try:
        url = 'https://api.wows.linxun.link/public/wows/account/search/user'
        params = {
            "server": server,
            "userName": name
        }
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=10)
            result = resp.json()
        if result['data']:
            return result['data']['accountId']
        else:
            return None
    except Exception:
        traceback.print_exc()
        return None
    

async def new_get_AccountInfo(qqid,info):
    try:
        params = None
        if isinstance(info,List):
            for i in info:
                if i == 'me':
                    url = 'https://api.wows.linxun.link/public/wows/account/platform/user/info'
                    params = {
                    "platformType": "QQ",
                    "platformId": qqid
                    }
                    break
                match = re.search(r"CQ:at,qq=(\d+)",i)
                if match:
                    url = 'https://api.wows.linxun.link/public/wows/account/platform/user/info'
                    params = {
                    "platformType": "QQ",
                    "platformId": match.group(1)
                    }
                    break
            if not params and len(info) == 2:
                param_server,info = await match_keywords(info,servers)
                if param_server:
                    param_accountid = await get_AccountIdByName(param_server,str(info[0]))
                    if param_accountid:
                        url = 'https://api.wows.linxun.link/public/wows/account/user/info'
                        params = {
                        "server": param_server,
                        "accountId": param_accountid
                        }
                    else:
                        return '无法查询该游戏昵称Orz，请检查昵称是否存在'
                else:
                    return '服务器参数似乎输错了呢'
            elif params:
                print(params)
            else:
                return '您似乎准备用游戏昵称查询水表，请检查参数中时候包含服务器和游戏昵称，以空格区分'
        else:
            return '参数似乎出了问题呢'
        print(params)
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=10)
            result = resp.json()
        if result['data']:
            template = env.get_template("wws-info.html")
            template_data = await set_infoparams(result['data'])
            content = await template.render_async(template_data)
            return await html_to_pic(content, wait=0, viewport={"width": 920, "height": 1000})
        else:
            return '查询不到对应信息哦~可能是游戏昵称不正确或QQ未绑定'
    except Exception:
        traceback.print_exc()
        return 'wuwuwu出了点问题，请联系麻麻解决'