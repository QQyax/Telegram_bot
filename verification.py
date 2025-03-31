import random
import string
import logging
from datetime import datetime, timedelta
from utils.sms_sender import send_sms

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 存储验证码的字典 {user_id: {'code': '123456', 'expires_at': datetime, 'phone': '+1234567890'}}
verification_codes = {}

def generate_verification_code(length=6):
    """
    生成指定长度的数字验证码
    
    Args:
        length (int): 验证码长度，默认为6位
        
    Returns:
        str: 生成的验证码
    """
    return ''.join(random.choices(string.digits, k=length))

def send_verification_code(user_id, phone_number, code_length=6, expires_minutes=10):
    """
    生成验证码并发送到指定手机号
    
    Args:
        user_id (int): 用户ID，用于后续验证
        phone_number (str): 手机号码，格式为 +国家代码电话号码
        code_length (int): 验证码长度，默认为6位
        expires_minutes (int): 验证码有效期（分钟），默认为10分钟
        
    Returns:
        dict: 包含操作结果的字典
    """
    # 生成验证码
    verification_code = generate_verification_code(code_length)
    
    # 设置过期时间
    expires_at = datetime.now() + timedelta(minutes=expires_minutes)
    
    # 构建短信内容
    message = f"【好旺公群】您的验证码是 {verification_code}，{expires_minutes}分钟内有效。请勿泄露给他人！"
    
    # 发送短信
    result = send_sms(phone_number, message)
    
    if result["success"]:
        # 存储验证码信息
        verification_codes[user_id] = {
            'code': verification_code,
            'expires_at': expires_at,
            'phone': phone_number
        }
        
        logger.info(f"验证码已发送至 {phone_number}，过期时间: {expires_at}")
        return {
            "success": True,
            "message": f"验证码已发送至 {phone_number}",
            "expires_at": expires_at
        }
    else:
        logger.error(f"验证码发送失败: {result['message']}")
        return result

def verify_code(user_id, code):
    """
    验证用户输入的验证码是否正确
    
    Args:
        user_id (int): 用户ID
        code (str): 用户输入的验证码
        
    Returns:
        dict: 包含验证结果的字典
    """
    # 检查是否存在该用户的验证码
    if user_id not in verification_codes:
        return {
            "success": False,
            "message": "验证码不存在或已过期，请重新获取验证码"
        }
    
    verification_info = verification_codes[user_id]
    
    # 检查验证码是否过期
    if datetime.now() > verification_info['expires_at']:
        # 删除过期验证码
        del verification_codes[user_id]
        return {
            "success": False,
            "message": "验证码已过期，请重新获取验证码"
        }
    
    # 验证码是否匹配
    if code == verification_info['code']:
        # 验证成功后删除验证码，防止重复使用
        phone = verification_info['phone']
        del verification_codes[user_id]
        
        return {
            "success": True,
            "message": "验证成功",
            "phone": phone
        }
    else:
        return {
            "success": False,
            "message": "验证码错误，请重新输入"
        }

def clean_expired_codes():
    """
    清理过期的验证码
    
    Returns:
        int: 清理的验证码数量
    """
    now = datetime.now()
    expired_keys = [
        user_id for user_id, info in verification_codes.items()
        if now > info['expires_at']
    ]
    
    for user_id in expired_keys:
        del verification_codes[user_id]
    
    if expired_keys:
        logger.info(f"已清理 {len(expired_keys)} 个过期验证码")
    
    return len(expired_keys)