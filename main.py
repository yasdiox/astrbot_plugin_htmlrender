from astrbot.api import logger
from astrbot.api.star import Context, Star, register

# htmlrender utilities
from .htmlrender import cleanup_tempfiles

class HtmlRenderStar(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        logger.info("astrbot_plugin_htmlrender 已加载")

    async def terminate(self):
        """插件卸载/停用时清理由 htmlrender 创建的临时文件。"""
        await cleanup_tempfiles()
        logger.info("astrbot_plugin_htmlrender 已卸载; 临时文件已清理")
