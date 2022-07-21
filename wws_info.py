from typing import List
import httpx
import traceback
import json
import jinja2
import re
import time
from pathlib import Path
from .data_source import servers,set_infoparams,set_damageColor,set_winColor,set_upinfo_color
from .publicAPI import get_AccountIdByName
from .utils import match_keywords
from .html_render import html_to_pic
from loguru import logger

dir_path = Path(__file__).parent
template_path = dir_path / "template"
cfgpath = dir_path / 'config.json'
config = json.load(open(cfgpath, 'r', encoding='utf8'))
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_path), enable_async=True
)
env.globals.update(set_damageColor=set_damageColor,set_winColor=set_winColor,set_upinfo_color=set_upinfo_color,time=time,int=int,abs=abs,enumerate=enumerate)

headers = {
    'Authorization': config['token']
}
  

async def get_AccountInfo(qqid,info):
    try:
        params = None
        if isinstance(info,List):
            for i in info:
                if i == 'me':
                    params = {
                    "server": "QQ",
                    "accountId": int(qqid)
                    }
                    break
                match = re.search(r"CQ:at,qq=(\d+)",i)
                if match:
                    params = {
                    "server": "QQ",
                    "accountId": int(match.group(1))
                    }
                    break
            if not params and len(info) == 2:
                param_server,info = await match_keywords(info,servers)
                if param_server:
                    param_accountid = await get_AccountIdByName(param_server,str(info[0]))
                    if isinstance(param_accountid,int):
                        params = {
                        "server": param_server,
                        "accountId": param_accountid
                        }
                    else:
                        return f"{param_accountid}"
                else:
                    return '服务器参数似乎输错了呢'
            elif params:
                print('下面是本次请求的参数，如果遇到了问题，请将这部分连同报错日志一起发送给麻麻哦')
            else:
                return '您似乎准备用游戏昵称查询水表，请检查参数中时候包含服务器和游戏昵称，以空格区分，如果您准备查询单船战绩，请带上ship参数'
        else:
            return '参数似乎出了问题呢'
        print(params)
        url = 'https://api.wows.shinoaki.com/public/wows/account/user/info'
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=None)
            result = resp.json()
        print(f"本次请求总耗时{resp.elapsed.total_seconds()*1000}，服务器计算耗时:{result['queryTime']}")
        if result['code'] == 200 and result['data']:
            template = env.get_template("wws-info.html")
            template_data = await set_infoparams(result['data'])
            content = await template.render_async(template_data)
            return await html_to_pic(content, wait=0, viewport={"width": 920, "height": 1000})
        elif result['code'] == 403:
            return f"{result['message']}\n请先绑定账号"
        elif result['code'] == 500:
            return f"{result['message']}\n这是服务器问题，请联系雨季麻麻"
        else:
            return f"{result['message']}"
    except Exception:
        logger.error(traceback.format_exc())
        return 'wuwuwu出了点问题，请联系麻麻解决'