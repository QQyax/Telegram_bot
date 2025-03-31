import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Twilio 配置
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

def send_sms(to_phone_number, message):
    """
    使用Twilio发送短信
    
    Args:
        to_phone_number (str): 接收短信的电话号码 (格式: +国家代码电话号码，例如 +8613812345678)
        message (str): 短信内容
        
    Returns:
        dict: 包含发送状态和信息的字典
    """
    # 检查是否配置了Twilio密钥
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        logger.error("Twilio配置不完整，缺少必要的环境变量")
        return {
            "success": False,
            "message": "短信服务配置不完整，请联系管理员",
            "error": "缺少Twilio配置"
        }
    
    # 创建Twilio客户端
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # 发送短信
        twilio_message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        
        logger.info(f"短信发送成功: SID={twilio_message.sid}, 状态={twilio_message.status}")
        return {
            "success": True,
            "message": "短信发送成功",
            "sid": twilio_message.sid,
            "status": twilio_message.status
        }
    
    except TwilioRestException as e:
        logger.error(f"Twilio错误: {str(e)}")
        
        # 提供友好的错误消息
        error_message = "短信发送失败"
        if e.code == 21211:
            error_message = "无效的电话号码格式，请确保包含国家代码 (例如: +8613800138000)"
        elif e.code == 21608:
            error_message = "该号码不是有效的手机号码"
        elif e.code == 21610:
            error_message = "该号码已选择不接收短信"
        
        return {
            "success": False,
            "message": error_message,
            "error": str(e),
            "code": e.code
        }
    
    except Exception as e:
        logger.error(f"发送短信时出现错误: {str(e)}")
        return {
            "success": False,
            "message": "发送短信时出现未知错误",
            "error": str(e)
        }