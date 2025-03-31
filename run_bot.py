#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Telegram 机器人启动脚本
本脚本用于在Replit环境中启动机器人，并保持其运行
"""

import logging
import os
import subprocess
import sys
import time
import threading
import traceback
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_runner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_token():
    """检查API令牌是否存在"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("未找到 TELEGRAM_BOT_TOKEN 环境变量")
        return False
    return True

def run_bot():
    """运行机器人"""
    logger.info("启动 Telegram 机器人进程...")
    
    try:
        # 直接执行main.py作为子进程
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # 监控进程而不阻塞主线程
        def log_output(proc):
            """记录子进程输出的线程函数"""
            if proc and proc.stdout:
                for line in iter(proc.stdout.readline, ''):
                    line = line.rstrip()
                    if line:
                        logger.info(f"Bot output: {line}")
        
        # 在单独的线程中记录输出
        log_thread = threading.Thread(target=log_output, args=(process,))
        log_thread.daemon = True
        log_thread.start()
        
        # 等待进程结束，获取返回码
        return_code = process.wait()
        logger.warning(f"机器人进程已退出，返回码: {return_code}")
        return False
    except Exception as e:
        logger.error(f"运行机器人时发生错误: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数，包含重试逻辑"""
    logger.info("=== 好旺公群机器人启动器开始运行 ===")
    
    max_retries = 1000  # 设置最大重试次数
    retry_count = 0
    
    while retry_count < max_retries:
        # 检查令牌
        if not check_token():
            logger.error("无法获取 API 令牌，30秒后重试...")
            time.sleep(30)
            continue
        
        # 运行机器人
        success = run_bot()
        
        if not success:
            retry_count += 1
            wait_time = min(30 + retry_count * 5, 300)  # 重试等待时间，最长5分钟
            logger.warning(f"机器人运行失败，这是第 {retry_count} 次失败。将在 {wait_time} 秒后重试...")
            time.sleep(wait_time)
        else:
            # 重置重试计数器
            retry_count = 0
    
    logger.critical(f"达到最大重试次数 ({max_retries})，脚本将退出。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭...")
    except Exception as e:
        logger.error(f"启动器发生严重错误: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 重启自身
        logger.info("将在 60 秒后重启启动器...")
        time.sleep(60)
        os.execv(sys.executable, [sys.executable] + sys.argv)