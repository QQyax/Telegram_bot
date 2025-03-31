#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
好旺公群机器人自动化运行脚本
--------------------
该脚本用于确保机器人24小时运行不间断。
它会在后台监控机器人进程，如果检测到机器人停止运行，将自动重启。
"""

import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_autorun.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("bot_autorun")

class BotKeeper:
    """机器人守护进程类，负责维持机器人运行状态"""
    
    def __init__(self, bot_script="main.py"):
        """初始化守护进程
        
        Args:
            bot_script: 机器人启动脚本路径
        """
        self.bot_script = bot_script
        self.process = None
        self.start_time = None
        self.restart_count = 0
        self.max_restarts = 1000  # 最大重启次数限制，防止无限循环
        self.check_interval = 60  # 每60秒检查一次机器人状态
        self.running = True
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        
    def handle_signal(self, signum, frame):
        """处理终止信号，优雅地关闭机器人和守护进程"""
        logger.info(f"收到信号 {signum}，正在关闭机器人和守护进程...")
        self.running = False
        if self.process:
            logger.info("正在终止机器人进程...")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)  # 等待进程终止
            except subprocess.TimeoutExpired:
                logger.warning("机器人进程未响应终止信号，强制终止")
                self.process.kill()
        logger.info("守护进程关闭完成")
        sys.exit(0)
    
    def start_bot(self):
        """启动机器人进程"""
        logger.info(f"启动机器人进程 (运行脚本: {self.bot_script})")
        try:
            # 使用 Python 解释器启动机器人
            self.process = subprocess.Popen([sys.executable, self.bot_script],
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT,
                                          universal_newlines=True)
            self.start_time = datetime.now()
            logger.info(f"机器人已启动，PID: {self.process.pid}")
            return True
        except Exception as e:
            logger.error(f"启动机器人失败: {str(e)}")
            return False
    
    def check_bot_status(self):
        """检查机器人进程状态"""
        if self.process is None:
            return False
        
        return_code = self.process.poll()
        
        # 如果 return_code 是 None，说明进程仍在运行
        if return_code is None:
            # 读取输出日志但不阻塞
            output = ""
            try:
                # 非阻塞地读取输出
                if self.process.stdout:  # 确保stdout不是None
                    for _ in range(100):  # 限制读取次数，避免无限循环
                        line = self.process.stdout.readline()
                        if not line:
                            break
                        output += line
            except:
                pass
            
            if output:
                # 只记录重要的输出信息
                important_lines = [line for line in output.split('\n') if 'ERROR' in line or 'WARNING' in line]
                if important_lines:
                    logger.info("机器人日志输出:\n" + "\n".join(important_lines))
            
            # 计算运行时间
            if self.start_time:  # 确保start_time不是None
                uptime = datetime.now() - self.start_time
                if uptime.total_seconds() % 3600 < self.check_interval:  # 每小时记录一次
                    hours, remainder = divmod(uptime.total_seconds(), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    logger.info(f"机器人运行状态: 正常 (已运行 {int(hours)}小时 {int(minutes)}分钟)")
            
            return True
        else:
            # 进程已终止
            stdout, _ = self.process.communicate()
            if stdout:
                logger.warning(f"机器人进程已终止 (返回码: {return_code})，输出:\n{stdout}")
            else:
                logger.warning(f"机器人进程已终止 (返回码: {return_code})，无输出")
            return False
    
    def restart_bot(self):
        """重启机器人进程"""
        self.restart_count += 1
        logger.warning(f"正在重启机器人 (第 {self.restart_count} 次重启)")
        
        # 如果旧进程还在，尝试终止它
        if self.process:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            except:
                pass
        
        # 启动新进程
        success = self.start_bot()
        if success:
            logger.info("机器人重启成功")
            # 记录重启时间并重置计数器
            self.start_time = datetime.now()
            return True
        else:
            logger.error("机器人重启失败")
            return False
    
    def run(self):
        """主循环，持续监控机器人状态"""
        logger.info("守护进程已启动，开始监控机器人")
        
        # 首次启动机器人
        if not self.start_bot():
            logger.error("初始启动失败，退出守护进程")
            return
        
        # 主监控循环
        while self.running and self.restart_count < self.max_restarts:
            try:
                # 检查机器人状态
                if not self.check_bot_status():
                    # 如果机器人不在运行，尝试重启
                    logger.warning("检测到机器人不在运行状态")
                    if not self.restart_bot():
                        # 如果重启失败，等待一段时间后再试
                        logger.error("重启失败，将在60秒后再次尝试")
                        time.sleep(60)
                
                # 等待指定的检查间隔
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"守护进程遇到错误: {str(e)}")
                time.sleep(60)  # 出错后等待一段时间再继续
        
        if self.restart_count >= self.max_restarts:
            logger.critical(f"重启次数达到上限 ({self.max_restarts})，守护进程退出")
        
        logger.info("守护进程正常退出")

if __name__ == "__main__":
    logger.info("=== 好旺公群机器人自动化运行脚本启动 ===")
    keeper = BotKeeper()
    keeper.run()