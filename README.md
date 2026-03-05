<div align="center">
  
# AstrBot HTML渲染器

✨ 基于 Playwright 的 HTML 转图片工具 ✨

</div>

<div align="center">
  
![:MoeCounter](https://count.getloli.com/@astrbot_plugin_htmlrender?name=astrbot_plugin_htmlrender&theme=moebooru&padding=7&offset=0&align=center&scale=1&pixelated=1&darkmode=auto)

</div>

---

## 📌 项目简介

本项目为 **AstrBot** 提供基于 **Playwright + Chromium** 的本地 HTML 转图片能力。

适合作为其他插件的前置依赖。

> [!Important]
> 本项目移植自：
> [https://github.com/kexue-z/nonebot-plugin-htmlrender](https://github.com/kexue-z/nonebot-plugin-htmlrender)
>
> 且仅移植了两个主要功能

### 支持功能

* ✅ Jinja2 模板 → 图片
* ✅ 原始 HTML → 图片

---

至于 AstrBot 明明已经有内置的 `custom_t2i_tmpl` 了，为什么还要特地再做一个。  
AstrBot 自带的 jinja2 转图片是云端操作，字体或者边距之类的会有些微妙的差别。  
本项目提供了基于 Playwright 的本地渲染能力，资源占用可能会较大。  

---

## 🔍 效果演示：

|HTML渲染器 jinja2 转图|AstrBot 自带 jinja2 转图|
|--|--|
|<img width="1700" height="978" alt="插件" src="https://github.com/user-attachments/assets/ce8b8b56-8463-4ae2-a422-af438d253948" />|<img width="1700" height="978" alt="内置" src="https://github.com/user-attachments/assets/2a8adc44-cbdd-4b32-b0f6-30971db244bf" />|


---

## 🧩 安装依赖

```bash
playwright install
```

---

## 🚀 快速使用

---

### 1️⃣ 直接渲染 HTML

```python
from data.plugins.astrbot_plugin_htmlrender.htmlrender import html_to_pic

path = await html_to_pic(
    "<html><body><h1>Hello</h1></body></html>"
)

print(path) # str 临时图片文件路径
```

---

### 2️⃣ 使用 Jinja2 模板

```python
from data.plugins.astrbot_plugin_htmlrender.htmlrender import template_to_pic

path = await template_to_pic(
    template_path=r"C:/path/to/templates",
    template_name="markdown.html",
    templates={
        "md": "# 标题\n内容"
    },
)

print(path) # str 临时图片文件路径
```

参数说明：

| 参数              | 类型     | 说明     |
| --------------- | ------ | ------ |
| `template_path` | `str`  | 模板目录路径 |
| `template_name` | `str`  | 模板文件名  |
| `templates`     | `dict` | 传入模板变量 |

---

### 3️⃣ 手动清理临时文件

```python
from data.plugins.astrbot_plugin_htmlrender.htmlrender import cleanup_tempfiles

await cleanup_tempfiles()
```

> 插件在卸载 / 停用时会自动调用该方法。

---

## 📚 API

---

### `html_to_pic`

```python
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
 ) -> str
```

* 渲染 HTML
* 返回临时文件路径

---

### `template_to_pic`

```python
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
) -> str
```

* 渲染 Jinja2 模板
* 返回临时文件路径

---

### `cleanup_tempfiles`

```python
async def cleanup_tempfiles() -> None
```

* 删除所有已记录的临时文件

---

## 🗂 临时文件机制

* 截图写入系统临时目录
* 内部维护文件记录列表
* 支持手动清理接口

---

## 📄 许可证

本项目基于 MIT 许可证开源。
