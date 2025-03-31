import logging
import re
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from bot.responses import get_response_for_keyword
from bot.helpers import is_user_admin
from config import PRIVATE_CHAT_WELCOME, CHANNEL_INFO, GROUP_DATABASE

# 导入 app 模块以访问机器人状态
try:
    from app import bot_status
except ImportError:
    # 如果导入失败，创建一个假的状态对象以防止错误
    bot_status = {"messages_processed": 0, "is_running": True}

logger = logging.getLogger(__name__)

async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome new members when they join the group."""
    new_members = update.message.new_chat_members
    chat_title = update.effective_chat.title
    
    for member in new_members:
        # Don't welcome the bot itself
        if member.id == context.bot.id:
            continue
            
        welcome_message = f"欢迎 {member.first_name} 加入 {chat_title}！👋"
        
        # If the user has a username, mention it
        if member.username:
            welcome_message += f"\n您可以通过 @{member.username} 被提及"
            
        # Add group rules or information if needed
        welcome_message += "\n\n请阅读群组规则并享受您的时光！"
        
        await update.message.reply_text(welcome_message)
        logger.info(f"Welcomed new member: {member.first_name} ({member.id}) to {chat_title}")

async def handle_private_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理私聊消息，提供群组搜索和导航功能"""
    if not update.message or not update.message.text:
        return
    
    # 只处理私聊消息
    if update.effective_chat.type != "private":
        return
    
    user = update.effective_user
    message_text = update.message.text.strip()
    
    # 更新处理消息计数
    bot_status["messages_processed"] += 1
    
    # 记录用户查询
    username = f"@{user.username}" if user and user.username else f"{user.first_name}" if user else "未知用户"
    logger.info(f"私聊查询 | 用户: {username} | 查询内容: '{message_text}'")
    
    # 处理首次私聊或/start命令
    if message_text.lower() == "/start":
        # 创建主要联系按钮，和查看频道按钮
        hwgq_button = InlineKeyboardButton("好旺公群", url="https://t.me/hwgq")
        channel_button = InlineKeyboardButton("查看频道", callback_data="view_channels")
        keyboard = InlineKeyboardMarkup([
            [hwgq_button],
            [channel_button]
        ])
        
        # 获取机器人设置中的欢迎消息，如果数据库中有的话
        try:
            from models import BotSettings
            settings = BotSettings.query.first()
            welcome_text = settings.private_chat_welcome if settings else PRIVATE_CHAT_WELCOME
        except Exception:
            # 如果出现异常（如数据库未初始化），使用默认欢迎消息
            welcome_text = PRIVATE_CHAT_WELCOME
        
        # 以HTML格式发送美观的欢迎消息，使用渐变背景效果
        await update.message.reply_text(
            welcome_text, 
            reply_markup=keyboard,
            parse_mode="HTML"  # 允许使用HTML格式以增强视觉效果
        )
        return
    
    # 处理群组编号查询 - 更新了正则表达式，支持更多格式
    # 1. 匹配中括号格式: 【数字】或[数字]，允许括号内外有空格
    group_number_match = re.search(r'[【\[\(]([\s\d]+)[】\]\)]', message_text)
    
    # 2. 如果没有中括号格式，尝试直接匹配纯数字（如001、123、666、1096等）
    if not group_number_match and re.search(r'^\s*\d{3,4}\s*$', message_text.strip()):
        group_number = message_text.strip()
        # 移除可能的前导零
        group_number = group_number.lstrip('0') or '0'
        # 查找群组信息
        await search_group_by_number(update, group_number)
        return
    elif group_number_match:
        # 提取并清理群组编号（去掉空格和前导零）
        group_number = group_number_match.group(1).strip()
        group_number = group_number.lstrip('0') or '0'
        # 查找群组信息
        await search_group_by_number(update, group_number)
        return
    
    # 处理关键词搜索
    # 先检查是否有自动回复的关键词
    keyword_response = get_response_for_keyword(message_text)
    if keyword_response:
        await update.message.reply_text(keyword_response)
        return
    
    # 如果没有匹配到关键词回复，尝试进行群组关键词搜索
    await search_groups_by_keyword(update, message_text)

async def search_group_by_number(update: Update, group_number: str) -> None:
    """通过群组编号搜索并返回群组信息，使用美观的格式，参考示例截图样式"""
    group_info = None
    
    # 首先尝试从数据库中查找群组
    try:
        from app import app
        with app.app_context():
            from models import Group
            db_group = Group.query.filter_by(group_number=group_number).first()
            
            if db_group:
                group_info = {
                    "name": db_group.name,
                    "link": db_group.link,
                    "description": db_group.description
                }
                logger.debug(f"从数据库找到群组: {group_number}")
    except Exception as e:
        # 如果数据库查询失败，记录错误
        logger.warning(f"数据库群组查询失败: {str(e)}")
    
    # 如果数据库中没有找到，尝试从配置文件中查找
    if not group_info and group_number in GROUP_DATABASE["数字编号"]:
        group_info = GROUP_DATABASE["数字编号"][group_number]
        logger.debug(f"从配置文件找到群组: {group_number}")
    
    # 如果找到群组信息，显示详情
    if group_info:
        # 根据截图样式创建带有背景颜色的标题
        # 根据群组描述设置分类
        group_category = "钱钱"  # 默认分类
        
        # 尝试从群组描述或关键词中获取更合适的分类
        description_lower = group_info['description'].lower()
        if any(kw in description_lower for kw in ["卡商", "pos机"]):
            group_category = "卡商"
        elif any(kw in description_lower for kw in ["代收", "代付", "支付"]):
            group_category = "代收代付"
        elif any(kw in description_lower for kw in ["白资"]):
            group_category = "白资"
        elif any(kw in description_lower for kw in ["承兑", "usdt", "互换"]):
            group_category = "承兑"
        elif any(kw in description_lower for kw in ["换汇", "货币"]):
            group_category = "换汇"
        elif any(kw in description_lower for kw in ["包网", "搭建"]):
            group_category = "包网"
        elif any(kw in description_lower for kw in ["技术", "开发"]):
            group_category = "技术"
            
        # 使用HTML格式创建美观的响应，完全参考截图样式
        # 顶部有群类型，然后是群号
        response = (
            f"<b>{group_category}</b>\n"
            f"<b>{group_number}</b>\n\n"
            f"<a href='{group_info['link']}'>{group_info['link']}</a>\n\n"
            f"<b>Telegram</b>\n"  # Telegram标签
            f"公群{group_number} {group_info['description']}\n"  # 使用完整描述
        )
        
        # 尝试使用引用回复发送消息
        try:
            await update.message.reply_text(
                response, 
                reply_to_message_id=update.message.message_id,  # 引用用户的消息
                parse_mode="HTML",  # 启用HTML格式
                disable_web_page_preview=False  # 启用网页预览，显示群组图片
            )
        except Exception as e:
            # 如果引用回复失败，尝试普通回复
            logger.warning(f"引用回复失败: {str(e)}")
            await update.message.reply_text(
                response, 
                parse_mode="HTML",
                disable_web_page_preview=False
            )
        
        logger.info(f"成功查询群组编号: {group_number} | 群组: {group_info['name']}")
        
        # 记录消息日志
        try:
            from app import app, db
            with app.app_context():
                from models import MessageLog
                log = MessageLog(
                    chat_id=update.effective_chat.id,
                    chat_type="private",
                    user_id=update.effective_user.id if update.effective_user else None,
                    username=update.effective_user.username if update.effective_user and update.effective_user.username else None,
                    message_text=f"查询群组编号:{group_number}"
                )
                db.session.add(log)
                db.session.commit()
        except Exception as e:
            logger.warning(f"记录消息日志失败: {str(e)}")
    else:
        # 创建返回主菜单按钮
        main_menu_button = InlineKeyboardButton("返回主菜单", callback_data="main_menu")
        contact_support_button = InlineKeyboardButton("联系客服", url="https://t.me/kefu")
        keyboard = InlineKeyboardMarkup([
            [main_menu_button],
            [contact_support_button]
        ])
        
        # 使用HTML格式创建美观的错误响应
        await update.message.reply_text(
            f"<b>❌ 未找到编号为【{group_number}】的群组。</b>\n\n"
            "请确认编号是否正确，或尝试使用以下方式找到群组：\n"
            "1. 输入关键词如：好旺、卡商、代收、白资等\n"
            "2. 联系客服了解更多群组：@kefu",
            reply_markup=keyboard,
            parse_mode="HTML",  # 启用HTML格式
            reply_to_message_id=update.message.message_id  # 引用用户的消息
        )
        logger.info(f"查询了不存在的群组编号: {group_number}")

async def search_groups_by_keyword(update: Update, keyword: str) -> None:
    """通过关键词搜索并返回相关群组列表，使用美观的格式"""
    found_groups = []
    
    # 首先尝试从数据库中查询关键词和群组
    try:
        from app import app
        with app.app_context():
            from models import Group, Keyword
            
            # 查找包含关键词的群组
            db_keywords = Keyword.query.filter(Keyword.word.ilike(f"%{keyword}%")).all()
            if db_keywords:
                for kw in db_keywords:
                    for group in kw.groups:
                        if group.group_number not in [g.get("number") for g in found_groups]:
                            found_groups.append({
                                "number": group.group_number,
                                "name": group.name,
                                "description": group.description,
                                "link": group.link
                            })
            
            # 如果没有找到，再尝试搜索群组名称和描述
            if not found_groups:
                db_groups = Group.query.filter(
                    (Group.name.ilike(f"%{keyword}%")) | 
                    (Group.description.ilike(f"%{keyword}%"))
                ).all()
                
                for group in db_groups:
                    if group.group_number not in [g.get("number") for g in found_groups]:
                        found_groups.append({
                            "number": group.group_number,
                            "name": group.name,
                            "description": group.description,
                            "link": group.link
                        })
            
            logger.debug(f"从数据库搜索关键词 '{keyword}' 找到 {len(found_groups)} 个群组")
    except Exception as e:
        # 如果数据库查询失败，记录错误
        logger.warning(f"数据库关键词搜索失败: {str(e)}")
    
    # 如果数据库中没有找到，尝试从配置文件中查找
    if not found_groups:
        # 在关键词索引中查找匹配项
        for key in GROUP_DATABASE["关键词"]:
            if keyword.lower() in key.lower() or key.lower() in keyword.lower():
                group_numbers = GROUP_DATABASE["关键词"][key]
                for number in group_numbers:
                    if number in GROUP_DATABASE["数字编号"] and number not in [g.get("number") for g in found_groups]:
                        group_info = GROUP_DATABASE["数字编号"][number]
                        found_groups.append({
                            "number": number,
                            "name": group_info["name"],
                            "description": group_info["description"],
                            "link": group_info["link"]
                        })
        logger.debug(f"从配置文件搜索关键词 '{keyword}' 找到 {len(found_groups)} 个群组")
    
    if found_groups:
        # 构建HTML格式的响应消息
        response = f"<b>🔍 关键词「{keyword}」搜索结果：</b>\n\n"
        
        # 为每个找到的群组创建按钮
        keyboard = []
        
        for idx, group in enumerate(found_groups, 1):
            response += f"<b>{idx}. {group['name']}</b> (编号: {group['number']})\n"
            response += f"   {group['description']}\n\n"
            
            # 添加群组按钮
            join_button = InlineKeyboardButton(f"加入 {group['name']}", url=group['link'])
            keyboard.append([join_button])
        
        # 添加返回主菜单的按钮
        keyboard.append([InlineKeyboardButton("返回主菜单", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # 发送美观的搜索结果
        await update.message.reply_text(
            response, 
            reply_markup=reply_markup,
            parse_mode="HTML"  # 启用HTML格式
        )
        logger.info(f"关键词搜索成功 | 关键词: '{keyword}' | 找到 {len(found_groups)} 个群组")
    else:
        # 创建返回主菜单按钮
        main_menu_button = InlineKeyboardButton("返回主菜单", callback_data="main_menu")
        contact_support_button = InlineKeyboardButton("联系客服", url="https://t.me/kefu")
        keyboard = InlineKeyboardMarkup([
            [main_menu_button],
            [contact_support_button]
        ])
        
        # 如果没有找到群组，提供美观的建议消息
        await update.message.reply_text(
            f"<b>❌ 未找到与「{keyword}」相关的群组。</b>\n\n"
            "您可以：\n"
            "1. 尝试使用其他关键词，如：卡商、代收、白资等\n"
            "2. 直接发送群组编号，格式如：【123】\n"
            "3. 联系客服获取帮助：@kefu",
            reply_markup=keyboard,
            parse_mode="HTML"  # 启用HTML格式
        )
        logger.info(f"关键词搜索无结果 | 关键词: '{keyword}'")

async def handle_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理按钮回调查询"""
    query = update.callback_query
    await query.answer()  # 通知 Telegram 客户端回调已处理
    
    if query.data == "main_menu":
        # 创建主要联系按钮
        hwgq_button = InlineKeyboardButton("好旺公群", url="https://t.me/hwgq")
        channel_button = InlineKeyboardButton("查看频道", callback_data="view_channels")
        keyboard = InlineKeyboardMarkup([
            [hwgq_button],
            [channel_button]
        ])
        
        # 尝试从数据库获取欢迎消息
        try:
            from models import BotSettings
            settings = BotSettings.query.first()
            welcome_text = settings.private_chat_welcome if settings else PRIVATE_CHAT_WELCOME
        except Exception:
            # 如果出现异常（如数据库未初始化），使用默认欢迎消息
            welcome_text = PRIVATE_CHAT_WELCOME
        
        # 返回主菜单，显示美观的欢迎消息
        await query.message.edit_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode="HTML"  # 允许使用HTML格式，保持样式一致
        )
    
    elif query.data == "view_channels":
        # 显示频道列表
        # 为每个官方频道创建对应的按钮
        buttons = []
        
        # 尝试从数据库获取频道信息
        try:
            from models import Channel
            
            # 获取频道信息并按display_order排序
            channels_db = Channel.query.order_by(Channel.display_order).all()
            
            if channels_db:
                channels = [(c.name, c.username) for c in channels_db]
            else:
                # 如果数据库中没有数据，使用默认值
                channels = [
                    ("好旺公群", "hwgq"),
                    ("供求信息", "hwtb2"),
                    ("新开公群", "xinqun"),
                    ("核心大群", "daqun"),
                    ("防骗指南", "hwtb22"),
                    ("担保教程", "hwtb33"),
                    ("联系好旺担保", "hwdb")
                ]
        except Exception:
            # 如果出现异常，使用默认值
            channels = [
                ("好旺公群", "hwgq"),
                ("供求信息", "hwtb2"),
                ("新开公群", "xinqun"),
                ("核心大群", "daqun"),
                ("防骗指南", "hwtb22"),
                ("担保教程", "hwtb33"),
                ("联系好旺担保", "hwdb")
            ]
        
        # 尝试从数据库获取频道信息展示文本
        try:
            from models import BotSettings
            settings = BotSettings.query.first()
            channel_info = settings.channel_info if settings else CHANNEL_INFO
        except Exception:
            # 出现异常时使用默认配置
            channel_info = CHANNEL_INFO
        
        # 使用美观的频道列表消息，与欢迎消息保持一致风格
        # 添加每个频道的按钮
        for name, username in channels:
            buttons.append([InlineKeyboardButton(name, url=f"https://t.me/{username}")])
        
        # 添加返回主菜单按钮和查看全部频道按钮
        buttons.append([InlineKeyboardButton("查看频道", callback_data="view_all_channels")])
        buttons.append([InlineKeyboardButton("返回主菜单", callback_data="main_menu")])
        keyboard = InlineKeyboardMarkup(buttons)
        
        # 发送美观的频道列表
        await query.message.edit_text(
            channel_info,
            reply_markup=keyboard,
            parse_mode="HTML"  # 允许使用HTML格式
        )
    
    # 其他回调操作可在此处理

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """自动回复包含特定关键词的消息。只有群组管理员可以使用此功能。"""
    # 检查消息是否存在且有文本内容
    if not update.message or not update.message.text:
        return
    
    chat_type = update.effective_chat.type
    chat_id = update.effective_chat.id
    user = update.effective_user
    user_id = user.id if user else None
    message_text = update.message.text
    
    # 更新处理消息计数
    bot_status["messages_processed"] += 1
    
    # 如果是私聊，则交由私聊处理器处理
    if chat_type == "private":
        await handle_private_chat(update, context)
        return
    
    # 以下是群组聊天的处理逻辑
    is_admin = False
    
    if user_id:
        # 检查用户是否是管理员
        is_admin = await is_user_admin(context.bot, chat_id, user_id)
    
    # 获取关键词回复
    response = get_response_for_keyword(message_text)
    
    if response:
        # 只有管理员可以触发机器人（除了验群关键词）
        if is_admin:
            # 处理关群和开群命令
            if "禁言" in message_text.lower() and "解除" not in message_text.lower():
                # 关群命令
                try:
                    # 获取或创建群组设置
                    from app import app
                    with app.app_context():
                        from models import GroupChatSettings
                        
                        chat_title = update.effective_chat.title
                        # 检查群组是否已存在设置
                        group_settings = GroupChatSettings.query.filter_by(chat_id=chat_id).first()
                        
                        if group_settings:
                            # 更新现有设置
                            group_settings.is_muted = True
                            group_settings.muted_at = datetime.utcnow()
                            group_settings.muted_by = user_id
                            group_settings.chat_title = chat_title  # 更新群组名称
                        else:
                            # 创建新的群组设置
                            group_settings = GroupChatSettings(
                                chat_id=chat_id,
                                chat_title=chat_title,
                                is_muted=True,
                                muted_at=datetime.utcnow(),
                                muted_by=user_id
                            )
                            from app import db
                            db.session.add(group_settings)
                        
                        # 保存更改
                        from app import db
                        db.session.commit()
                        
                        logger.info(f"群组 {chat_title} ({chat_id}) 已被管理员 {user_id} 设置为禁言状态")
                except Exception as e:
                    logger.error(f"设置群组禁言状态时出错: {str(e)}")
                
            elif "解除禁言" in message_text.lower():
                # 开群命令
                try:
                    # 获取或创建群组设置
                    from app import app
                    with app.app_context():
                        from models import GroupChatSettings
                        
                        chat_title = update.effective_chat.title
                        # 检查群组是否已存在设置
                        group_settings = GroupChatSettings.query.filter_by(chat_id=chat_id).first()
                        
                        if group_settings:
                            # 更新现有设置
                            group_settings.is_muted = False
                            group_settings.unmuted_at = datetime.utcnow()
                            group_settings.unmuted_by = user_id
                            group_settings.chat_title = chat_title  # 更新群组名称
                        else:
                            # 创建新的群组设置（默认为非禁言状态）
                            group_settings = GroupChatSettings(
                                chat_id=chat_id,
                                chat_title=chat_title,
                                is_muted=False,
                                unmuted_at=datetime.utcnow(),
                                unmuted_by=user_id
                            )
                            from app import db
                            db.session.add(group_settings)
                        
                        # 保存更改
                        from app import db
                        db.session.commit()
                        
                        logger.info(f"群组 {chat_title} ({chat_id}) 已被管理员 {user_id} 解除禁言状态")
                except Exception as e:
                    logger.error(f"解除群组禁言状态时出错: {str(e)}")
            
            # 根据用户名称个性化回复（如果可用）
            if user and user.first_name:
                # 如果响应中没有称呼，且不是系统性的响应（如规则通知），可以加上称呼
                if not any(keyword in response for keyword in ["命令", "规则", "功能", "/", "使用", "禁言"]):
                    # 20%的概率在回复前面加上用户称呼
                    import random
                    if random.random() < 0.2:
                        response = f"{user.first_name}，{response}"
            
            # 发送回复
            await update.message.reply_text(response)
            
            # 记录详细日志
            username = f"@{user.username}" if user and user.username else "未知用户"
            chat_name = update.effective_chat.title
            
            logger.info(
                f"自动回复消息 | 聊天: {chat_name} | "
                f"用户: {username} | 触发文本: '{message_text[:20]}...' 如果较长"
            )
        elif "验群" in message_text.lower():
            # 即使不是管理员，也允许"验群"关键词，因为这是安全验证功能
            await update.message.reply_text(response)
            logger.info(f"验群消息回复 | 由非管理员触发: {user.username if user and user.username else '未知用户'}")
        else:
            # 检查群组是否处于禁言状态
            try:
                from app import app
                with app.app_context():
                    from models import GroupChatSettings
                    group_settings = GroupChatSettings.query.filter_by(chat_id=chat_id).first()
                    
                    if group_settings and group_settings.is_muted:
                        # 如果群组处于禁言状态，不提示用户关于管理员限制
                        return
            except Exception:
                pass
                
            # 告知用户只有管理员可以使用机器人
            await update.message.reply_text("抱歉，只有群组管理员可以使用机器人功能。")
            logger.info(f"非管理员尝试使用机器人 | 用户: {user.username if user and user.username else '未知用户'}")
