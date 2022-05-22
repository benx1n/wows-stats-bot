from nonebot.typing import State_T
from pixivpy3 import *
from nonebot.exceptions import CQHttpError
import hoshino
from hoshino import R, Service, priv, get_bot
from hoshino.util import FreqLimiter, DailyNumberLimiter
from hoshino.typing import CQEvent, MessageSegment
from nonebot import NoticeSession, on_command
from .publicAPI import get_nation_list,get_ship_name

sv = Service('wows-stats-bot', manage_priv=priv.SUPERUSER, enable_on_default=True)

@sv.on_prefix(('wws 地区','wws地区'))
async def send_nation_info(bot, ev:CQEvent):
    msg = await get_nation_list()
    if msg:
        await bot.send(ev,msg)
    else:
        await bot.send(ev,"wuwuwu~好像出了点问题")
    return

@sv.on_prefix(('wws 船名','wws船名'))
async def send_ship_name(bot, ev:CQEvent):
    infolist = str(ev.message).split()
    if len(infolist) != 3 :
        await bot.send(ev,"参数格式不正确，请确保后面跟随国家、等级、船只类型，以空格分隔")
        return
    else:
        msg = await get_ship_name(infolist)
        if msg:
            await bot.send(ev,str(msg))
        else:
            await bot.send(ev,"wuwuwu~好像出了点问题")
        return