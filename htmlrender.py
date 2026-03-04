import asyncio
import os
import tempfile
import time
from os import getcwd
from pathlib import Path
from typing import Any, Literal

import aiofiles
import jinja2
from playwright.async_api import async_playwright

from astrbot.api import logger

TEMPLATES_PATH = str(Path(__file__).parent / "templates")

# 记录此模块创建的临时文件
_temp_files: set[str] = set()
# 可选映射，记录创建时间以便基于年龄的清理
_temp_mtime: dict[str, float] = {}
# 锁用于保护对 _temp_files/_temp_mtime 的并发访问
_temp_lock = asyncio.Lock()


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

    # 立即记录生成的文件，以避免后续异常导致泄漏
    async with _temp_lock:
        _temp_files.add(tmp_path)
        _temp_mtime[tmp_path] = time.time()

    try:
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
    except Exception:
        # 如果出错，尝试立即清理该临时文件
        try:
            os.remove(tmp_path)
        except Exception as e:
            logger.warning(f"在错误后删除临时文件失败：{tmp_path} ({e})")
        async with _temp_lock:
            _temp_files.discard(tmp_path)
            _temp_mtime.pop(tmp_path, None)
        raise

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


async def cleanup_tempfiles(age_seconds: float | None = None) -> None:
    """删除所有已跟踪的临时文件。

    如果 ``age_seconds`` 提供，将只删除至少存在该秒数的文件。
    这对于避免误删仍可能被使用的最新文件有帮助。
    """
    now = time.time()
    async with _temp_lock:
        paths = list(_temp_files)

    for p in paths:
        if age_seconds is not None:
            created = _temp_mtime.get(p, now)
            if now - created < age_seconds:
                # 跳过较新文件
                continue
        try:
            os.remove(p)
        except FileNotFoundError:
            # 已经不存在，无需处理
            logger.debug(f"清理时未找到临时文件：{p}")
        except Exception as e:
            logger.warning(f"删除临时文件失败：{p} ({e})")
        finally:
            async with _temp_lock:
                _temp_files.discard(p)
                _temp_mtime.pop(p, None)
