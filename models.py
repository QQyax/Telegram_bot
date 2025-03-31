from datetime import datetime
# 从 app.py 导入 db 对象
from app import db

class Group(db.Model):
    """群组信息模型"""
    id = db.Column(db.Integer, primary_key=True)
    group_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    link = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 与关键词的关系
    keywords = db.relationship('Keyword', secondary='group_keyword', back_populates='groups')

    def __repr__(self):
        return f'<Group {self.name}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'group_number': self.group_number,
            'name': self.name,
            'link': self.link,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'keywords': [kw.word for kw in self.keywords]
        }

class Keyword(db.Model):
    """关键词模型"""
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 与群组的关系
    groups = db.relationship('Group', secondary='group_keyword', back_populates='keywords')

    def __repr__(self):
        return f'<Keyword {self.word}>'

# 群组-关键词关联表
group_keyword = db.Table('group_keyword',
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True),
    db.Column('keyword_id', db.Integer, db.ForeignKey('keyword.id'), primary_key=True)
)

class KeywordResponse(db.Model):
    """关键词回复模型"""
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(50), unique=True, nullable=False)
    response = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<KeywordResponse {self.keyword}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'keyword': self.keyword,
            'response': self.response,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Channel(db.Model):
    """频道信息模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    link = db.Column(db.String(255), nullable=False)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Channel {self.name}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'description': self.description,
            'link': self.link,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class MessageLog(db.Model):
    """消息日志模型"""
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.BigInteger, nullable=False)
    chat_type = db.Column(db.String(20), nullable=False)
    chat_title = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.BigInteger, nullable=True)
    username = db.Column(db.String(100), nullable=True)
    message_text = db.Column(db.Text, nullable=True)
    trigger_keyword = db.Column(db.String(50), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MessageLog {self.id}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'chat_type': self.chat_type,
            'chat_title': self.chat_title,
            'user_id': self.user_id,
            'username': self.username,
            'message_text': self.message_text,
            'trigger_keyword': self.trigger_keyword,
            'is_admin': self.is_admin,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

class BotSettings(db.Model):
    """机器人设置模型 - 单例模式"""
    id = db.Column(db.Integer, primary_key=True)
    welcome_message = db.Column(db.Text, nullable=False)
    private_chat_welcome = db.Column(db.Text, nullable=False)
    channel_info = db.Column(db.Text, nullable=False)
    is_admin_only = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<BotSettings {self.id}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'welcome_message': self.welcome_message,
            'private_chat_welcome': self.private_chat_welcome,
            'channel_info': self.channel_info,
            'is_admin_only': self.is_admin_only,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PhoneVerification(db.Model):
    """手机号码验证模型"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.BigInteger, nullable=False, index=True)
    telegram_username = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(20), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<PhoneVerification {self.id} - {self.phone_number}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'telegram_username': self.telegram_username,
            'phone_number': self.phone_number,
            'is_verified': self.is_verified,
            'verification_date': self.verification_date.isoformat() if self.verification_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
class GroupChatSettings(db.Model):
    """群组聊天设置模型 - 用于存储群聊设置，如禁言状态等"""
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.BigInteger, unique=True, nullable=False, index=True)
    chat_title = db.Column(db.String(255), nullable=True)
    is_muted = db.Column(db.Boolean, default=False)  # 群组是否被禁言
    muted_at = db.Column(db.DateTime, nullable=True)  # 禁言时间
    muted_by = db.Column(db.BigInteger, nullable=True)  # 禁言操作执行者ID
    unmuted_at = db.Column(db.DateTime, nullable=True)  # 解除禁言时间
    unmuted_by = db.Column(db.BigInteger, nullable=True)  # 解除禁言操作执行者ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        mute_status = "已禁言" if self.is_muted else "正常"
        return f"<GroupChatSettings {self.chat_id} ({self.chat_title}): {mute_status}>"
        
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "chat_title": self.chat_title,
            "is_muted": self.is_muted,
            "muted_at": self.muted_at.isoformat() if self.muted_at else None,
            "muted_by": self.muted_by,
            "unmuted_at": self.unmuted_at.isoformat() if self.unmuted_at else None,
            "unmuted_by": self.unmuted_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }