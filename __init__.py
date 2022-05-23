from distutils.log import info
from nonebot.typing import State_T
from pixivpy3 import *
from nonebot.exceptions import CQHttpError
import hoshino
from hoshino import R, Service, priv, get_bot
from hoshino.util import FreqLimiter, DailyNumberLimiter
from hoshino.typing import CQEvent, MessageSegment
from nonebot import NoticeSession, on_command
from .publicAPI import get_nation_list,get_ship_name
from .wws_info import get_AccountInfo
from .wws_recent import get_RecentInfo
import base64
from PIL import Image
from io import BytesIO
import traceback


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
    
@sv.on_prefix(('wws info','wwsinfo'))
async def send_account_info(bot, ev:CQEvent):
    uid = ev['user_id']
    searchtag = str(ev.message).strip()
    if not searchtag or searchtag=="":
        await bot.send(ev,'请在后方@对方QQ或输入服务器+游戏昵称')
        return
    elif ev.message[0].type == 'at':
        user = int(ev.message[0].data['qq'])
        msg = await get_AccountInfo(user)
    elif str(ev.message).strip() == 'me':
        msg = await get_AccountInfo(uid)
    else:
        infolist = str(ev.message).split()
        if len(infolist) != 2 :
            await bot.send(ev,"参数格式不正确，请确保后面跟随服务器和游戏昵称，以空格分隔")
        else:
            msg = await get_AccountInfo(infolist)
    if isinstance(msg, str):
        await bot.send(ev,msg)
    else:
        img_base64= base64.b64encode(msg).decode('utf8')
        await bot.send(ev,str(MessageSegment.image("base64://" + img_base64)))
    return
    
@sv.on_prefix(('wws recent','wwsrecent'))
async def send_recent_info(bot, ev:CQEvent):
    try:
        uid = ev['user_id']
        day,user = 1,0
        searchtag = str(ev.message).strip()
        if not searchtag or searchtag=="":
            await bot.send(ev,'请在后方输入查询天数和服务器账号/艾特QQ，以空格分隔')
            return
        infolist = str(ev.message).split()
        for message in ev.message:
            if message['type']== 'at':
                user = int(message['data']['qq'])
            if message['type'] =='text' and str(message['data']['text']).strip().isdigit():
                day = int(message['data']['text'])
        if user:
            msg = await get_RecentInfo(day,user)
        else:
            infolist = str(ev.message).split()
            if len(infolist) == 1 and infolist[0] == 'me':
                msg = await get_RecentInfo(day,uid)             
            elif len(infolist) == 2 and infolist[0].isdigit() and infolist[1] == 'me':
                msg = await get_RecentInfo(infolist[0],uid)
            elif len(infolist) == 2 and infolist[0] != 'me' and infolist[1] != 'me':
                msg = await get_RecentInfo(day,infolist)
            elif len(infolist) == 3 and infolist[0].isdigit() and infolist[1] != 'me' and infolist[2] != 'me':
                day = infolist[0]
                infolist.remove(day)
                msg = await get_RecentInfo(day,infolist)
            else:
                await bot.send(ev,"参数格式不正确，请确保后面按顺序跟随日期、服务器和游戏昵称（或艾特QQ），以空格分隔，日期留空则默认为一天")
                return
        if isinstance(msg, str):
            await bot.send(ev,msg)
        else:
            img_base64= base64.b64encode(msg).decode('utf8')
            await bot.send(ev,str(MessageSegment.image("base64://" + img_base64)))
        return
    except Exception:
        traceback.print_exc()
        await bot.send(ev,'呜呜呜发生了错误，如果过段时间不能恢复请联系麻麻哦~')
        return