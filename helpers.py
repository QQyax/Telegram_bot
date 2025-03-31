from typing import List, Dict, Any
from telegram import Bot, ChatMember, ChatMemberAdministrator, ChatMemberOwner

async def get_group_admins(bot: Bot, chat_id: int) -> List[Dict[str, Any]]:
    """
    Get a list of all administrators in a group.
    
    Args:
        bot: The bot instance
        chat_id: The ID of the chat/group
        
    Returns:
        A list of admin user info dictionaries
    """
    admins = []
    try:
        administrators = await bot.get_chat_administrators(chat_id)
        for admin in administrators:
            admin_info = {
                'id': admin.user.id,
                'username': admin.user.username,
                'first_name': admin.user.first_name,
                'is_bot': admin.user.is_bot,
                'is_owner': isinstance(admin, ChatMemberOwner)
            }
            admins.append(admin_info)
        return admins
    except Exception as e:
        print(f"获取管理员列表错误 (Error retrieving admins): {e}")
        return []

async def is_user_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    """
    Check if a user is an admin in the group.
    
    Args:
        bot: The bot instance
        chat_id: The ID of the chat/group
        user_id: The ID of the user to check
        
    Returns:
        True if the user is an admin, False otherwise
    """
    try:
        chat_member = await bot.get_chat_member(chat_id, user_id)
        return isinstance(chat_member, (ChatMemberAdministrator, ChatMemberOwner))
    except Exception as e:
        print(f"检查管理员状态错误 (Error checking admin status): {e}")
        return False
