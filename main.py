import logging
import os
import threading
from bot import create_bot
from app import app, bot_status
from datetime import datetime

def start_bot():
    """在单独的线程中启动机器人"""
    # 设置日志
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    
    # 获取机器人令牌
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("未提供令牌。请设置环境变量 TELEGRAM_BOT_TOKEN。")
        return
    
    # 更新状态
    bot_status["started_at"] = datetime.now()
    bot_status["is_running"] = True
    
    # 创建并启动机器人
    logger.info("开始启动好旺公群机器人...")
    bot = create_bot(token)
    bot.run_polling()
    
    # 保持机器人运行
    bot.idle()

def main():
    # 当直接运行此脚本时，将仅启动 Telegram 机器人
    if __name__ == "__main__":
        # 设置日志
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.INFO
        )
        logger = logging.getLogger(__name__)
        logger.info("启动好旺公群机器人（命令行模式）...")
        
        # 获取机器人令牌
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.error("未提供令牌。请设置环境变量 TELEGRAM_BOT_TOKEN。")
            return
        
        # 更新状态
        bot_status["started_at"] = datetime.now()
        bot_status["is_running"] = True
        
        # 创建并启动机器人
        bot = create_bot(token)
        bot.run_polling()
        
        # 保持机器人运行
        bot.idle()
    else:
        # 当作为模块导入时，在单独的线程中启动机器人
        bot_thread = threading.Thread(target=start_bot)
        bot_thread.daemon = True
        bot_thread.start()

# 如果直接运行此脚本，则启动机器人
if __name__ == "__main__":
    main()
