import asyncio
import html
import random
import re
import traceback

import hoshino
import httpx
import orjson
from hoshino import R, Service, get_bot, priv
from hoshino.typing import CQEvent, MessageSegment
from hoshino.util import DailyNumberLimiter, FreqLimiter
from loguru import logger
from nonebot import NoticeSession, on_command
from nonebot.exceptions import CQHttpError
from nonebot.typing import State_T

from .command_select import select_command
from .data_source import config, dir_path, template_path
from .game.ocr import downlod_OcrResult, pic2txt_byOCR, upload_OcrResult
from .game.pupu import get_pupu_msg
from .html_render import text_to_pic
from .HttpClient_pool import client_default
from .moudle.publicAPI import get_nation_list
from .utils import bytes2b64
from .moudle.wws_clan import ClanSecletProcess
from .moudle.wws_ship import ShipSecletProcess

_max = 100
EXCEED_NOTICE = f'您今天已经冲过{_max}次了，请明早5点后再来！'
_nlmt = DailyNumberLimiter(_max)
_flmt = FreqLimiter(3)
_version = "0.3.8"
WWS_help ="""请发送wws help查看帮助"""
sv_help = WWS_help.strip()
sv = Service('wows-stats-bot', manage_priv=priv.SUPERUSER, enable_on_default=True,help_ = sv_help)

@sv.on_fullmatch(('wws帮助','wws 帮助','wws help'))
async def get_help(bot, ev):
    url = 'https://benx1n.oss-cn-beijing.aliyuncs.com/version.json'
    resp = await client_default.get(url, timeout=10)
    result = orjson.loads(resp.content)
    latest_version = result['latest_version']
    url = 'https://benx1n.oss-cn-beijing.aliyuncs.com/wws_help.txt'
    resp = await client_default.get(url, timeout=10)
    result = resp.text
    result = f'''帮助列表                                                当前版本{_version}  最新版本{latest_version}\n{result}'''
    img = await text_to_pic(text = result, width = 800)
    await bot.send(ev,str(MessageSegment.image(bytes2b64(img))))
    return

@sv.on_prefix(('wws 地区','wws地区'))
async def send_nation_info(bot, ev:CQEvent):
    msg = await get_nation_list()
    if msg:
        await bot.send(ev,msg)
    else:
        await bot.send(ev,"wuwuwu~好像出了点问题")
    return

@sv.on_prefix(('wws'))
async def main(bot,ev:CQEvent):
    try:
        qqid = ev['user_id']
        if not _nlmt.check(qqid):
            await bot.send(ev, EXCEED_NOTICE, at_sender=True)
            return
        if not _flmt.check(qqid):
            await bot.send(ev, '您冲得太快了，请稍候再冲', at_sender=True)
            return
        _flmt.start_cd(qqid)
        _nlmt.increase(qqid) 
        if random.randint(1,1000) == 1:
            await bot.send(ev, "一天到晚惦记你那b水表，就nm离谱")
            return
        replace_name = None
        searchtag = html.unescape(str(ev.message)).strip()
        if not searchtag:
            await bot.send(ev,WWS_help.strip())
            return
        match = re.search(r"(\(|（)(.*?)(\)|）)",searchtag)
        if match:
            replace_name = match.group(2)
            search_list = searchtag.replace(match.group(0),'').split()
        else:
            search_list = searchtag.split()
        command,search_list = await select_command(search_list)
        if replace_name:
            search_list.append(replace_name)
        msg = await command(search_list,bot,ev)
        if msg:
            if isinstance(msg,str):
                await bot.send(ev,msg)
            else:
                await bot.send(ev,str(MessageSegment.image(bytes2b64(msg))))
        else:
            await bot.send(ev,'没有获取到数据，可能是内部问题')
        return
    except CQHttpError:
        logger.error(traceback.format_exc())
        try:
            await bot.send(ev,'发不出图片，可能被风控了QAQ')
        except Exception:
            pass
        return
    except Exception:
        logger.error(traceback.format_exc())
        await bot.send(ev,'呜呜呜发生了错误，可能是网络问题，如果过段时间不能恢复请联系麻麻哦~')
        return

@sv.on_message()
async def change_select_state(bot, ev):
    try:
        msg = ev["raw_message"]
        qqid = ev['user_id']
        if ShipSecletProcess[qqid].SelectList and str(msg).isdigit():
            if int(msg) <= len( ShipSecletProcess[qqid].SelectList):
                ShipSecletProcess[qqid] = ShipSecletProcess[qqid]._replace(state = True)
                ShipSecletProcess[qqid] = ShipSecletProcess[qqid]._replace(SlectIndex = int(msg))
            else:
                await bot.send(ev,'请选择列表中的序号哦~')
        if ClanSecletProcess[qqid].SelectList and str(msg).isdigit():
            if int(msg) <= len( ClanSecletProcess[qqid].SelectList):
                ClanSecletProcess[qqid] = ClanSecletProcess[qqid]._replace(state = True)
                ClanSecletProcess[qqid] = ClanSecletProcess[qqid]._replace(SlectIndex = int(msg))
            else:
                await bot.send(ev,'请选择列表中的序号哦~') 
        return
    except Exception:
        logger.error(traceback.format_exc())
        return

@sv.on_fullmatch('wws 检查更新')
async def check_version(bot, ev:CQEvent):
    try:
        url = 'https://benx1n.oss-cn-beijing.aliyuncs.com/version.json'
        resp = await client_default.get(url, timeout=10)
        result = orjson.loads(resp.content)
        bot = hoshino.get_bot()
        superid = hoshino.config.SUPERUSERS[0]
        match,msg = False,f'发现新版本'
        for each in result['data']:
            if each['version'] > _version:
                match = True
                msg += f"\n{each['date']} v{each['version']}\n"
                for i in each['description']:
                    msg += f"{i}\n"
        if match:
                await bot.send_private_msg(user_id=superid, message=msg)
                try:
                    await bot.send(ev,msg)
                except Exception:
                    logger.error(traceback.format_exc())
                    return     
        return
    except Exception:
        logger.error(traceback.format_exc())
        return
    
@sv.on_fullmatch('wws 更新样式')
async def startup(bot, ev:CQEvent):
    try:
        tasks = []
        url = 'https://benx1n.oss-cn-beijing.aliyuncs.com/template_Hoshino_Latest/template.json'
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=20)
            result = orjson.loads(resp.content)
            for each in result:
                for name, url in each.items():
                    tasks.append(asyncio.ensure_future(startup_download(url, name)))
        await asyncio.gather(*tasks)
    except Exception:
        logger.error(traceback.format_exc())
        return 
    
async def startup_download(url,name):
    async with httpx.AsyncClient() as client:
        resp = resp = await client.get(url, timeout=20)
        with open(template_path/name , "wb+") as file:
            file.write(resp.content)
            
@sv.scheduled_job('cron',hour='12')
async def job1():
    bot = get_bot()
    ev = CQEvent
    await check_version(bot,ev)
    
@sv.scheduled_job('cron',hour='12')
async def job2():
    bot = get_bot()
    ev = CQEvent
    await startup(bot,ev)
    
@sv.scheduled_job('interval',minutes=10)
async def job3():
    await downlod_OcrResult()
    
logger.add(
    str(dir_path/"logs/error.log"),
    rotation="00:00",
    retention="1 week",
    diagnose=False,
    level="ERROR",
    encoding="utf-8",
)
logger.add(
    str(dir_path/"logs/info.log"),
    rotation="00:00",
    retention="1 week",
    diagnose=False,
    level="INFO",
    encoding="utf-8",
)
logger.add(
    str(dir_path/"logs/warning.log"),
    rotation="00:00",
    retention="1 week",
    diagnose=False,
    level="WARNING",
    encoding="utf-8",
)


@sv.on_fullmatch('噗噗')
async def send_pupu_msg(bot, ev:CQEvent):
    try:
        if config['pupu']:
            msg = await get_pupu_msg()
            await bot.send(ev,msg)
    except CQHttpError:
        logger.error(traceback.format_exc())
        try:
            await bot.send(ev,'噗噗寄了>_<可能被风控了QAQ')
        except Exception:
            pass
        return
    except Exception:
        logger.error(traceback.format_exc())
        await bot.send(ev,'呜呜呜发生了错误，可能是网络问题，如果过段时间不能恢复请联系麻麻哦~')
        return
    
@sv.on_message()
async def OCR_listen(bot, ev:CQEvent):
    try:
        if not config['ocr_on']:
            return
        if not (str(ev.message).find("[CQ:image")+1):  #判断收到的信息是否为图片，不是就退出
            return
        for seg in ev.message:
            if seg.type == 'image':
                tencent_url = seg.data['url']
                filename = str(seg.data['file']).replace(".image","")
        ocr_text = await pic2txt_byOCR(tencent_url,filename)
        if ocr_text:
            match = re.search(r"^(/?)wws(.*?)$",ocr_text)
            if match:
                qqid = ev['user_id']
                if not _nlmt.check(qqid):
                    await bot.send(ev, EXCEED_NOTICE, at_sender=True)
                    return
                if not _flmt.check(qqid):
                    await bot.send(ev, '您冲得太快了，请稍候再冲', at_sender=True)
                    return
                _flmt.start_cd(qqid)
                _nlmt.increase(qqid) 
                replace_name = None
                searchtag = re.sub(r"^(/?)wws","",ocr_text)        #删除wws和/wws
                searchtag = html.unescape(str(searchtag)).strip()
                if not searchtag:
                    await bot.send(ev,WWS_help.strip())
                    return
                match = re.search(r"(\(|（)(.*?)(\)|）)",searchtag)
                if match:
                    replace_name = match.group(2)
                    search_list = searchtag.replace(match.group(0),'').split()
                else:
                    search_list = searchtag.split()
                command,search_list = await select_command(search_list)
                if replace_name:
                    search_list.append(replace_name)
                msg = await command(search_list,bot,ev)
                if msg:
                    if isinstance(msg,str):
                        await bot.send(ev,msg)
                        await upload_OcrResult(ocr_text,filename)
                    else:
                        await bot.send(ev,str(MessageSegment.image(bytes2b64(msg))))
                        await upload_OcrResult(ocr_text,filename)
                else:
                    await bot.send(ev,'没有获取到数据，可能是内部问题')
            else:
                return
    except CQHttpError:
        logger.error(traceback.format_exc())
        try:
            await bot.send(ev,'发不出图片，可能被风控了QAQ')
        except Exception:
            pass
    except Exception:
        logger.error(traceback.format_exc())
        return