# Dictionary of keywords and their corresponding responses
KEYWORD_RESPONSES = {
    # English keywords and responses
    "hello": "Hello there! How can I help you?",
    "hi": "Hi! How are you doing?",
    "help": "If you need help, you can use the /help command.",
    "thank you": "You're welcome!",
    "thanks": "You're welcome!",
    "rules": "Please read the group rules pinned in the group.",
    "group rules": "The group rules can be found in the pinned messages.",
    
    # 基本问候和回复
    "你好": "你好呀！有什么我可以帮忙的吗？",
    "嗨": "嗨！你好吗？",
    "早上好": "早上好！祝你有个美好的一天~",
    "中午好": "中午好！记得吃午饭哦~",
    "晚上好": "晚上好！今天过得怎么样？",
    "晚安": "晚安！祝你有个甜美的梦~",
    "新年快乐": "新年快乐！祝你在新的一年里万事如意！",
    "元旦快乐": "元旦快乐！新的一年，新的开始！",
    "春节快乐": "春节快乐！恭喜发财，红包拿来！🧧",
    
    # 帮助相关
    "帮助": "如果你需要帮助，可以使用 /help 命令查看所有可用命令。",
    "使用说明": "使用 /help 命令可以查看机器人的所有功能和使用方法。",
    "怎么用": "你可以使用 /help 命令查看所有功能，或者直接问我具体问题。",
    "功能": "本机器人提供群组管理、信息查询、自动回复等功能，使用 /help 查看详情。",
    
    # 感谢用语
    "谢谢": "不客气，很高兴能帮到你！",
    "感谢": "不客气！",
    "太棒了": "谢谢夸奖，我会继续努力的！",
    "好用": "谢谢！我们一直在努力改进~",
    
    # 群组规则
    "规则": "请阅读群组内置顶的群组规则。违反规则可能会被警告或封禁。",
    "群规": "群组规则可以在置顶消息中找到。请大家共同维护良好的群组环境！",
    "禁言": "违反群规的用户可能会被禁言，请大家文明发言，共同维护良好的交流环境。",
    "举报": "如果发现有人违反群规，请联系群组管理员进行举报。",
    
    # 群组信息
    "群组信息": "使用 /stats 命令可以查看当前群组的详细信息。",
    "群统计": "使用 /stats 命令可以查看群组统计信息，包括成员数量等数据。",
    "活动": "群组活动信息会定期在公告中发布，请留意置顶消息。",
    "管理员": "如需联系管理员，请在消息中@管理员或私信他们。",
    
    # 机器人相关
    "机器人": "我是一个群管理机器人，可以帮助管理群组、回答问题和提供各种服务。",
    "指令": "使用 /help 命令可以查看所有可用的指令列表。",
    "命令": "我支持多种命令，如 /start, /help, /ban, /stats 等，详情请查看 /help。",
    
    # 其他常见问题
    "怎么加入": "想加入本群组，请联系群组管理员获取邀请链接。",
    "太安静了": "是有点安静呢，不如分享一些有趣的话题，活跃一下群组氛围吧！",
    "闲聊": "闲聊是允许的，但请遵守群规，保持友善和尊重。",
    "笑话": "抱歉，我不会讲笑话，但你可以在群里分享有趣的事情！"
}

from typing import Optional, Dict
import logging

# 导入配置中的额外关键词回复
try:
    from config import ADDITIONAL_KEYWORD_RESPONSES
except ImportError:
    logging.warning("Could not import ADDITIONAL_KEYWORD_RESPONSES from config.py")
    ADDITIONAL_KEYWORD_RESPONSES = {}

# 合并基础关键词和配置文件中的额外关键词
ALL_KEYWORD_RESPONSES: Dict[str, str] = {**KEYWORD_RESPONSES, **ADDITIONAL_KEYWORD_RESPONSES}

def get_response_for_keyword(message_text: str) -> Optional[str]:
    """
    检查消息是否包含任何关键词并返回相应的回复。
    优先从数据库中获取关键词回复，如果没有找到或者数据库访问出错，则使用配置文件中的关键词。
    
    Args:
        message_text: 要检查关键词的文本消息。
        
    Returns:
        找到的第一个关键词的回复，如果没有找到关键词则返回 None。
    """
    if not message_text:
        return None
        
    message_lower = message_text.lower()
    
    # 尝试从数据库中获取关键词回复
    try:
        # 导入数据库模型
        from app import app
        with app.app_context():
            from models import KeywordResponse
            
            # 获取所有活跃的关键词响应
            keyword_responses = KeywordResponse.query.filter_by(is_active=True).all()
            
            # 优先检查是否包含任何数据库中的关键词
            for kr in keyword_responses:
                if kr.keyword.lower() in message_lower:
                    logging.debug(f"从数据库匹配到关键词 '{kr.keyword}'")
                    return kr.response
    except Exception as e:
        # 如果数据库访问出错，记录错误并回退到配置文件
        logging.warning(f"数据库关键词查询失败: {str(e)}, 使用配置文件中的关键词")
    
    # 如果没有从数据库匹配到，或者出现异常，使用配置文件中的关键词
    for keyword, response in ALL_KEYWORD_RESPONSES.items():
        if keyword.lower() in message_lower:
            logging.debug(f"从配置文件匹配到关键词 '{keyword}'")
            return response
            
    return None
