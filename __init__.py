from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters

from bot.commands import (
    start, help_command, ban_user, mute_user, unmute_user, stats_command, 
    admin_panel, button_callback, verify_phone_start, phone_input, 
    code_input, cancel_verification, PHONE_INPUT, CODE_INPUT
)
from bot.handlers import welcome_new_members, auto_reply, handle_button_callback, handle_private_chat

def create_bot(token):
    """
    Create and configure the Telegram bot.
    
    Args:
        token: The Telegram bot API token.
        
    Returns:
        The configured bot application.
    """
    # Create the Application
    application = ApplicationBuilder().token(token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("admin", admin_panel))
    
    # Add callback query handlers for interactive buttons
    # Admin panel button callbacks
    application.add_handler(CallbackQueryHandler(button_callback, pattern=r"^admin_"))
    application.add_handler(CallbackQueryHandler(button_callback, pattern=r"^mute_"))
    application.add_handler(CallbackQueryHandler(button_callback, pattern=r"^unmute_user$"))
    # Private chat navigation and group search callbacks
    application.add_handler(CallbackQueryHandler(handle_button_callback, pattern=r"^(main_menu|group_|search_)"))
    
    # 添加手机验证对话处理器
    verify_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("verify", verify_phone_start)],
        states={
            PHONE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_input)],
            CODE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, code_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_verification)],
    )
    application.add_handler(verify_conv_handler)
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, handle_private_chat))
    application.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, auto_reply))
    
    return application
