from typing import List
import httpx
import traceback
import json
import jinja2
import re
import asyncio
from pathlib import Path
from hoshino.typing import MessageSegment
#from .data_source import servers,set_clanparams
from .utils import match_keywords,bytes2b64
from.publicAPI import get_ClanIdByName
from collections import defaultdict, namedtuple
from .html_render import html_to_pic,text_to_pic

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

ClanSlectState = namedtuple("ClanSlectState", ['state','SlectIndex','SelectList'])
ClanSecletProcess = defaultdict(lambda: ClanSlectState(False, None, None))

async def get_ClanInfo(qqid,info,bot,ev):
    try:
        params = None
        if isinstance(info,List):
            for flag,i in enumerate(info):              #是否包含me或@，包含则调用平台接口
                if i == 'me':
                    url = ''
                    params = {
                    "server": "QQ",
                    "clanId": qqid,
                    }
                    info.remove("me")
                match = re.search(r"CQ:at,qq=(\d+)",i)
                if match:
                    url = ''
                    params = {
                    "server": "QQ",
                    "clanId": match.group(1),
                    }
                    info[flag] = str(i).replace(f"[{match.group(0)}]",'')
                    if not info[flag]:
                        info.remove('')
                    break
            if not params and len(info) == 2:
                param_server,info = await match_keywords(info,servers)
                if param_server:
                    clanList = await get_ClanIdByName(param_server,str(info[0])) 
                    if clanList:
                        if len(clanList) < 2:
                            selectClanId = clanList[0][0]
                        else:
                            msg = f'存在多个名字相似的军团\n请在20秒内选择对应的序号\n================\n'
                            flag = 0
                            for each in clanList:
                                flag += 1
                                msg += f"{flag}：{each[1]}\n"
                            ClanSecletProcess[qqid] = ClanSecletProcess(False, None, clanList)
                            img = await text_to_pic(text=msg,css_path = template_path/"text-ship.css",width=250)
                            await bot.send(ev,str(MessageSegment.image(bytes2b64(img))))
                            await asyncio.sleep(20)
                            if ClanSecletProcess[qqid].state and ClanSecletProcess[qqid].SlectIndex <= len(clanList):
                                selectClanId = clanList[ClanSecletProcess[qqid].SlectIndex-1][0]
                            else:
                                return '已超时退出'
                    else:
                        return '找不到军团'
                    if selectClanId :
                        url = ''
                        params = {
                        "server": param_server,
                        "clanId": selectClanId,
                        }
                    else:
                        return '发生了错误，有可能是网络波动，请稍后再试'
                else:
                    return '服务器参数似乎输错了呢'
            else:
                return '您似乎准备用军团名查询军团详情，请检查参数中是否包含服务器、军团名，以空格区分'
        else:
            return '参数似乎出了问题呢'
        print(f"下面是本次请求的参数，如果遇到了问题，请将这部分连同报错日志一起发送给麻麻哦\n{params}")
        async with httpx.AsyncClient(headers=headers) as client:
            resp = await client.get(url, params=params, timeout=20)
            result = resp.json()
        if result['code'] == 200 and result['data']:
            template = env.get_template("wws-clan.html")
            #template_data = await set_clanparams(result['data'])
            content = await template.render_async(template_data)
            return await html_to_pic(content, wait=0, viewport={"width": 800, "height": 100})
        elif result['code'] == 403:
            return f"{result['message']}\n请先绑定账号"
        elif result['code'] == 404 or result['code'] == 405:
            return f"{result['message']}"
        elif result['code'] == 500:
            return f"{result['message']}\n这是服务器问题，请联系雨季麻麻"
        else:
            return 'wuwuu好像出了点问题，可能是网络问题，过一会儿还是不行的话请联系麻麻~'
    except Exception:
        traceback.print_exc()
        return 