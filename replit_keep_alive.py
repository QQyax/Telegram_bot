#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Replit 保活脚本
用于确保Replit服务器不会休眠，从而保证机器人24小时运行
"""

import logging
import os
import subprocess
import sys
import threading
import time
from datetime import datetime

# 使用内置的http.server模块而不是Flask，减少依赖
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("keep_alive.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("keep_alive")

# 全局变量，用于追踪机器人状态
bot_status = {
    "running": False,
    "start_time": None,
    "uptime": "0分钟",
    "restart_count": 0,
    "last_restart": None,
    "process": None
}

# 定义一个简单的HTTP处理器
class BotStatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # 生成状态页面
        status_page = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>好旺公群机器人状态</title>
            <style>
                body {{
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f7f7f7;
                }}
                .container {{
                    background-color: white;
                    border-radius: 8px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 2px solid #eee;
                    padding-bottom: 10px;
                }}
                .status {{
                    margin-top: 20px;
                    padding: 15px;
                    border-radius: 4px;
                }}
                .status.running {{
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    color: #155724;
                }}
                .status.stopped {{
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    color: #721c24;
                }}
                .info-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin-top: 20px;
                }}
                .info-card {{
                    background-color: #f8f9fa;
                    border-radius: 4px;
                    padding: 15px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                .label {{
                    font-weight: bold;
                    color: #6c757d;
                    margin-bottom: 5px;
                }}
                .value {{
                    font-size: 1.2em;
                }}
                .timestamp {{
                    margin-top: 30px;
                    color: #6c757d;
                    font-size: 0.9em;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>好旺公群机器人状态监控</h1>
                
                <div class="status {'running' if bot_status['running'] else 'stopped'}">
                    <h2>状态: {'运行中' if bot_status['running'] else '已停止'}</h2>
                </div>
                
                <div class="info-grid">
                    <div class="info-card">
                        <div class="label">运行时间</div>
                        <div class="value">{bot_status['uptime']}</div>
                    </div>
                    <div class="info-card">
                        <div class="label">重启次数</div>
                        <div class="value">{bot_status['restart_count']}</div>
                    </div>
                    <div class="info-card">
                        <div class="label">启动时间</div>
                        <div class="value">{bot_status['start_time'] or '未启动'}</div>
                    </div>
                    <div class="info-card">
                        <div class="label">最近一次重启</div>
                        <div class="value">{bot_status['last_restart'] or '无'}</div>
                    </div>
                </div>
                
                <div class="timestamp">
                    页面更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </div>
        </body>
        </html>
        """
        
        # 发送状态页面
        self.wfile.write(status_page.encode('utf-8'))

def format_uptime():
    """格式化运行时间"""
    if not bot_status["start_time"]:
        return "0分钟"
    
    uptime = datetime.now() - bot_status["start_time"]
    total_seconds = int(uptime.total_seconds())
    
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}天")
    if hours > 0 or days > 0:
        parts.append(f"{hours}小时")
    parts.append(f"{minutes}分钟")
    
    return "".join(parts)

def check_bot_process():
    """通过系统命令检查机器人进程是否在运行"""
    try:
        # 使用ps命令查找机器人进程
        output = subprocess.check_output(
            "ps aux | grep 'python main.py' | grep -v grep",
            shell=True,
            text=True
        )
        
        # 如果有输出，说明进程在运行
        return len(output.strip()) > 0
    except:
        # 如果命令失败，假设进程不在运行
        return False

def start_bot():
    """启动机器人"""
    logger.info("启动机器人进程...")
    
    try:
        # 使用subprocess启动机器人
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # 更新状态
        bot_status["process"] = process
        bot_status["running"] = True
        bot_status["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bot_status["uptime"] = format_uptime()
        
        logger.info(f"机器人已启动，PID: {process.pid}")
        return True
    except Exception as e:
        logger.error(f"启动机器人失败: {str(e)}")
        bot_status["running"] = False
        return False

def monitor_bot():
    """监控机器人进程的线程函数"""
    check_interval = 60  # 每60秒检查一次
    logger.info("监控线程已启动")
    
    while True:
        try:
            # 检查机器人进程状态
            is_running = check_bot_process()
            bot_status["running"] = is_running
            
            # 如果机器人不在运行，尝试启动它
            if not is_running:
                logger.warning("检测到机器人不在运行，尝试启动...")
                bot_status["restart_count"] += 1
                bot_status["last_restart"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                success = start_bot()
                
                if success:
                    logger.info("机器人启动成功")
                else:
                    logger.error("机器人启动失败")
            else:
                # 更新运行时间
                if bot_status["start_time"]:
                    bot_status["uptime"] = format_uptime()
            
            # 等待指定的间隔时间
            time.sleep(check_interval)
            
        except Exception as e:
            logger.error(f"监控线程发生错误: {str(e)}")
            time.sleep(check_interval)  # 出错后等待一段时间再继续

def run_web_server():
    """运行Web服务器，用于保持Replit活跃"""
    # 使用简单的多线程HTTP服务器
    class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
        """多线程HTTP服务器"""
        pass
    
    try:
        # 在5000端口启动服务器
        server = ThreadedHTTPServer(('0.0.0.0', 5000), BotStatusHandler)
        logger.info("Web服务器已启动，监听端口：5000")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Web服务器发生错误: {str(e)}")

def main():
    """主函数"""
    logger.info("=== Replit 保活系统启动 ===")
    
    # 启动监控线程
    monitor_thread = threading.Thread(target=monitor_bot, daemon=True)
    monitor_thread.start()
    
    # 启动Web服务器
    run_web_server()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭...")
    except Exception as e:
        logger.error(f"程序发生致命错误: {str(e)}")
        sys.exit(1)