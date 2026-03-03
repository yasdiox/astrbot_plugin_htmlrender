import os
import tempfile
from os import getcwd
from pathlib import Path
from typing import Any, Literal

import aiofiles
import jinja2
from playwright.async_api import async_playwright

from astrbot.api import logger

TEMPLATES_PATH = str(Path(__file__).parent / "templates")

_temp_files: set[str] = set()


async def read_file(path: str) -> str:
    async with aiofiles.open(path, encoding="UTF8") as f:
        return await f.read()


async def read_tpl(path: str) -> str:
    return await read_file(f"{TEMPLATES_PATH}/{path}")


async def html_to_pic(
    html: str,
    wait: int = 0,
    template_path: str = f"file://{getcwd()}",
    type: Literal["jpeg", "png"] = "png",
    quality: int | None = None,
    device_scale_factor: float = 2,
    screenshot_timeout: float | None = 30_000,
    full_page: bool | None = True,
    **kwargs,
 ) -> str:
    """把一段 HTML 渲染成图片。

    该函数会临时启动一个 Chromium 浏览器实例，打开页面并截屏。
    参数设计和原 nonebot 插件保持一致。
    """
    if "file:" not in template_path:
        raise Exception("template_path should be file:///path/to/template")

    suffix = f".{type}"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = tmp.name
    tmp.close()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(device_scale_factor=device_scale_factor, **kwargs)
        page.on("console", lambda msg: logger.debug(f"[Browser Console]: {msg.text}"))
        await page.goto(template_path)
        await page.set_content(html, wait_until="networkidle")
        await page.wait_for_timeout(wait)
        await page.screenshot(
            path=tmp_path,
            full_page=full_page,
            type=type,
            quality=quality,
            timeout=screenshot_timeout,
        )
        await browser.close()

    _temp_files.add(tmp_path)
    return tmp_path


async def template_to_pic(
    template_path: str,
    template_name: str,
    templates: dict[Any, Any],
    filters: dict[str, Any] | None = None,
    pages: dict[str, Any] | None = None,
    wait: int = 0,
    type: Literal["jpeg", "png"] = "png",
    quality: int | None = None,
    device_scale_factor: float = 2,
    screenshot_timeout: float | None = 30_000,
) -> str:
    """使用 jinja2 模板渲染 HTML 并截图。

    - ``template_path``: 模板目录，例如 ``/path/to/your/templates``。
    - ``template_name``: 目录下的模板文件名（如 ``foo.html``）。
    - ``templates``: 传给模板的上下文变量。
    - ``filters``: 可选的自定义过滤器字典。
    - ``pages``: 传给 ``html_to_pic`` 的页面参数，包括 ``viewport``、``base_url`` 等。
    """
    if pages is None:
        pages = {
            "viewport": {"width": 500, "height": 10},
            "base_url": f"file://{getcwd()}",
        }

    template_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path),
        enable_async=True,
    )

    if filters:
        for fname, ffunc in filters.items():
            template_env.filters[fname] = ffunc
            logger.debug(f"Custom filter loaded: {fname}")

    template = template_env.get_template(template_name)

    html = await template.render_async(**templates)
    return await html_to_pic(
        template_path=f"file://{template_path}",
        html=html,
        wait=wait,
        type=type,
        quality=quality,
        device_scale_factor=device_scale_factor,
        screenshot_timeout=screenshot_timeout,
        **pages,
    )


async def cleanup_tempfiles() -> None:
    for p in list(_temp_files):
        try:
            os.remove(p)
        except Exception:
            logger.warning(f"删除临时文件失败：{p}")
        finally:
            _temp_files.discard(p)
