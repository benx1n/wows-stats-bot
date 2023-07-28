import asyncio
import re
import sys
import traceback
from collections import defaultdict, namedtuple

import hoshino
from hikari_core import callback_hikari, init_hikari, set_hikari_config
from hikari_core.game.help import check_version
from hikari_core.model import Hikari_Model
from hikari_core.moudle.wws_real_game import get_diff_ship
from hoshino import Service, get_bot, priv
from hoshino.typing import CQEvent, MessageSegment
from hoshino.util import DailyNumberLimiter, FreqLimiter
from loguru import logger
from nonebot.exceptions import CQHttpError

from .data_source import config, dir_path
from .game.ocr import downlod_OcrResult, get_Random_Ocr_Pic, pic2txt_byOCR, upload_OcrResult
from .game.pupu import get_pupu_msg
from .utils import bytes2b64

_max = 100
EXCEED_NOTICE = f'您今天已经冲过{_max}次了，请明早5点后再来！'
_nlmt = DailyNumberLimiter(_max)
_flmt = FreqLimiter(3)
WWS_help = """请发送wws help查看帮助"""
sv_help = WWS_help.strip()
sv = Service('wows-stats-bot', manage_priv=priv.ADMIN, enable_on_default=True, help_=sv_help)
set_hikari_config(
    use_broswer=config['browser'],
    http2=config['http2'],
    proxy=config['proxy'],
    token=config['token'],
    game_path=str(dir_path / 'game'),
)

SlectState = namedtuple('SlectState', ['state', 'SlectIndex', 'SelectList'])
SecletProcess = defaultdict(lambda: SlectState(False, None, None))


@sv.on_prefix(('wws'))
async def main(bot, ev: CQEvent):
    try:
        qqid = ev['user_id']
        group_id = None
        if ev['message_type'] == 'group':
            group_id = ev['group_id']
        if not _nlmt.check(qqid):
            await bot.send(ev, EXCEED_NOTICE, at_sender=True)
            return
        if not _flmt.check(qqid):
            await bot.send(ev, '您冲得太快了，请稍候再冲', at_sender=True)
            return
        _flmt.start_cd(qqid)
        _nlmt.increase(qqid)
        hikari = await init_hikari(platform='QQ', PlatformId=str(ev['user_id']), command_text=str(ev.message), GroupId=group_id)
        if hikari.Status == 'success':
            if isinstance(hikari.Output.Data, bytes):
                await bot.send(ev, str(MessageSegment.image(bytes2b64(hikari.Output.Data))))
            elif isinstance(hikari.Output.Data, str):
                await bot.send(ev, str(hikari.Output.Data))
        elif hikari.Status == 'wait':
            await bot.send(ev, str(MessageSegment.image(bytes2b64(hikari.Output.Data))))
            hikari = await wait_to_select(hikari)
            if hikari.Status == 'error':
                await bot.send(ev, str(hikari.Output.Data))
                return
            hikari = await callback_hikari(hikari)
            if isinstance(hikari.Output.Data, bytes):
                await bot.send(ev, str(MessageSegment.image(bytes2b64(hikari.Output.Data))))
            elif isinstance(hikari.Output.Data, str):
                await bot.send(ev, str(hikari.Output.Data))
        else:
            await bot.send(ev, str(hikari.Output.Data))
    except CQHttpError:
        logger.error(traceback.format_exc())
        try:
            await bot.send(ev, '发不出图片，可能被风控了QAQ')
        except Exception:
            pass
        return
    except Exception:
        logger.error(traceback.format_exc())
        await bot.send(ev, '呜呜呜发生了错误，可能是网络问题，如果过段时间不能恢复请联系麻麻哦~')
        return


@sv.on_message()
async def change_select_state(bot, ev):
    try:
        msg = ev['raw_message']
        qqid = str(ev['user_id'])
        if SecletProcess[qqid].state and str(msg).isdigit():
            if int(msg) <= len(SecletProcess[qqid].SelectList):
                SecletProcess[qqid] = SecletProcess[qqid]._replace(state=False)
                SecletProcess[qqid] = SecletProcess[qqid]._replace(SlectIndex=int(msg))
            else:
                await bot.send(ev, '请选择列表中的序号哦~')
        return
    except Exception:
        logger.error(traceback.format_exc())
        return


async def wait_to_select(hikari):
    SecletProcess[hikari.UserInfo.PlatformId] = SlectState(True, None, hikari.Input.Select_Data)
    a = 0
    while a < 40 and not SecletProcess[hikari.UserInfo.PlatformId].SlectIndex:
        a += 1
        await asyncio.sleep(0.5)
    if SecletProcess[hikari.UserInfo.PlatformId].SlectIndex:
        hikari.Input.Select_Index = SecletProcess[hikari.UserInfo.PlatformId].SlectIndex
        SecletProcess[hikari.UserInfo.PlatformId] = SlectState(False, None, None)
        return hikari
    else:
        SecletProcess[hikari.UserInfo.PlatformId] = SlectState(False, None, None)
        return hikari.error('已超时退出')


@sv.scheduled_job('cron', hour='12')
async def job1():
    bot = get_bot()
    hikari = Hikari_Model()
    hikari = await check_version(hikari)
    superid = hoshino.config.SUPERUSERS[0]
    await bot.send_private_msg(user_id=superid, message=hikari.Output.Data)


@sv.scheduled_job('interval', minutes=10)
async def job2():
    await downlod_OcrResult()


@sv.scheduled_job('interval', minutes=1)
async def job3():
    bot = get_bot()
    hikari = Hikari_Model()
    hikari = await get_diff_ship(hikari)
    if hikari.Status == 'success':
        for _each in hikari.Output.Data:
            await bot.send_group_msg(group_id=_each['group_id'], message=_each['msg'])


logger.add(
    str(dir_path / 'logs/error.log'),
    rotation='00:00',
    retention='1 week',
    diagnose=False,
    level='ERROR',
    encoding='utf-8',
)
logger.add(
    str(dir_path / 'logs/info.log'),
    rotation='00:00',
    retention='1 week',
    diagnose=False,
    level='INFO',
    encoding='utf-8',
)
logger.add(
    str(dir_path / 'logs/warning.log'),
    rotation='00:00',
    retention='1 week',
    diagnose=False,
    level='WARNING',
    encoding='utf-8',
)


@sv.on_fullmatch('噗噗')
async def send_pupu_msg(bot, ev: CQEvent):
    try:
        if config['pupu']:
            msg = await get_pupu_msg()
            await bot.send(ev, msg)
    except CQHttpError:
        logger.error(traceback.format_exc())
        try:
            await bot.send(ev, '噗噗寄了>_<可能被风控了QAQ')
        except Exception:
            pass
        return
    except Exception:
        logger.error(traceback.format_exc())
        await bot.send(ev, '呜呜呜发生了错误，可能是网络问题，如果过段时间不能恢复请联系麻麻哦~')
        return


@sv.on_fullmatch('wws 随机表情包')
async def send_random_ocr_image(bot, ev: CQEvent):
    try:
        img = await get_Random_Ocr_Pic()
        if isinstance(img, bytes):
            await bot.send(ev, str(MessageSegment.image(bytes2b64(img))))
        elif isinstance(img, str):
            await bot.send(ev, str(img))
    except Exception:
        logger.error(traceback.format_exc())
        await bot.send(ev, '呜呜呜发生了错误，可能是网络问题，如果过段时间不能恢复请联系麻麻哦~')
        return


@sv.on_message()
async def OCR_listen(bot, ev: CQEvent):
    try:
        if not config['ocr_on']:
            return
        if not (str(ev.message).find('[CQ:image') + 1):  # 判断收到的信息是否为图片，不是就退出
            return
        for seg in ev.message:
            if seg.type == 'image':
                tencent_url = seg.data['url']
                filename = str(seg.data['file']).replace('.image', '')
        ocr_text = await pic2txt_byOCR(tencent_url, filename)
        if ocr_text:
            match = re.search(r'^(/?)wws(.*?)$', ocr_text)
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
                searchtag = re.sub(r'^(/?)wws', '', ocr_text)  # 删除wws和/wws
                hikari = await init_hikari(platform='QQ', PlatformId=str(ev['user_id']), command_text=str(searchtag))
                if hikari.Status == 'success':
                    if isinstance(hikari.Output.Data, bytes):
                        await bot.send(ev, str(MessageSegment.image(bytes2b64(hikari.Output.Data))))
                    elif isinstance(hikari.Output.Data, str):
                        await bot.send(ev, str(hikari.Output.Data))
                elif hikari.Status == 'wait':
                    await bot.send(ev, str(MessageSegment.image(bytes2b64(hikari.Output.Data))))
                    hikari = await wait_to_select(hikari)
                    if hikari.Status == 'error':
                        await bot.send(ev, str(hikari.Output.Data))
                        return
                    hikari = await callback_hikari(hikari)
                    if isinstance(hikari.Output.Data, bytes):
                        await bot.send(ev, str(MessageSegment.image(bytes2b64(hikari.Output.Data))))
                    elif isinstance(hikari.Output.Data, str):
                        await bot.send(ev, str(hikari.Output.Data))
                else:
                    await bot.send(ev, str(hikari.Output.Data))
                await upload_OcrResult(ocr_text, filename)
            else:
                return
    except CQHttpError:
        logger.error(traceback.format_exc())
        try:
            await bot.send(ev, '发不出图片，可能被风控了QAQ')
        except Exception:
            pass
    except Exception:
        logger.error(traceback.format_exc())
        return
