from typing import List
import httpx
import traceback
import json
import jinja2
import re
from pathlib import Path
from .data_source import servers,set_clanRecord_params
from .publicAPI import get_AccountIdByName
from .utils import match_keywords
from .html_render import html_to_pic
from bs4 import BeautifulSoup

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
  

async def get_clanRecord(qqid,info):
    try:
        params = None
        if isinstance(info,List):
            for i in info:
                if i == 'me':
                    url = 'https://api.wows.linxun.link/upload/numbers/data/upload/user/clan/record'
                    params = {
                    "server": "QQ",
                    "accountId": str(qqid)
                    }
                    break
                match = re.search(r"CQ:at,qq=(\d+)",i)
                if match:
                    url = 'https://api.wows.linxun.link/upload/numbers/data/upload/user/clan/record'
                    params = {
                    "server": "QQ",
                    "accountId": match.group(1)
                    }
                    break
            if not params and len(info) == 2:
                param_server,info = await match_keywords(info,servers)
                if param_server and param_server != 'cn':
                    param_accountid = await get_AccountIdByName(param_server,str(info[0]))
                    if isinstance(param_accountid,int):
                        url = 'https://api.wows.linxun.link/upload/numbers/data/upload/user/clan/record'
                        params = {
                        "server": param_server,
                        "accountId": param_accountid
                        }
                    else:
                        return f"{param_accountid}"
                elif param_server == 'cn':
                    return '暂不支持国服'
                else:
                    return '服务器参数似乎输错了呢'
            elif params:
                print('下面是本次请求的参数，如果遇到了问题，请将这部分连同报错日志一起发送给麻麻哦')
            else:
                return '您似乎准备用游戏昵称查询公会进出记录，请检查参数中时候包含服务器和游戏昵称，以空格区分，如果您准备查询单船战绩，请带上ship参数'
        else:
            return '参数似乎出了问题呢'
        print(params)
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=None)
            result = resp.json()
        if result['code'] == 200 and result['data']:
            template = env.get_template("wws-clanRecord.html")
            template_data = {"data":result['data']}
            content = await template.render_async(template_data)
            return await html_to_pic(content, wait=0, viewport={"width": 920, "height": 100})
        elif result['code'] == 403:
            return f"{result['message']}\n请检查昵称或绑定账号"
        elif result['code'] == 404:
            template = env.get_template("wws-clanRecord.html")
            template_data = await get_ClanRecord_Numbers(result['data'][0]['httpUrl'],params)
            print(template_data)
            if template_data:
                template_data = {"data":template_data}
            else:
                return '查询失败了呢，可能是没有进出记录'
            content = await template.render_async(template_data)
            return await html_to_pic(content, wait=0, viewport={"width": 920, "height": 100})
        elif result['code'] == 500:
            return f"{result['message']}\n这是服务器问题，请联系雨季麻麻"
        else:
            return f"{result['message']}"
    except Exception:
        traceback.print_exc()
        return 'wuwuwu出了点问题，请联系麻麻解决，目前不支持国服哦'
    
    
async def get_ClanRecord_Numbers(url,params):
    try:
        data = None
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=None)
            soup = BeautifulSoup(resp.content, 'html.parser')
            data = soup.select(f'table[class="table table-styled table-bordered cells-middle"]')
            data = data[len(data)-1].select(f'tr')
            info_list = []
            for each in data:
                class_list = each.select('td span')[0].attrs['class']
                for classes in class_list:
                    if classes == 'transfer-out':
                        status = 1
                    else:
                        status = 0
                timeGroup = re.match( r'(.*?)\.(.*?)\.(.*?)$', each.select('td')[1].string)
                time = f"{timeGroup.group(3)}.{timeGroup.group(2)}.{timeGroup.group(1)}"
                clanId = re.match( r'\/clan\/(.*?),', each.select('td a')[0].attrs['href']).group(1)
                clanName = each.select('td a')[0].string
                params['accountId'] = int(params['accountId'])
                params['clanId'] = int(clanId)
                params['status'] = status
                params['time'] = time
                params['clanName'] = clanName
                info_list.append(params.copy())
            result = await post_ClanRecord_yuyuko(info_list)
            if result:
                return result
            else:
                return None
    except Exception:
        traceback.print_exc()
        return None
    
async def post_ClanRecord_yuyuko(post_data):
    try:
        async with httpx.AsyncClient(headers=headers) as client:
            url = 'https://api.wows.linxun.link/upload/numbers/data/upload/user/clan/record'
            resp = await client.post(url, json = post_data, timeout=None)
            result = resp.json()
            if result['code'] == 200 and result['data']:
                return result['data']
            else:
                return None
    except Exception:
        traceback.print_exc()
        return None