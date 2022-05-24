from os import getcwd
from .browser import get_new_page
import re

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

async def match_keywords(match_list,Lists):
    for List in Lists :                        #第一次匹配
        for kw in List.keywords:
            for match_kw in match_list:
                if match_kw == kw or match_kw.upper() == kw.upper() or match_kw.lower() == kw.lower():
                    match_list.remove(match_kw)
                    return List.match_keywords,match_list
    return None,match_list

async def find_and_replace_keywords(match_list,Lists):
    for List in Lists :                        #第一次匹配
        for kw in List.keywords:
            for i,match_kw in enumerate(match_list):
                if (match_kw.find(kw)+1):
                    match_list[i] = str(match_kw).replace(kw,"")
                    if match_list[i] == '':
                        match_list.remove('')
                    print(match_list)
                    return List.match_keywords,match_list
    return None,match_list