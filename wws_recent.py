from typing import List
import httpx
import traceback
import json
import jinja2
import time
from pathlib import Path
from .data_source import servers,set_recentparams
from .utils import html_to_pic
from .wws_info import get_AccountIdByName

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

async def get_RecentInfo(day,info):
    try:
        param_server = ''
        print(day,info)
        if isinstance (info,int):
            print(1)
            url = 'https://api.wows.linxun.link/api/wows/recent/recent/info/platform'
            params = {
            "platformType": "QQ",
            "platformId": info,
            "seconds": int(time.time())-86400*int(day)
            }
            print(params)
        elif isinstance (info,List):
            for server in servers :
                for kw in server.keywords:
                    for match_kw in info:
                        if match_kw == kw or match_kw.upper() == kw.upper() or match_kw.lower() == kw.lower():
                            param_server = server.match_keywords
                            info.remove(match_kw)
            if not param_server:
                return '参数格式不正确，请确保后面按顺序跟随日期、服务器和游戏昵称（或艾特QQ），以空格分隔，日期留空则默认为一天'
            params_accountId,test_accountname = await get_AccountIdByName(param_server,str(info[0]))
            if params_accountId:
                url = 'https://api.wows.linxun.link/api/wows/recent/recent/info'
                params = {
                "server": param_server,
                "accountId": params_accountId,
                "seconds": int(time.time())-86400*int(day)
                }
                print(params)
            else:
                return '无法查询该游戏昵称Orz，可能是网络问题，请稍后再试'
        else:
            return 'wuwuwu出了点问题，可能是参数不正确，请联系麻麻解决'  
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=10)
            result = resp.json()
        if result['code'] == 200 and result['data']:
            template = env.get_template("wws-info-recent.html")
            template_data = await set_recentparams(result['data'])
            content = await template.render_async(template_data)
            return await html_to_pic(content, wait=0, viewport={"width": 900, "height": 1500})
        elif result['code'] == 404:
            return '该日期数据记录不存在'
        elif result['code'] == 500:
            return f"{result['message']}"
        else:
            return 'wuwuu好像出了点问题，过一会儿还是不行的话请联系麻麻~'

    except Exception:
        traceback.print_exc()
        return