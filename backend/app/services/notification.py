"""
Telegram 推送通知服务 - 事件驱动，仅推送紧急新闻
"""
import httpx
import logging
from datetime import datetime, timedelta
from typing import List

from app.config import settings

logger = logging.getLogger(__name__)


# 紧急关键词（命中任意一个即推送）
URGENT_KEYWORDS = [
    "暴跌", "跌停", "熔断", "崩盘", "黑天鹅",
    "监管", "处罚", "立案", "调查", "退市", "ST",
    "降息", "加息", "降准", "IPO", "注册制",
    "重大利空", "业绩暴雷", "财务造假",
    "减持", "清仓", "质押", "爆仓",
    "封杀", "制裁", "禁令",
]

# 紧急事件类型
URGENT_EVENT_TYPES = ["policy", "monetary_policy"]


class TelegramNotifier:
    """Telegram Bot 推送 - 仅紧急新闻"""

    @staticmethod
    async def send_telegram_message(text: str, parse_mode: str = "HTML") -> bool:
        """发送 Telegram 消息"""
        token = settings.tg_bot_token
        chat_id = settings.tg_chat_id
        if not token or not chat_id:
            logger.warning("TG_BOT_TOKEN 或 TG_CHAT_ID 未配置，跳过推送")
            return False

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                logger.info("TG 推送成功")
                return True
        except Exception as e:
            logger.error(f"TG 推送失败: {e}")
            return False

    @staticmethod
    def _is_urgent(title: str, content: str, event_type: str = None) -> bool:
        """判断新闻是否紧急"""
        text = f"{title} {content or ''}"
        # 政策/货币政策事件
        if event_type in URGENT_EVENT_TYPES:
            return True
        # 关键词匹配
        for kw in URGENT_KEYWORDS:
            if kw in text:
                return True
        return False

    @staticmethod
    async def check_and_push(new_news_list: list):
        """
        事件驱动：在每次新闻采集后调用，检查新采集的新闻是否紧急，立即推送。
        new_news_list: [{'title': ..., 'content': ..., 'source': ..., 'stock_code': ..., 'event_type': ...}, ...]
        """
        urgent = []
        for item in new_news_list:
            title = item.get("title", "")
            content = item.get("content", "")
            event_type = item.get("event_type")
            if TelegramNotifier._is_urgent(title, content, event_type):
                urgent.append(item)

        if not urgent:
            return False

        lines = ["<b>🚨 紧急新闻</b>\n"]
        for n in urgent[:5]:  # 最多5条，避免刷屏
            stock_tag = f" | 📌 {n.get('stock_code', '')}" if n.get('stock_code') else ""
            source_tag = f" ({n.get('source', '')})"
            lines.append(f"• <b>{n['title']}</b>{source_tag}{stock_tag}")
            if n.get("content"):
                lines.append(f"  {n['content'][:120]}...")

        text = "\n".join(lines)
        await TelegramNotifier.send_telegram_message(text)
        return True

    @staticmethod
    async def push_urgent_news() -> bool:
        """
        兜底：查询最近 10 分钟内是否有紧急新闻未推送（防漏）
        由调度器每 10 分钟调用一次
        """
        from app.database import SessionLocal
        from app.models.news import News
        from sqlalchemy import or_

        token = settings.tg_bot_token
        chat_id = settings.tg_chat_id
        if not token or not chat_id:
            return False

        db = SessionLocal()
        try:
            ten_min_ago = datetime.now() - timedelta(minutes=10)
            news_list = (
                db.query(News)
                .filter(News.created_at >= ten_min_ago)
                .order_by(News.created_at.desc())
                .limit(50)
                .all()
            )

            urgent = []
            for n in news_list:
                if TelegramNotifier._is_urgent(n.title, n.content, getattr(n, "event_type", None)):
                    urgent.append({
                        "title": n.title,
                        "content": n.content,
                        "source": n.source,
                        "stock_code": n.stock_code,
                    })

            if not urgent:
                return False

            lines = ["<b>🚨 紧急新闻</b>\n"]
            for n in urgent[:5]:
                stock_tag = f" | 📌 {n.get('stock_code', '')}" if n.get("stock_code") else ""
                lines.append(f"• <b>{n['title']}</b> ({n['source']}){stock_tag}")

            text = "\n".join(lines)
            await TelegramNotifier.send_telegram_message(text)
            return True
        except Exception as e:
            logger.error(f"紧急新闻推送失败: {e}")
            return False
        finally:
            db.close()
