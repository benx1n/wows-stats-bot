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
from .wws_bind import set_BindInfo,get_BindInfo,change_BindInfo
from .data_source import command_list
from .utils import match_keywords,find_and_replace_keywords
import base64
from PIL import Image
from io import BytesIO
import traceback
import re

WWS_help ="""
    帮助列表
    wws bind/set/绑定 服务器 游戏昵称：绑定QQ与游戏账号
    wws 查询绑定/查绑定/绑定列表[me][@]：查询指定用户的绑定账号
    wws 切换绑定[id]：使用查绑定中的序号快速切换绑定账号
    wws [服务器+游戏昵称][@群友][me]：查询账号总体战绩
    wws [服务器+游戏昵称][@群友][me] recent [日期]：查询账号近期战绩，默认1天
    wws 船名 [国家][等级][类型]：查找符合条件的舰船中英文名称
    [待开发] wws ship
    [待开发] wws ship recent
    以上指令参数顺序均无强制要求，即你完全可以发送wws eu 7 recent Test以查询欧服Test七天内的战绩
"""
sv_help = WWS_help.strip()
sv = Service('wows-stats-bot', manage_priv=priv.SUPERUSER, enable_on_default=True,help_ = sv_help)

@sv.on_fullmatch('wws帮助','wws 帮助','wws help')
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

# @sv.on_prefix(('wws 查询绑定','wws查询绑定','wws 查绑定','wws查绑定'))
# async def send_bind_search(bot, ev:CQEvent):
#     try:
#         uid = ev['user_id']
#         searchtag = str(ev.message).strip()
#         if not searchtag or searchtag=="":
#             await bot.send(ev,'请在后方艾特要查询的QQ，查询自己请输入me')
#             return
#         elif ev.message[0].type == 'at':
#             user = int(ev.message[0].data['qq'])
#         elif str(ev.message).strip() == 'me':
#             user = uid
#         else:
#             await bot.send(ev,'参数格式不正确，请在后方艾特要查询的QQ，查询自己请输入me')
#             return
#         msg = await get_BindInfo(user)
#         await bot.send(ev,str(msg))
#     except Exception:
#         traceback.print_exc()
#         await bot.send(ev,'呜呜呜发生了错误，如果过段时间不能恢复请联系麻麻哦~')
#         return

@sv.on_prefix(('wws'))
async def selet_command(bot,ev:CQEvent):
    try:
        qqid = ev['user_id']
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
                msg = '待开发：查单船总战绩'
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
        else:
            msg = '看不懂指令QAQ'
        if isinstance(msg,str):
            print(msg)
            await bot.send(ev,msg)
        else:
            img_base64= base64.b64encode(msg).decode('utf8')
            await bot.send(ev,str(MessageSegment.image("base64://" + img_base64)))
        return
    except Exception:
        traceback.print_exc()
        await bot.send(ev,'呜呜呜发生了错误，如果过段时间不能恢复请联系麻麻哦~')
        return