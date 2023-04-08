from typing import List
import httpx
import traceback
import json
import jinja2
import re
import time
from pathlib import Path
from ..data_source import servers
from ..publicAPI import get_AccountIdByName
from ..utils import match_keywords
from ..html_render import html_to_pic
from ..wws_bind import get_DefaultBindInfo
from loguru import logger

dir_path = Path(__file__).parent.parent
template_path = dir_path / "template"
cfgpath = dir_path / 'config.json'
config = json.load(open(cfgpath, 'r', encoding='utf8'))
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_path), enable_async=True
)

headers = {
    'Authorization': config['token']
}
  

async def get_BanInfo(info,bot,ev):
    try:
        params = None
        if isinstance(info,List):
            for i in info:
                if i == 'me':
                    params = {
                    "server": "QQ",
                    "accountId": int(ev['user_id'])
                    }
                    break
                match = re.search(r"CQ:at,qq=(\d+)",i)
                if match:
                    params = {
                    "server": "QQ",
                    "accountId": int(match.group(1))
                    }
                    break
            if params:
                bindResult = await get_DefaultBindInfo(params['server'],params['accountId'])
                if bindResult:
                    if bindResult['serverType'] == 'cn':
                        param_accountid = int(bindResult['accountId'])
                    else:
                        return "目前仅支持国服查询"
                else:
                    return "未查询到该用户绑定信息，请使用wws 查询绑定 进行检查"
            elif not params and len(info) == 2:
                param_server,info = await match_keywords(info,servers)
                if param_server == 'cn':
                    param_accountid = await get_AccountIdByName(param_server,str(info[0]))
                    if not isinstance(param_accountid,int):
                        return f"{param_accountid}"
                else:
                    return '目前仅支持国服查询'
            else:
                return '您似乎准备用游戏昵称查询水表，请检查参数中时候包含服务器和游戏昵称，以空格区分'
        else:
            return '参数似乎出了问题呢'
        url = 'https://api.wows.shinoaki.com/public/wows/ban/cn/user'
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.post(url, json={"accountId":param_accountid}, timeout=None)
            result = resp.json()
        print(f"本次请求总耗时{resp.elapsed.total_seconds()*1000}，服务器计算耗时:{result['queryTime']}")
        if result['code'] == 200 and result['data']:
            template = env.get_template("wws-ban.html")
            template_data = {"data": result["data"]}
            content = await template.render_async(template_data)
            return await html_to_pic(content, wait=0, viewport={"width": 900, "height": 100})
        elif result["code"] == 404 and result["data"]:
            template = env.get_template("wws-unban.html")
            template_data = {"data": result["data"]}
            content = await template.render_async(template_data)
            return await html_to_pic(content, wait=0, viewport={"width": 900, "height": 100})
        else:
            return f"{result['message']}"
    except Exception:
        logger.error(traceback.format_exc())
        return 'wuwuwu出了点问题，请联系麻麻解决'