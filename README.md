# Telegram Group Management Bot
# Telegram 群组管理机器人

A Telegram bot for group management with moderation commands, welcome messages, and keyword responses.
一个用于群组管理的 Telegram 机器人，具有管理命令、欢迎消息和关键词回复功能。

## Features | 功能

- Basic command handling (/start, /help) | 基本命令处理 (/start, /help)
- Moderation commands (/ban) | 管理命令 (/ban)
- Group statistics (/stats) | 群组统计信息 (/stats)
- Admin command palette with interactive buttons | 带有交互式按钮的管理员命令面板
- Automatic welcome messages for new members | 自动欢迎新成员消息
- Comprehensive keyword-triggered responses | 全面的关键词触发回复
- Customizable auto-replies | 可自定义的自动回复
- Smart context-aware responses | 智能的上下文感知回复
- Complete Chinese language support | 完整的中文语言支持
- Admin-only mode (only admins can use commands) | 仅管理员模式（只有管理员能使用命令）
- Group verification feature ("验群") | 群组验证功能（"验群"）
- Group search and navigation system | 群组搜索和导航系统
- Official channel links and verification | 官方频道链接和验证

## Setup | 设置

1. Create a Telegram bot using BotFather and get your API token
   使用 BotFather 创建一个 Telegram 机器人并获取 API 令牌
2. Set the environment variable:
   设置环境变量：
   ```
   export TELEGRAM_BOT_TOKEN=your_token_here
   ```
3. Install requirements:
   安装依赖：
   ```
   pip install python-telegram-bot flask flask-sqlalchemy psycopg2-binary
   ```
4. Run the bot:
   运行机器人：
   ```
   python main.py
   ```

## 24小时自动化运行 | 24/7 Automated Operation

本项目包含多个自动化脚本，确保机器人在Replit环境中24小时不间断运行：

### 方法一：使用 run_bot.py（推荐）

这是最简单的方法，使用内置的Python自动重启机制：

```bash
# 赋予脚本执行权限
chmod +x run_bot.py

# 启动机器人（会自动重启）
python run_bot.py
```

此脚本会：
- 监控机器人进程状态
- 如果机器人停止运行，自动重启
- 记录详细日志供排查问题
- 随机化重试间隔，防止频繁重启

### 方法二：使用 autorun.py

这是一个更复杂的守护进程脚本，提供更多监控功能：

```bash
# 赋予脚本执行权限
chmod +x autorun.py

# 启动守护进程
python autorun.py
```

此脚本的特点：
- 使用单独的进程监控机器人
- 提供详细的状态报告和日志
- 优雅地处理各种终止信号
- 自动限制最大重启次数，防止无限循环

### 方法三：使用 Shell 脚本

适合喜欢Shell脚本的用户：

```bash
# 赋予脚本执行权限
chmod +x start_replit_bot.sh

# 启动脚本
./start_replit_bot.sh
```

Shell脚本的优点：
- 简单直观，易于理解
- 使用nohup在后台运行机器人
- 自动跟踪机器人运行时间
- 适合与Cron或其他调度系统集成

### 方法四：使用 replit_keep_alive.py（完整监控）

这是最全面的解决方案，专为Replit环境优化：

```bash
# 运行保活脚本
python replit_keep_alive.py
```

此脚本提供：
- 内置Web服务器，防止Replit休眠
- 美观的状态监控页面
- 进程状态监控与自动重启
- 详细的日志记录系统

### 在Replit上自动启动

设置Replit的启动命令为以下任一选项:

```bash
# 在.replit文件中配置运行命令
run = "python run_bot.py"

# 或者使用web界面和自动重启
run = "python replit_keep_alive.py"
```

## Available Commands | 可用命令

- `/start` - Start the bot and get a welcome message | 启动机器人并获取欢迎信息
- `/help` - View help information | 查看帮助信息
- `/ban <username or user ID>` - Ban a specific user from the group (admin only) | 封禁指定用户（仅限管理员）
- `/stats` - Display group statistics | 显示群组统计信息（仅限管理员）
- `/admin` - Opens the admin command palette with intuitive icons for all management functions | 打开带有直观图标的管理员命令面板（仅限管理员）

## Admin Command Palette | 管理员命令面板

The admin command palette provides a visual interface with intuitive icons for all admin functions:
管理员命令面板提供了带有直观图标的可视化界面，包含所有管理功能：

- 📊 **Group Statistics** - View detailed stats about the group | 查看群组的详细统计信息
- 🚫 **Ban User** - Remove users from the group | 将用户从群组中移除
- ⚠️ **Warn User** - Send warnings to users | 向用户发送警告
- 🔇 **Mute User** - Temporarily restrict users from sending messages | 临时限制用户发送消息
- 📝 **Group Rules** - Set and manage group rules | 设置和管理群组规则
- 🔨 **Clean Messages** - Delete multiple messages at once | 批量删除消息

## Customization | 自定义设置

You can customize the bot's behavior by:
您可以通过以下方式自定义机器人的行为：

1. Adding or modifying keyword responses in `bot/responses.py`
   在 `bot/responses.py` 中添加或修改关键词回复
2. Adding custom keyword responses in `config.py` without modifying core code
   在 `config.py` 中添加自定义关键词回复，无需修改核心代码
3. Changing the welcome message format in `bot/handlers.py`
   在 `bot/handlers.py` 中更改欢迎消息格式
4. Adding new commands by creating handlers in `bot/commands.py` and registering them in `bot/__init__.py`
   在 `bot/commands.py` 中创建处理程序并在 `bot/__init__.py` 中注册它们，以添加新命令

## Group Search & Navigation | 群组搜索与导航

The bot provides an advanced group search and navigation system in private chats:
机器人在私聊中提供高级群组搜索和导航系统：

### Beautifully Designed Welcome Message | 精美设计的欢迎消息
- Modern UI with gradient background and profile picture | 带有渐变背景和头像的现代界面
- Well-structured information with visual hierarchy | 具有视觉层次结构的信息布局
- Complete information about official channels | 关于官方频道的完整信息

### Search Methods | 搜索方法

1. **Keyword Search | 关键词搜索**
   - Users can simply type keywords like "卡商", "白资", "代收" in private chat
   - 用户只需在私聊中输入关键词，如"卡商"、"白资"、"代收"
   - The bot searches the database and returns matching groups with join buttons
   - 机器人搜索数据库并返回匹配的群组，带有加入按钮

2. **Group Number Navigation | 群组编号导航**
   - Users can directly access groups by sending group numbers in format: 【123】or [123]
   - 用户可以通过发送格式为【123】或[123]的群组编号直接访问群组
   - The bot provides direct join links for the specified group
   - 机器人为指定的群组提供直接加入链接

### Interactive Elements | 交互式元素

- **Interactive Channel Directory | 交互式频道目录**
  - Complete list of all official channels with direct links
  - 所有官方频道的完整列表及直接链接
  - Single-tap access to any official resource
  - 一键访问任何官方资源

- **Join Buttons | 加入按钮**
  - Each search result includes a direct join button for easy access
  - 每个搜索结果都包含一个直接加入按钮，方便访问
  
- **Menu Navigation | 菜单导航**
  - Return to main menu button for easy navigation
  - 返回主菜单按钮，方便导航
  
- **Official Channel Links | 官方频道链接**
  - Links to official verification channels to avoid scams
  - 官方验证频道链接，避免诈骗
  - Clearly visible anti-fraud guidance
  - 清晰可见的防诈骗指南

### Group Database Configuration | 群组数据库配置

Configure groups in `config.py`:
在 `config.py` 中配置群组：

```python
GROUP_DATABASE = {
    # 按编号索引的群组
    "数字编号": {
        "123": {"name": "卡商交流群", "link": "https://t.me/+abcdefg123456", "description": "卡商交流与服务"},
        "234": {"name": "承兑服务群", "link": "https://t.me/+bcdefgh234567", "description": "专业承兑服务"},
    },
    
    # 按关键词索引的群组
    "关键词": {
        "卡商": ["123"],
        "承兑": ["234"],
    }
}
```

## Auto-reply System | 自动回复系统

The bot includes a comprehensive auto-reply system with the following features:
机器人包含一个全面的自动回复系统，具有以下特点：

### Keyword Response Setup | 关键词回复设置

There are two ways to add keyword responses:
有两种添加关键词回复的方式：

1. Core keywords in `bot/responses.py` - Contains base responses for common phrases
   核心关键词在 `bot/responses.py` 中 - 包含常见短语的基本回复
   
2. Custom keywords in `config.py` - Easy to modify without changing core code
   自定义关键词在 `config.py` 中 - 无需更改核心代码即可轻松修改

### Features | 特点

- Personalized responses that sometimes include the user's name
  有时会包含用户姓名的个性化回复
  
- Context-aware responses that adapt to the message content
  适应消息内容的上下文感知回复
  
- Comprehensive logging of triggered keywords for analysis
  触发关键词的全面日志记录，便于分析
  
- Support for both Chinese and English keywords and responses
  同时支持中文和英文关键词及回复

### Example | 示例

Add custom responses in `config.py`:
在 `config.py` 中添加自定义回复：

```python
ADDITIONAL_KEYWORD_RESPONSES = {
    "群介绍": "这是一个友好的交流群，我们欢迎大家分享知识和经验。",
    "如何提问": "请直接描述你的问题，尽量提供完整的信息。",
    # 可以根据需要添加更多关键词和回复
}
```

## License | 许可证

MIT
