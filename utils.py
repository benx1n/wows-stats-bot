from os import getcwd
from .browser import get_new_page


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

