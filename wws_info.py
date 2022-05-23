from typing import List
import httpx
import traceback
import json
import jinja2
from pathlib import Path
from .data_source import servers,set_infoparams
from .utils import html_to_pic

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
        if isinstance (info,int):
            url = 'https://api.wows.linxun.link/api/wows/account/user/info'
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
            params_accountId,test_accountname = await get_AccountIdByName(param_server,str(info[0]))
            if params_accountId:
                url = 'https://api.wows.linxun.link/public/wows/account/user/info'
                params = {
                "server": param_server,
                "accountId": params_accountId
                }
            else:
                return '无法查询该游戏昵称Orz'
        else:
            return 'wuwuwu出了点问题，可能是参数不正确，请联系麻麻解决'
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
            return result['data']['accountId'],result['data']['userName']
        else:
            return 0,0
    except Exception:
        traceback.print_exc()
        return
    

