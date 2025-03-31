#!/bin/bash
# 启动好旺公群机器人的Replit脚本
# 此脚本用于在Replit环境中启动并保持机器人24小时运行

echo "=== 好旺公群机器人启动脚本 ==="
echo "开始时间: $(date)"

# 确保日志目录存在
mkdir -p logs

# 启动机器人并重定向日志
echo "启动机器人进程..."
nohup python main.py > logs/bot.log 2>&1 &
BOT_PID=$!
echo "机器人进程已启动，PID: $BOT_PID"

# 记录PID以便后续管理
echo $BOT_PID > bot_pid.txt

# 设置看门狗函数
restart_bot() {
    echo "正在重启机器人..."
    
    # 如果旧进程还在运行，先终止它
    if [ -f bot_pid.txt ]; then
        OLD_PID=$(cat bot_pid.txt)
        if ps -p $OLD_PID > /dev/null; then
            echo "终止旧进程 (PID: $OLD_PID)..."
            kill $OLD_PID
            sleep 5
            # 如果进程仍在运行，强制终止
            if ps -p $OLD_PID > /dev/null; then
                echo "强制终止进程..."
                kill -9 $OLD_PID
            fi
        fi
    fi
    
    # 启动新进程
    nohup python main.py > logs/bot.log 2>&1 &
    NEW_PID=$!
    echo $NEW_PID > bot_pid.txt
    echo "新机器人进程已启动，PID: $NEW_PID"
    return $NEW_PID
}

# 主循环，检查机器人进程状态
echo "开始监控机器人进程..."
while true; do
    # 检查记录的PID
    if [ -f bot_pid.txt ]; then
        BOT_PID=$(cat bot_pid.txt)
        if ! ps -p $BOT_PID > /dev/null; then
            echo "检测到机器人进程 (PID: $BOT_PID) 不在运行状态"
            NEW_PID=$(restart_bot)
            echo "机器人已重启，新PID: $NEW_PID"
        else
            # 进程运行正常，记录运行时间
            if [ -f bot_start_time.txt ]; then
                START_TIME=$(cat bot_start_time.txt)
                CURRENT_TIME=$(date +%s)
                UPTIME=$((CURRENT_TIME - START_TIME))
                HOURS=$((UPTIME / 3600))
                MINUTES=$(( (UPTIME % 3600) / 60 ))
                
                # 每小时记录一次
                if [ $((UPTIME % 3600)) -lt 60 ]; then
                    echo "机器人运行状态: 正常 (已运行 ${HOURS}小时 ${MINUTES}分钟)"
                fi
            else
                # 第一次运行，记录开始时间
                date +%s > bot_start_time.txt
            fi
        fi
    else
        echo "未找到机器人PID文件，启动新的机器人进程..."
        restart_bot
    fi
    
    # 睡眠60秒再检查
    sleep 60
done