from nonebot.typing import State_T
from nonebot.exceptions import CQHttpError
import hoshino
from hoshino import R, Service, priv, get_bot
from hoshino.util import FreqLimiter, DailyNumberLimiter
from hoshino.typing import CQEvent, MessageSegment
from nonebot import NoticeSession, on_command
from .html_render import text_to_pic
from .publicAPI import get_nation_list,get_ship_name,get_ship_byName
from .wws_info import get_AccountInfo
from .wws_recent import get_RecentInfo
from .wws_bind import set_BindInfo,get_BindInfo,change_BindInfo,set_special_BindInfo,delete_BindInfo
from .wws_ship import get_ShipInfo,get_ShipInfoRecent,ShipSecletProcess
from .wws_clan import get_ClanInfo,ClanSecletProcess
from .wws_record import get_record
from .wws_shiprank import get_ShipRank
from .data_source import command_list
from .utils import match_keywords,find_and_replace_keywords,bytes2b64
import traceback
import httpx
import json
import re
import html

_max = 100
EXCEED_NOTICE = f'您今天已经冲过{_max}次了，请明早5点后再来！'
_nlmt = DailyNumberLimiter(_max)
_flmt = FreqLimiter(3)
_version = "0.3.1"
WWS_help ="""请发送wws help查看帮助"""
sv_help = WWS_help.strip()
sv = Service('wows-stats-bot', manage_priv=priv.SUPERUSER, enable_on_default=True,help_ = sv_help)

@sv.on_fullmatch(('wws帮助','wws 帮助','wws help'))
async def get_help(bot, ev):
    url = 'https://benx1n.oss-cn-beijing.aliyuncs.com/version.json'
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
        result = json.loads(resp.text)
    latest_version = result['latest_version']
    url = 'https://benx1n.oss-cn-beijing.aliyuncs.com/wws_help.txt'
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
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
async def selet_command(bot,ev:CQEvent):
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
        select_command,replace_name = None,None
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
        select_command,search_list = await find_and_replace_keywords(search_list,command_list)
        if not select_command:
            if replace_name:
                search_list.append(replace_name)
            msg = await get_AccountInfo(qqid,search_list)
        elif select_command == 'ship':
            select_command = None
            select_command,search_list = await find_and_replace_keywords(search_list,command_list)         #第二次匹配
            if replace_name:
                search_list.append(replace_name)
            if not select_command:
                msg = await get_ShipInfo(qqid,search_list,bot,ev)
            elif select_command == 'recent':
                msg = await get_ShipInfoRecent(qqid,search_list,bot,ev)
            else:
                msg = '看不懂指令QAQ'
        elif select_command == 'recent':
            select_command = None
            select_command,search_list = await find_and_replace_keywords(search_list,command_list)             #第二次匹配
            if replace_name:
                search_list.append(replace_name)
            if not select_command:
                msg = await get_RecentInfo(qqid,search_list)
            elif select_command == 'ship':
                msg = await get_ShipInfoRecent(qqid,search_list,bot,ev)
            else:
                msg = '：看不懂指令QAQ'
        elif select_command == 'clan':
            select_command = None
            select_command,search_list = await find_and_replace_keywords(search_list,command_list) 
            if not select_command:                  #查询公会详情信息
                msg = await get_ClanInfo(qqid,search_list,bot,ev)
            elif select_command == 'record':        #查询公会历史记录
                msg = await get_record(qqid,search_list,"clan")
        elif select_command == 'record':
            select_command = None
            select_command,search_list = await find_and_replace_keywords(search_list,command_list) 
            if replace_name:
                search_list.append(replace_name)
            if not select_command:                  #查询个人历史记录
                msg = await get_record(qqid,search_list,"personal")
            elif select_command == 'clan':          #查询公会历史记录
                msg = await get_record(qqid,search_list,"clan")
        elif select_command == 'ship_rank':
            msg = await get_ShipRank(qqid,search_list,bot,ev)
        elif select_command == 'special_bind':
            msg = await set_special_BindInfo(qqid,search_list)
        elif select_command == 'bind':
            if replace_name:
                search_list.append(replace_name)
            msg = await set_BindInfo(qqid,search_list)
        elif select_command == 'bindlist':
            msg = await get_BindInfo(qqid,search_list)
        elif select_command == 'changebind':
            msg = await change_BindInfo(qqid,search_list)
        elif select_command == 'delete_bind':
            msg = await delete_BindInfo(qqid,search_list)
        elif select_command == 'searchship':
            msg = await get_ship_name(search_list)
        else:
            msg = '看不懂指令QAQ'
        if msg:
            if isinstance(msg,str):
                await bot.send(ev,msg)
            else:
                await bot.send(ev,str(MessageSegment.image(bytes2b64(msg))))
        else:
            await bot.send('呜呜呜发生了错误，可能是网络问题，如果过段时间不能恢复请联系麻麻哦~')
        return
    except Exception:
        traceback.print_exc()
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
        traceback.print_exc()
        return

@sv.on_fullmatch('wws 检查更新')
async def check_version(bot, ev:CQEvent):
    try:
        url = 'https://benx1n.oss-cn-beijing.aliyuncs.com/version.json'
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
            result = json.loads(resp.text)
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
                    traceback.print_exc()
                    return     
        return
    except Exception:
        traceback.print_exc()
        return

@sv.scheduled_job('cron',hour='12')
async def job1():
    bot = get_bot()
    ev = CQEvent
    await check_version(bot,ev)