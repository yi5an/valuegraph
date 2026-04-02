"""
Telegram 推送通知服务
"""
import httpx
import logging
from datetime import datetime, timedelta
from typing import List

from app.config import settings

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Telegram Bot 推送"""

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
    async def push_important_news():
        """
        查询最近 1 小时负面新闻（关联有财务数据的持仓股），推送到 TG
        """
        from app.database import SessionLocal
        from app.models.news import News
        from app.models.financial import Financial
        from sqlalchemy import distinct

        token = settings.tg_bot_token
        chat_id = settings.tg_chat_id
        if not token or not chat_id:
            return

        db = SessionLocal()
        try:
            # 获取有财务数据的股票代码集合
            tracked_codes = {
                code for (code,) in
                db.query(distinct(Financial.stock_code)).all()
            }
            if not tracked_codes:
                logger.info("无持仓股，跳过推送")
                return

            # 查询最近 1 小时、负面情感、关联持仓股的新闻
            one_hour_ago = datetime.now() - timedelta(hours=1)
            news_list = (
                db.query(News)
                .filter(
                    News.sentiment == "负面",
                    News.stock_code.isnot(None),
                    News.stock_code.in_(tracked_codes),
                    News.created_at >= one_hour_ago,
                )
                .order_by(News.created_at.desc())
                .limit(10)
                .all()
            )

            if not news_list:
                return

            lines = ["<b>⚠️ 重要负面新闻提醒</b>\n"]
            for n in news_list:
                lines.append(
                    f"• <b>{n.title}</b>\n"
                    f"  摘要: {n.content[:100] if n.content else '无'}...\n"
                    f"  股票: {n.stock_code} | 来源: {n.source}\n"
                )

            text = "\n".join(lines)
            await TelegramNotifier.send_telegram_message(text)
        except Exception as e:
            logger.error(f"推送重要新闻失败: {e}")
        finally:
            db.close()
