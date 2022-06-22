import httpx
import traceback
import json
import jinja2
import asyncio
from pathlib import Path
from hoshino.typing import MessageSegment
from .data_source import servers,set_shipparams,tiers,number_url_homes,set_ShipRank_Numbers
from .utils import match_keywords,bytes2b64
from .wws_ship import ShipSecletProcess,ShipSlectState
from.publicAPI import get_ship_byName
from bs4 import BeautifulSoup
from .html_render import html_to_pic,text_to_pic

dir_path = Path(__file__).parent
template_path = dir_path / "template"
cfgpath = dir_path / 'config.json'
config = json.load(open(cfgpath, 'r', encoding='utf8'))
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_path), enable_async=True
)

headers = {
    'Authorization': config['token'],
    'accept':'application/json',
    'Content-Type':'application/json',
}

async def get_ShipRank(qqid,info,bot,ev):
    try:
        if len(info) == 2:
            param_server,info = await match_keywords(info,servers)
            if param_server and not param_server == 'cn':
                number_url = number_url_homes[param_server] + "/ship/"
            else:
                return '请检查服务器是否正确，暂不支持国服'
        else:
            return '参数似乎出了问题呢'
        shipList = await get_ship_byName(str(info[0]))
        print(shipList)
        if shipList:
            if len(shipList) < 2:
                select_shipId = shipList[0][0]
                number_url += f"{select_shipId},{shipList[0][2]}"
            else:
                msg = f'存在多条名字相似的船\n请在20秒内选择对应的序号\n=================\n'
                flag = 0
                for each in shipList:
                    flag += 1
                    msg += f"{flag}：{tiers[each[3]-1]} {each[1]}\n"
                ShipSecletProcess[qqid] = ShipSlectState(False, None, shipList)
                img = await text_to_pic(text=msg,width=230)
                await bot.send(ev,str(MessageSegment.image(bytes2b64(img))))
                a = 0
                while a < 40 and not ShipSecletProcess[qqid].state:
                    a += 1
                    await asyncio.sleep(0.5)
                if ShipSecletProcess[qqid].state and ShipSecletProcess[qqid].SlectIndex <= len(shipList):
                    select_shipId = int(shipList[ShipSecletProcess[qqid].SlectIndex-1][0])
                    number_url += f"{select_shipId},{shipList[ShipSecletProcess[qqid].SlectIndex-1][2]}"
                    ShipSecletProcess[qqid] = ShipSlectState(False, None, None)
                    print(number_url)
                else:
                    ShipSecletProcess[qqid] = ShipSlectState(False, None, None)
                    return '已超时退出'
        else:
            return '找不到船'
        content = await search_ShipRank_Yuyuko(select_shipId,param_server)
        if content:                                         #存在缓存，直接出图
            return await html_to_pic(content, wait=0, viewport={"width": 1300, "height": 100})
        else:                                               #无缓存，去Number爬
            content,numbers_data = await search_ShipRank_Numbers(number_url,param_server,select_shipId)
            if content:
                await post_ShipRank(numbers_data)     #上报Yuyuko
                return await html_to_pic(content, wait=0, viewport={"width": 1300, "height": 100})
            else:
                return 'wuwuu好像出了点问题，可能是网络问题，过一会儿还是不行的话请联系麻麻~'   
    except Exception:
        traceback.print_exc()
        return 'wuwuu好像出了点问题，过一会儿还是不行的话请联系麻麻~'    
   
async def search_ShipRank_Yuyuko(shipId,server):
    try:
        content = None
        async with httpx.AsyncClient(headers=headers) as client:        #查询是否有缓存
            url = 'https://api.wows.linxun.link/upload/numbers/data/v2/upload/ship/rank'
            params = {
                "server":server,
                "shipId":int(shipId)
            }
            print(f"{url}\n{params}")
            resp = await client.get(url, params=params,timeout=20)
            result = resp.json()
            if result['code'] == 200 and result['data']:
                result_data = {"data":result['data']}
                template = env.get_template("ship-rank.html")
                content = await template.render_async(result_data)
                return content
            else:
                return None
    except Exception:
        traceback.print_exc()
        return None 
        
async def search_ShipRank_Numbers(url,server,shipId):
    try:
        content = None
        print(url)
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=20)
        soup = BeautifulSoup(resp.content, 'html.parser')
        data = soup.select('tr[class="cells-middle"]')
        infoList = await set_ShipRank_Numbers(data,server,shipId)
        if infoList:
            result_data = {"data":infoList}
            template = env.get_template("ship-rank.html")
            content = await template.render_async(result_data)
            return content,infoList
        else:
            return None,None
    except Exception:
        traceback.print_exc()
        return None,None
            
async def post_ShipRank(data):
    try:
        async with httpx.AsyncClient(headers=headers) as client:
            url = 'https://api.wows.linxun.link/upload/numbers/data/v2/upload/ship/rank'
            resp = await client.post(url, json = data, timeout=20)
            print(resp.request)
            result = resp.json()
            print(result)
    except Exception:
        traceback.print_exc()