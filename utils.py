import datetime
import hashlib
from base64 import b64encode

from apscheduler.triggers.date import DateTrigger
from nonebot import scheduler


async def match_keywords(match_list, Lists):
    for List in Lists:
        for kw in List.keywords:
            for match_kw in match_list:
                if match_kw == kw or match_kw.upper() == kw.upper() or match_kw.lower() == kw.lower():
                    match_list.remove(match_kw)
                    return List.match_keywords, match_list
    return None, match_list


async def find_and_replace_keywords(match_list, Lists):
    for List in Lists:
        for kw in List.keywords:
            for i, match_kw in enumerate(match_list):
                if match_kw.find(kw) + 1:
                    match_list[i] = str(match_kw).replace(kw, '')
                    if match_list[i] == '':
                        match_list.remove('')
                    return List.match_keywords, match_list
    return None, match_list


def bytes2b64(im: bytes) -> str:
    return f'base64://{b64encode(im).decode()}'


def cancel_call_later(job_id):
    scheduler.remove_job(job_id, 'default')


def call_later(delay, func, job_id):
    if scheduler.get_job(job_id, 'default'):
        cancel_call_later(job_id)
    now = datetime.datetime.now()
    notify_time = now + datetime.timedelta(seconds=delay)
    return scheduler.add_job(
        func,
        trigger=DateTrigger(notify_time),
        id=job_id,
        misfire_grace_time=60,
        coalesce=True,
        jobstore='default',
        max_instances=1,
    )


async def byte2md5(bytes):
    res = hashlib.md5(bytes).hexdigest()
    return res
