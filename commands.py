import logging
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CallbackQueryHandler, ConversationHandler
from telegram.error import TelegramError
from bot.helpers import is_user_admin
from app import db
from models import PhoneVerification
from utils.verification import send_verification_code, verify_code

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    
    if chat_type == "private":
        # 检查用户是否已验证手机
        existing_verification = PhoneVerification.query.filter_by(user_id=user_id).first()
        is_verified = existing_verification and existing_verification.is_verified
        
        welcome_text = (
            "👋 *欢迎使用好旺公群管理机器人！* 👋\n\n"
            "这是一款功能强大的群组管理工具，可以帮助您搜索公群、验证群组真实性，并提供丰富的群管理功能。\n\n"
            "您可以直接发送群组编号或关键词来搜索相关群组。\n"
            f"手机验证状态: {'✅ 已验证' if is_verified else '❌ 未验证'}\n\n"
        )
        
        if not is_verified:
            welcome_text += (
                "🔐 *需要验证* 🔐\n"
                "为了使用完整功能并保障您的账号安全，请使用 /verify 命令完成手机号验证。\n\n"
            )
        
        welcome_text += "使用 /help 查看所有可用命令。"
        
        # 创建按钮
        keyboard = []
        
        # 添加验证按钮（如果未验证）
        if not is_verified:
            keyboard.append([InlineKeyboardButton("📱 立即验证手机号", callback_data="verify_phone")])
        
        # 添加其他常用按钮
        keyboard.append([InlineKeyboardButton("🔍 搜索群组", callback_data="search_group")])
        keyboard.append([InlineKeyboardButton("ℹ️ 查看频道", callback_data="view_channels")])
        keyboard.append([InlineKeyboardButton("❓ 帮助信息", callback_data="help_info")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        # 在群组中的简短回复
        await update.message.reply_text(
            '欢迎使用好旺公群管理机器人！你可以使用 /help 查看可用命令。\n'
            '群管理员可使用 /admin 命令访问管理面板。'
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
可用命令：
/start - 启动机器人并获取欢迎信息
/help - 查看帮助信息
/verify - 通过手机号验证您的身份
/ban <用户名或用户ID> - 封禁指定用户（仅限管理员）
/mute <用户名> [时长] - 禁言用户一段时间（例如：/mute @用户名 30m）（仅限管理员）
/unmute <用户名> - 解除用户的禁言（仅限管理员）
/stats - 显示群组统计信息（仅限管理员）
/admin - 打开管理员命令面板，包含所有管理功能（仅限管理员）

时长单位：m(分钟)、h(小时)、d(天)
例如：30m, 2h, 1d

注意：本机器人只响应群组管理员的命令和关键词。
但任何用户都可以通过"验群"关键词验证群组真实性。
某些功能可能需要先完成手机验证，请使用 /verify 命令进行验证。
"""
    await update.message.reply_text(help_text)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send group statistics when the command /stats is issued."""
    chat = update.effective_chat
    user_id = update.effective_user.id
    
    if chat.type == "private":
        await update.message.reply_text("此命令只能在群组中使用。")
        return
    
    # 检查用户是否是管理员
    is_admin = await is_user_admin(context.bot, chat.id, user_id)
    
    if not is_admin:
        await update.message.reply_text("抱歉，只有群组管理员可以使用此命令。")
        logger.info(f"非管理员尝试使用 /stats 命令: {update.effective_user.username if update.effective_user.username else user_id}")
        return
    
    try:
        # Get chat info
        chat_info = await context.bot.get_chat(chat.id)
        member_count = await context.bot.get_chat_member_count(chat.id)
        
        # Get current date and time
        now = datetime.now()
        date_str = now.strftime("%Y年%m月%d日")
        time_str = now.strftime("%H:%M:%S")
        
        # Format statistics message
        stats_message = f"""
📊 *群组统计信息* 📊

*群组名称:* {chat_info.title}
*群组成员:* {member_count} 人
*群组类型:* {'超级群组' if chat.type == 'supergroup' else '普通群组'}
*群组ID:* `{chat.id}`

*生成时间:* {date_str} {time_str}
"""
        
        await update.message.reply_markdown(stats_message)
        logger.info(f"Stats sent for chat: {chat.title} ({chat.id})")
        
    except Exception as e:
        await update.message.reply_text(f"获取统计信息失败：{str(e)}")
        logger.error(f"Stats error: {e}")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """显示管理员命令面板，包含有直观图标的交互式按钮。"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # 检查是否在群组中使用命令
    if update.effective_chat.type == "private":
        await update.message.reply_text("此命令只能在群组中使用。")
        return
    
    # 检查用户是否是管理员
    is_admin = await is_user_admin(context.bot, chat_id, user_id)
    
    if not is_admin:
        await update.message.reply_text("抱歉，只有群组管理员可以使用此命令。")
        logger.info(f"非管理员尝试使用 /admin 命令: {update.effective_user.username if update.effective_user.username else user_id}")
        return
    
    # 创建带有图标的管理员命令面板按钮
    keyboard = [
        [
            InlineKeyboardButton("📊 群组统计", callback_data="admin_stats"),
            InlineKeyboardButton("🚫 封禁用户", callback_data="admin_ban")
        ],
        [
            InlineKeyboardButton("⚠️ 警告用户", callback_data="admin_warn"),
            InlineKeyboardButton("🔇 禁言用户", callback_data="admin_mute")
        ],
        [
            InlineKeyboardButton("📝 群组规则", callback_data="admin_rules"),
            InlineKeyboardButton("🔨 清理消息", callback_data="admin_clean")
        ],
        [
            InlineKeyboardButton("❓ 管理帮助", callback_data="admin_help")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # 发送带有按钮的面板消息
    await update.message.reply_text(
        "📋 *管理员命令面板* 📋\n\n请选择要执行的操作：",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    logger.info(f"管理员面板已显示给用户: {update.effective_user.username if update.effective_user.username else user_id}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理管理员命令面板按钮的回调。"""
    query = update.callback_query
    await query.answer()  # 回应回调查询
    
    # 提取回调数据
    callback_data = query.data
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # 检查用户是否是管理员 (重新检查，以防权限已经改变)
    is_admin = await is_user_admin(context.bot, chat_id, user_id)
    if not is_admin:
        await query.edit_message_text("抱歉，您不再是群组管理员，无法使用此功能。")
        return
    
    # 基于回调数据处理不同功能
    if callback_data == "admin_stats":
        # 显示群组统计
        try:
            chat_info = await context.bot.get_chat(chat_id)
            member_count = await context.bot.get_chat_member_count(chat_id)
            
            # 获取当前日期和时间
            now = datetime.now()
            date_str = now.strftime("%Y年%m月%d日")
            time_str = now.strftime("%H:%M:%S")
            
            # 格式化统计信息消息
            stats_message = f"""
📊 *群组统计信息* 📊

*群组名称:* {chat_info.title}
*群组成员:* {member_count} 人
*群组类型:* {'超级群组' if update.effective_chat.type == 'supergroup' else '普通群组'}
*群组ID:* `{chat_id}`

*生成时间:* {date_str} {time_str}
"""
            # 更新原始消息
            await query.edit_message_text(
                stats_message,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回", callback_data="admin_back")]])
            )
            
            logger.info(f"管理员 {update.effective_user.username} 通过面板查看了群组统计")
            
        except Exception as e:
            await query.edit_message_text(
                f"获取统计信息失败：{str(e)}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回", callback_data="admin_back")]])
            )
            logger.error(f"Stats error from panel: {e}")
    
    elif callback_data == "admin_ban":
        # 显示封禁用户表单
        await query.edit_message_text(
            "🚫 *封禁用户*\n\n请回复此消息，指定要封禁的用户名或用户ID。\n格式: `/ban @用户名` 或 `/ban 用户ID`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回", callback_data="admin_back")]])
        )
    
    elif callback_data == "admin_warn":
        # 显示警告用户功能说明
        await query.edit_message_text(
            "⚠️ *警告用户*\n\n此功能正在开发中，即将推出。\n您将能够向用户发送正式警告，并跟踪警告次数。",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回", callback_data="admin_back")]])
        )
    
    elif callback_data == "admin_mute":
        # 显示禁言用户选项
        keyboard = [
            [
                InlineKeyboardButton("🔇 30分钟", callback_data="mute_30m"),
                InlineKeyboardButton("🔇 1小时", callback_data="mute_1h")
            ],
            [
                InlineKeyboardButton("🔇 6小时", callback_data="mute_6h"),
                InlineKeyboardButton("🔇 1天", callback_data="mute_1d")
            ],
            [
                InlineKeyboardButton("🔇 自定义时长", callback_data="mute_custom"),
                InlineKeyboardButton("🔊 解除禁言", callback_data="unmute_user")
            ],
            [
                InlineKeyboardButton("🔙 返回", callback_data="admin_back")
            ]
        ]
        
        await query.edit_message_text(
            "🔇 *禁言用户*\n\n请选择禁言时长，然后回复要禁言的用户消息。\n或者可以使用命令： `/mute @用户名 时长`\n例如：`/mute @用户名 2h`\n\n时长单位：m(分钟)、h(小时)、d(天)",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif callback_data == "admin_rules":
        # 显示设置规则功能说明
        await query.edit_message_text(
            "📝 *群组规则*\n\n此功能正在开发中，即将推出。\n您将能够设置和管理群组规则，用户可以通过命令查看。",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回", callback_data="admin_back")]])
        )
    
    elif callback_data == "admin_clean":
        # 显示清理消息功能说明
        await query.edit_message_text(
            "🔨 *清理消息*\n\n此功能正在开发中，即将推出。\n您将能够批量删除群组中的消息，帮助维护群组秩序。",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回", callback_data="admin_back")]])
        )
    
    elif callback_data == "admin_help":
        # 显示管理员帮助信息
        help_text = """
❓ *管理员帮助* ❓

本机器人提供以下管理员功能：

• 📊 *群组统计* - 查看群组的详细统计信息
• 🚫 *封禁用户* - 将用户从群组中移除并禁止其重新加入
• ⚠️ *警告用户* - 向用户发出警告，多次警告后可执行其他操作
• 🔇 *禁言用户* - 临时限制用户在群组中发言
• 📝 *群组规则* - 设置和管理群组规则
• 🔨 *清理消息* - 批量删除群组中的消息

使用 `/admin` 命令可随时访问此管理面板。
"""
        await query.edit_message_text(
            help_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回", callback_data="admin_back")]])
        )
    
    elif callback_data.startswith("mute_"):
        # 处理禁言选项
        # 保存群组、时长等信息到上下文中，等待用户回复
        duration_code = callback_data[5:]  # 取出时长代码，如 "30m", "1h" 等
        
        # 默认值，避免可能出现的未定义情况
        duration_text = "1小时"
        duration_cmd = "1h"
        
        if duration_code == "30m":
            duration_text = "30分钟"
            duration_cmd = "30m"
        elif duration_code == "1h":
            duration_text = "1小时"
            duration_cmd = "1h"
        elif duration_code == "6h":
            duration_text = "6小时"
            duration_cmd = "6h"
        elif duration_code == "1d":
            duration_text = "1天"
            duration_cmd = "1d"
        elif duration_code == "custom":
            # 显示自定义时长输入提示
            await query.edit_message_text(
                "🔇 *自定义禁言时长*\n\n请直接使用命令设置禁言：\n`/mute @用户名 时长`\n\n时长格式示例：\n- `5m` (5分钟)\n- `2h` (2小时)\n- `1d` (1天)",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回禁言菜单", callback_data="admin_mute")]])
            )
            return
        
        # 提示用户输入要禁言的用户
        await query.edit_message_text(
            f"🔇 *禁言用户 {duration_text}*\n\n请回复以下命令，并@要禁言的用户：\n`/mute @用户名 {duration_cmd}`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回禁言菜单", callback_data="admin_mute")]])
        )
    
    elif callback_data == "unmute_user":
        # 提示用户输入要解除禁言的用户
        await query.edit_message_text(
            "🔊 *解除禁言*\n\n请回复以下命令，并@要解除禁言的用户：\n`/unmute @用户名`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回禁言菜单", callback_data="admin_mute")]])
        )
    
    # 处理公共按钮回调
    elif callback_data == "verify_phone":
        # 启动手机验证流程
        await query.edit_message_text(
            "请使用 /verify 命令开始手机验证流程。",
            parse_mode="Markdown"
        )
        
    elif callback_data == "search_group":
        # 显示群组搜索说明
        await query.edit_message_text(
            "🔍 *搜索群组* 🔍\n\n"
            "您可以通过以下方式搜索群组：\n\n"
            "1. 直接发送群组编号 (例如: 999, 621)\n"
            "2. 发送关键词 (例如: 金融, 交易, 游戏)\n\n"
            "我们将为您找到最匹配的群组。",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_main")]])
        )
        
    elif callback_data == "view_channels":
        # 显示官方频道列表
        channel_text = (
            "📢 *官方频道* 📢\n\n"
            "以下是我们的官方频道：\n\n"
            "• [@hwgq](https://t.me/hwgq) - 好旺公群主频道\n"
            "• [@gongqunLC](https://t.me/gongqunLC) - 公群联创\n"
            "• [@kefu](https://t.me/kefu) - 客服频道\n"
            "• [@hwtb2](https://t.me/hwtb2) - 好旺通报频道\n\n"
            "请关注以上频道获取最新消息与公告。"
        )
        await query.edit_message_text(
            channel_text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_main")]])
        )
        
    elif callback_data == "help_info":
        # 显示帮助信息
        help_text = """
可用命令：
/start - 启动机器人并获取欢迎信息
/help - 查看帮助信息
/verify - 通过手机号验证您的身份
/ban <用户名或用户ID> - 封禁指定用户（仅限管理员）
/mute <用户名> [时长] - 禁言用户一段时间（例如：/mute @用户名 30m）（仅限管理员）
/unmute <用户名> - 解除用户的禁言（仅限管理员）
/stats - 显示群组统计信息（仅限管理员）
/admin - 打开管理员命令面板，包含所有管理功能（仅限管理员）

时长单位：m(分钟)、h(小时)、d(天)
例如：30m, 2h, 1d

注意：本机器人只响应群组管理员的命令和关键词。
但任何用户都可以通过"验群"关键词验证群组真实性。
某些功能可能需要先完成手机验证，请使用 /verify 命令进行验证。
"""
        await query.edit_message_text(
            help_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_main")]])
        )
    
    elif callback_data == "back_to_main":
        # 返回主菜单（重新构建/start命令的界面）
        user_id = update.effective_user.id
        
        # 检查用户是否已验证手机
        existing_verification = PhoneVerification.query.filter_by(user_id=user_id).first()
        is_verified = existing_verification and existing_verification.is_verified
        
        welcome_text = (
            "👋 *欢迎使用好旺公群管理机器人！* 👋\n\n"
            "这是一款功能强大的群组管理工具，可以帮助您搜索公群、验证群组真实性，并提供丰富的群管理功能。\n\n"
            "您可以直接发送群组编号或关键词来搜索相关群组。\n"
            f"手机验证状态: {'✅ 已验证' if is_verified else '❌ 未验证'}\n\n"
        )
        
        if not is_verified:
            welcome_text += (
                "🔐 *需要验证* 🔐\n"
                "为了使用完整功能并保障您的账号安全，请使用 /verify 命令完成手机号验证。\n\n"
            )
        
        welcome_text += "使用 /help 查看所有可用命令。"
        
        # 创建按钮
        keyboard = []
        
        # 添加验证按钮（如果未验证）
        if not is_verified:
            keyboard.append([InlineKeyboardButton("📱 立即验证手机号", callback_data="verify_phone")])
        
        # 添加其他常用按钮
        keyboard.append([InlineKeyboardButton("🔍 搜索群组", callback_data="search_group")])
        keyboard.append([InlineKeyboardButton("ℹ️ 查看频道", callback_data="view_channels")])
        keyboard.append([InlineKeyboardButton("❓ 帮助信息", callback_data="help_info")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    elif callback_data == "admin_back":
        # 返回主菜单
        keyboard = [
            [
                InlineKeyboardButton("📊 群组统计", callback_data="admin_stats"),
                InlineKeyboardButton("🚫 封禁用户", callback_data="admin_ban")
            ],
            [
                InlineKeyboardButton("⚠️ 警告用户", callback_data="admin_warn"),
                InlineKeyboardButton("🔇 禁言用户", callback_data="admin_mute")
            ],
            [
                InlineKeyboardButton("📝 群组规则", callback_data="admin_rules"),
                InlineKeyboardButton("🔨 清理消息", callback_data="admin_clean")
            ],
            [
                InlineKeyboardButton("❓ 管理帮助", callback_data="admin_help")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📋 *管理员命令面板* 📋\n\n请选择要执行的操作：",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ban a user from the group."""
    # Check if the user has admin privileges
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # 检查是否在群组中使用命令
    if update.effective_chat.type == "private":
        await update.message.reply_text("此命令只能在群组中使用。")
        return
    
    try:
        # 使用统一的 helper 函数检查管理员权限
        is_admin = await is_user_admin(context.bot, chat_id, user_id)
        
        if not is_admin:
            await update.message.reply_text("抱歉，只有群组管理员可以使用此命令。")
            logger.info(f"非管理员尝试使用 /ban 命令: {update.effective_user.username if update.effective_user.username else user_id}")
            return
        
        # Check if a username was provided
        if len(context.args) == 0:
            await update.message.reply_text("请输入要封禁的用户名或用户ID。")
            return
        
        target_user = context.args[0]
        
        # If username starts with @, remove it
        if target_user.startswith('@'):
            target_user = target_user[1:]
        
        # Try to ban the user
        try:
            # If it's a numeric ID
            if target_user.isdigit():
                target_user_id = int(target_user)
                await context.bot.ban_chat_member(chat_id, target_user_id)
                await update.message.reply_text(f"已成功封禁用户ID {target_user_id}。")
                logger.info(f"管理员 {update.effective_user.username if update.effective_user.username else user_id} 封禁了用户ID {target_user_id}")
            else:
                # Try to get user info from username
                # Note: This requires the user to have interacted with the bot
                await update.message.reply_text(f"正在封禁用户 {target_user}...")
                
                # For usernames, we need to find the user ID
                await context.bot.ban_chat_member(chat_id, target_user)
                await update.message.reply_text(f"已成功封禁用户 {target_user}。")
                logger.info(f"管理员 {update.effective_user.username if update.effective_user.username else user_id} 封禁了用户 {target_user}")
        
        except TelegramError as e:
            await update.message.reply_text(f"封禁用户失败：{str(e)}")
            logger.error(f"Ban error: {e}")
    
    except Exception as e:
        await update.message.reply_text(f"发生错误：{str(e)}")
        logger.error(f"General error in ban_user: {e}")

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """禁言用户，限制其在群组中发言。"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # 检查是否在群组中使用命令
    if update.effective_chat.type == "private":
        await update.message.reply_text("此命令只能在群组中使用。")
        return
    
    try:
        # 使用统一的 helper 函数检查管理员权限
        is_admin = await is_user_admin(context.bot, chat_id, user_id)
        
        if not is_admin:
            await update.message.reply_text("抱歉，只有群组管理员可以使用此命令。")
            logger.info(f"非管理员尝试使用 /mute 命令: {update.effective_user.username or user_id}")
            return
        
        # 检查参数
        if len(context.args) < 1:
            await update.message.reply_text("使用方法: /mute @用户名 [时长]\n例如: /mute @用户名 60m\n时长单位: m(分钟)、h(小时)、d(天)")
            return
        
        target_user = context.args[0]
        
        # 解析禁言时长 (默认为1小时)
        mute_duration = 60 * 60  # 默认1小时（秒）
        if len(context.args) >= 2:
            duration_str = context.args[1].lower()
            try:
                # 解析数字部分
                time_value = ""
                time_unit = ""
                for char in duration_str:
                    if char.isdigit():
                        time_value += char
                    else:
                        time_unit += char
                
                time_value = int(time_value) if time_value else 1
                
                # 解析单位
                if time_unit == 'm':
                    mute_duration = time_value * 60  # 分钟
                elif time_unit == 'h':
                    mute_duration = time_value * 60 * 60  # 小时
                elif time_unit == 'd':
                    mute_duration = time_value * 24 * 60 * 60  # 天
                else:
                    mute_duration = time_value * 60  # 默认分钟
            except ValueError:
                await update.message.reply_text("时长格式错误，将使用默认时长(1小时)。\n正确格式如: 30m, 2h, 1d")
                mute_duration = 60 * 60  # 默认1小时
        
        # 如果用户名以@开头，去掉@
        if target_user.startswith('@'):
            target_user = target_user[1:]
        
        # 禁言用户
        try:
            # 如果是数字ID
            if target_user.isdigit():
                target_user_id = int(target_user)
                
                # 创建禁言权限
                permissions = {
                    "can_send_messages": False,
                    "can_send_media_messages": False,
                    "can_send_polls": False,
                    "can_send_other_messages": False,
                    "can_add_web_page_previews": False,
                    "can_change_info": False,
                    "can_invite_users": True,
                    "can_pin_messages": False
                }
                
                until_date = int(datetime.now().timestamp() + mute_duration)
                
                await context.bot.restrict_chat_member(
                    chat_id, 
                    target_user_id,
                    permissions=permissions,
                    until_date=until_date
                )
                
                # 格式化禁言时长显示
                duration_display = ""
                if mute_duration < 60 * 60:
                    duration_display = f"{mute_duration // 60}分钟"
                elif mute_duration < 24 * 60 * 60:
                    duration_display = f"{mute_duration // (60 * 60)}小时"
                else:
                    duration_display = f"{mute_duration // (24 * 60 * 60)}天"
                
                await update.message.reply_text(f"已成功禁言用户ID {target_user_id} {duration_display}。")
                logger.info(f"管理员 {update.effective_user.username or user_id} 禁言了用户ID {target_user_id} {duration_display}")
            else:
                # 查找用户ID
                await update.message.reply_text(f"正在禁言用户 {target_user}...")
                
                # 创建禁言权限
                permissions = {
                    "can_send_messages": False,
                    "can_send_media_messages": False,
                    "can_send_polls": False,
                    "can_send_other_messages": False,
                    "can_add_web_page_previews": False,
                    "can_change_info": False,
                    "can_invite_users": True,
                    "can_pin_messages": False
                }
                
                until_date = int(datetime.now().timestamp() + mute_duration)
                
                await context.bot.restrict_chat_member(
                    chat_id, 
                    target_user,
                    permissions=permissions,
                    until_date=until_date
                )
                
                # 格式化禁言时长显示
                duration_display = ""
                if mute_duration < 60 * 60:
                    duration_display = f"{mute_duration // 60}分钟"
                elif mute_duration < 24 * 60 * 60:
                    duration_display = f"{mute_duration // (60 * 60)}小时"
                else:
                    duration_display = f"{mute_duration // (24 * 60 * 60)}天"
                
                await update.message.reply_text(f"已成功禁言用户 {target_user} {duration_display}。")
                logger.info(f"管理员 {update.effective_user.username or user_id} 禁言了用户 {target_user} {duration_display}")
        
        except TelegramError as e:
            await update.message.reply_text(f"禁言用户失败：{str(e)}")
            logger.error(f"Mute error: {e}")
    
    except Exception as e:
        await update.message.reply_text(f"发生错误：{str(e)}")
        logger.error(f"General error in mute_user: {e}")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """解除用户禁言，恢复其在群组中的发言权限。"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # 检查是否在群组中使用命令
    if update.effective_chat.type == "private":
        await update.message.reply_text("此命令只能在群组中使用。")
        return
    
    try:
        # 使用统一的 helper 函数检查管理员权限
        is_admin = await is_user_admin(context.bot, chat_id, user_id)
        
        if not is_admin:
            await update.message.reply_text("抱歉，只有群组管理员可以使用此命令。")
            logger.info(f"非管理员尝试使用 /unmute 命令: {update.effective_user.username or user_id}")
            return
        
        # 检查参数
        if len(context.args) < 1:
            await update.message.reply_text("使用方法: /unmute @用户名")
            return
        
        target_user = context.args[0]
        
        # 如果用户名以@开头，去掉@
        if target_user.startswith('@'):
            target_user = target_user[1:]
        
        # 解除禁言
        try:
            # 如果是数字ID
            if target_user.isdigit():
                target_user_id = int(target_user)
                
                # 创建恢复权限
                permissions = {
                    "can_send_messages": True,
                    "can_send_media_messages": True,
                    "can_send_polls": True,
                    "can_send_other_messages": True,
                    "can_add_web_page_previews": True,
                    "can_change_info": False,
                    "can_invite_users": True,
                    "can_pin_messages": False
                }
                
                await context.bot.restrict_chat_member(
                    chat_id, 
                    target_user_id,
                    permissions=permissions
                )
                
                await update.message.reply_text(f"已成功解除用户ID {target_user_id} 的禁言。")
                logger.info(f"管理员 {update.effective_user.username or user_id} 解除了用户ID {target_user_id} 的禁言")
            else:
                # 解除用户禁言
                await update.message.reply_text(f"正在解除用户 {target_user} 的禁言...")
                
                # 创建恢复权限
                permissions = {
                    "can_send_messages": True,
                    "can_send_media_messages": True,
                    "can_send_polls": True,
                    "can_send_other_messages": True,
                    "can_add_web_page_previews": True,
                    "can_change_info": False,
                    "can_invite_users": True,
                    "can_pin_messages": False
                }
                
                await context.bot.restrict_chat_member(
                    chat_id, 
                    target_user,
                    permissions=permissions
                )
                
                await update.message.reply_text(f"已成功解除用户 {target_user} 的禁言。")
                logger.info(f"管理员 {update.effective_user.username or user_id} 解除了用户 {target_user} 的禁言")
        
        except TelegramError as e:
            await update.message.reply_text(f"解除禁言失败：{str(e)}")
            logger.error(f"Unmute error: {e}")
    
    except Exception as e:
        await update.message.reply_text(f"发生错误：{str(e)}")
        logger.error(f"General error in unmute_user: {e}")


# 手机号验证状态
PHONE_INPUT, CODE_INPUT = range(2)

async def verify_phone_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """开始手机号验证流程"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    # 检查用户是否已经验证
    existing_verification = PhoneVerification.query.filter_by(user_id=user_id).first()
    if existing_verification and existing_verification.is_verified:
        await update.message.reply_text(
            "✅ 您已经完成了手机号验证，无需重复验证。\n\n"
            f"验证手机: {existing_verification.phone_number}\n"
            f"验证时间: {existing_verification.verification_date.strftime('%Y-%m-%d %H:%M:%S') if existing_verification.verification_date else '未知'}"
        )
        return ConversationHandler.END
    
    # 显示验证说明
    await update.message.reply_text(
        "📱 *手机号验证* 📱\n\n"
        "为提高安全性并防止滥用，我们需要验证您的手机号码。\n\n"
        "请按以下格式输入您的手机号码：\n"
        "`+国家代码电话号码`\n\n"
        "例如：\n"
        "- 中国大陆: `+8613812345678`\n"
        "- 香港: `+85261234567`\n"
        "- 台湾: `+886912345678`\n\n"
        "输入 /cancel 可取消验证流程。",
        parse_mode="Markdown"
    )
    
    return PHONE_INPUT

async def phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """处理用户输入的手机号"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # 检查是否取消操作
    if user_message.lower() == '/cancel':
        await update.message.reply_text("❌ 验证已取消。")
        return ConversationHandler.END
    
    # 简单验证手机号格式
    phone_pattern = r'^\+[0-9]{6,15}$'
    if not re.match(phone_pattern, user_message):
        await update.message.reply_text(
            "❌ 手机号格式不正确。\n\n"
            "请按以下格式重新输入：\n"
            "`+国家代码电话号码`\n\n"
            "例如：`+8613812345678`\n\n"
            "输入 /cancel 可取消验证流程。",
            parse_mode="Markdown"
        )
        return PHONE_INPUT
    
    # 发送验证码
    phone_number = user_message.strip()
    result = send_verification_code(user_id, phone_number)
    
    if result["success"]:
        # 保存电话号码到上下文
        context.user_data['phone_number'] = phone_number
        
        # 向用户发送验证码已发送的消息
        await update.message.reply_text(
            "✅ 验证码已发送到您的手机，请查收。\n\n"
            "请在10分钟内输入收到的6位数字验证码。\n\n"
            "输入 /cancel 可取消验证流程。"
        )
        return CODE_INPUT
    else:
        # 发送验证码失败
        await update.message.reply_text(
            f"❌ 发送验证码失败: {result['message']}\n\n"
            "请检查手机号是否正确，然后重试。\n\n"
            "输入 /cancel 可取消验证流程。"
        )
        return PHONE_INPUT

async def code_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """处理用户输入的验证码"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    user_message = update.message.text
    
    # 检查是否取消操作
    if user_message.lower() == '/cancel':
        await update.message.reply_text("❌ 验证已取消。")
        return ConversationHandler.END
    
    # 验证码格式检查
    if not user_message.isdigit() or len(user_message) != 6:
        await update.message.reply_text(
            "❌ 验证码格式不正确。\n\n"
            "请输入6位数字验证码。\n\n"
            "输入 /cancel 可取消验证流程。"
        )
        return CODE_INPUT
    
    # 验证输入的验证码
    verification_code = user_message.strip()
    result = verify_code(user_id, verification_code)
    
    if result["success"]:
        # 验证成功，保存到数据库
        phone_number = context.user_data.get('phone_number') or result.get('phone')
        
        try:
            # 检查是否已存在验证记录
            existing_verification = PhoneVerification.query.filter_by(user_id=user_id).first()
            
            if existing_verification:
                # 更新现有记录
                existing_verification.phone_number = phone_number
                existing_verification.telegram_username = username
                existing_verification.is_verified = True
                existing_verification.verification_date = datetime.now()
            else:
                # 创建新记录
                new_verification = PhoneVerification(
                    user_id=user_id,
                    telegram_username=username,
                    phone_number=phone_number,
                    is_verified=True,
                    verification_date=datetime.now()
                )
                db.session.add(new_verification)
            
            db.session.commit()
            
            # 向用户发送验证成功的消息
            await update.message.reply_text(
                "🎉 *验证成功* 🎉\n\n"
                "您的手机号已成功验证！现在您可以使用所有机器人功能。\n\n"
                "感谢您的配合，祝您使用愉快！",
                parse_mode="Markdown"
            )
            
            logger.info(f"用户 {username or user_id} 成功完成手机号验证：{phone_number}")
            
        except Exception as e:
            logger.error(f"保存验证信息到数据库时出错: {str(e)}")
            await update.message.reply_text(
                "⚠️ 验证成功，但保存信息时出现问题。请联系管理员。"
            )
    else:
        # 验证失败
        await update.message.reply_text(
            f"❌ {result['message']}\n\n"
            "请重新输入验证码，或输入 /cancel 取消验证流程。"
        )
        return CODE_INPUT
    
    return ConversationHandler.END

async def cancel_verification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """取消验证流程"""
    await update.message.reply_text("❌ 验证已取消。")
    return ConversationHandler.END
