from os import getcwd
from .browser import get_new_page
import datetime
from nonebot import scheduler
from apscheduler.triggers.date import DateTrigger
import jinja2
import aiofiles
from pathlib import Path

TEMPLATES_PATH = str(Path(__file__).parent / "templates")

env = jinja2.Environment(
    extensions=["jinja2.ext.loopcontrols"],
    loader=jinja2.FileSystemLoader(TEMPLATES_PATH),
    enable_async=True,
)

async def html_to_pic(
    html: str, wait: int = 0, template_path: str = f"file://{getcwd()}", **kwargs
) -> bytes:
    if "file:" not in template_path:
        raise "template_path 应该为 file:///path/to/template"
    async with get_new_page(**kwargs) as page:
        await page.goto(template_path)
        await page.set_content(html, wait_until="networkidle")
        await page.wait_for_timeout(wait)
        img_raw = await page.screenshot(full_page=True)
    return img_raw

async def text_to_pic(text: str, css_path: str = "", width: int = 500) -> bytes:
    """多行文本转图片
    Args:
        text (str): 纯文本, 可多行
        css_path (str, optional): css文件
        width (int, optional): 图片宽度，默认为 500
    Returns:
        bytes: 图片, 可直接发送
    """
    template = env.get_template("text.html")

    return await html_to_pic(
        template_path=f"file://{css_path if css_path else TEMPLATES_PATH}",
        html=await template.render_async(
            text=text,
            css=await read_file(css_path) if css_path else await read_tpl("text.css"),
        ),
        viewport={"width": width, "height": 10},
    )


async def match_keywords(match_list,Lists):
    for List in Lists :                        
        for kw in List.keywords:
            for match_kw in match_list:
                if match_kw == kw or match_kw.upper() == kw.upper() or match_kw.lower() == kw.lower():
                    match_list.remove(match_kw)
                    return List.match_keywords,match_list
    return None,match_list

async def find_and_replace_keywords(match_list,Lists):
    for List in Lists :                        
        for kw in List.keywords:
            for i,match_kw in enumerate(match_list):
                if (match_kw.find(kw)+1):
                    match_list[i] = str(match_kw).replace(kw,"")
                    if match_list[i] == '':
                        match_list.remove('')
                    return List.match_keywords,match_list
    return None,match_list


def cancel_call_later(job_id):
    scheduler.remove_job(job_id, "default")


def call_later(delay, func, job_id):
    if scheduler.get_job(job_id, "default"):
        cancel_call_later(job_id)
    now = datetime.datetime.now()
    notify_time = now + datetime.timedelta(seconds=delay)
    return scheduler.add_job(
        func,
        trigger=DateTrigger(notify_time),
        id=job_id,
        misfire_grace_time=60,
        coalesce=True,
        jobstore="default",
        max_instances=1,
    )

async def read_file(path: str) -> str:
    async with aiofiles.open(path, mode="r") as f:
        return await f.read()


async def read_tpl(path: str) -> str:
    return await read_file(f"{TEMPLATES_PATH}/{path}")
