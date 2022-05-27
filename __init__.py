from nonebot.typing import State_T
from nonebot.exceptions import CQHttpError
import hoshino
from hoshino import R, Service, priv, get_bot
from hoshino.util import FreqLimiter, DailyNumberLimiter
from hoshino.typing import CQEvent, MessageSegment
from nonebot import NoticeSession, on_command
from .publicAPI import get_nation_list,get_ship_name,get_ship_byName
from .wws_info import get_AccountInfo
from .wws_recent import get_RecentInfo
from .wws_bind import set_BindInfo,get_BindInfo,change_BindInfo
from .wws_ship import get_ShipInfo,SecletProcess
from .data_source import command_list
from .utils import match_keywords,find_and_replace_keywords
import base64
import traceback
import httpx
import json

_max = 100
EXCEED_NOTICE = f'您今天已经冲过{_max}次了，请明早5点后再来！'
_nlmt = DailyNumberLimiter(_max)
_flmt = FreqLimiter(5)
_version = "0.1.5"
WWS_help ="""
    帮助列表
    wws bind/set/绑定 服务器 游戏昵称：绑定QQ与游戏账号
    wws 查询绑定/查绑定/绑定列表[me][@]：查询指定用户的绑定账号
    wws 切换绑定[id]：使用查绑定中的序号快速切换绑定账号
    wws [服务器+游戏昵称][@群友][me]：查询账号总体战绩
    wws [服务器+游戏昵称][@群友][me] recent [日期]：查询账号近期战绩，默认1天
    wws [服务器+游戏昵称][@群友][me] ship 船名：查询单船总体战绩
    wws [搜/查船名] [国家][等级][类型]：查找符合条件的舰船中英文名称
    wws 检查更新
    [待开发] wws ship recent
    [待开发] wws rank
    以上指令参数顺序均无强制要求，即你完全可以发送wws eu 7 recent Test以查询欧服Test七天内的战绩
    搭建bot请加官方群：967546463，如果您觉得bot还可以的话请点个star哦~
    仓库地址：https://github.com/benx1n/wows-stats-bot
"""
sv_help = WWS_help.strip()
sv = Service('wows-stats-bot', manage_priv=priv.SUPERUSER, enable_on_default=True,help_ = sv_help)

@sv.on_fullmatch(('wws帮助','wws 帮助','wws help'))
async def get_help(bot, ev):
    await bot.send(ev, sv_help)

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
        select_command = None
        searchtag = str(ev.message).strip()
        if not searchtag or searchtag=="":
            await bot.send(ev,WWS_help.strip())
            return
        search_list = str(ev.message).split()
        select_command,search_list = await find_and_replace_keywords(search_list,command_list)
        if not select_command:
            msg = await get_AccountInfo(qqid,search_list)
        elif select_command == 'ship':
            select_command = None
            select_command,search_list = await find_and_replace_keywords(search_list,command_list)         #第二次匹配
            if not select_command:
                msg = await get_ShipInfo(qqid,search_list,bot,ev)
            elif select_command == 'recent':
                msg = '待开发：查单船近期战绩'
            else:
                msg = '看不懂指令QAQ'
        elif select_command == 'recent':
            select_command = None
            select_command,search_list = await find_and_replace_keywords(search_list,command_list)             #第二次匹配
            if not select_command:
                msg = await get_RecentInfo(qqid,search_list)
            elif select_command == 'ship':
                msg = '待开发：查单船近期战绩'
            else:
                msg = '：看不懂指令QAQ'
        elif select_command == 'bind':
            msg = await set_BindInfo(qqid,search_list)
        elif select_command == 'bindlist':
            msg = await get_BindInfo(qqid,search_list)
        elif select_command == 'changebind':
            msg = await change_BindInfo(qqid,search_list)
        elif select_command == 'searchship':
            msg = await get_ship_name(search_list)
        else:
            msg = '看不懂指令QAQ'
        if isinstance(msg,str):
            await bot.send(ev,msg)
        else:
            img_base64= base64.b64encode(msg).decode('utf8')
            await bot.send(ev,str(MessageSegment.image("base64://" + img_base64)))
        return
    except Exception:
        traceback.print_exc()
        await bot.send(ev,'呜呜呜发生了错误，可能是网络问题，如果过段时间不能恢复请联系麻麻哦~')
        return

@sv.on_message()
async def change_select_state(bot, ev):
    msg = ev["raw_message"]
    qqid = ev['user_id']
    if SecletProcess[qqid].SelectList and str(msg).isdigit():
        SecletProcess[qqid] = SecletProcess[qqid]._replace(state = True)
        SecletProcess[qqid] = SecletProcess[qqid]._replace(SlectIndex = int(msg))
    return

@sv.on_fullmatch('wws 检查更新')
async def check_version(bot, ev:CQEvent):
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

@sv.scheduled_job('cron',hour='12')
async def job1():
    bot = get_bot()
    ev = CQEvent
    await check_version(bot,ev)