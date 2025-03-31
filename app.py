import os
import logging
from datetime import datetime
from flask import Flask, render_template_string
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# 机器人状态信息 - 放在最前面，避免循环导入问题
bot_status = {
    "started_at": datetime.now(),
    "is_running": True,
    "messages_processed": 0
}

class Base(DeclarativeBase):
    pass

# 初始化 SQLAlchemy
db = SQLAlchemy(model_class=Base)

# 设置 Flask 应用
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "highly-secure-secret-key")

# 配置数据库
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///bot.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
# 初始化数据库
db.init_app(app)

@app.route('/')
def index():
    """显示机器人状态页面"""
    status_text = "运行中" if bot_status["is_running"] else "未运行"
    uptime = "N/A"
    
    if bot_status["started_at"]:
        uptime_seconds = (datetime.now() - bot_status["started_at"]).total_seconds()
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        uptime = f"{hours}小时 {minutes}分钟 {seconds}秒"
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>好旺公群机器人管理面板</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
        <style>
            body {
                background: linear-gradient(135deg, #ff9d6c 0%, #bb4e75 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                padding: 20px 0;
            }
            .card {
                background-color: rgba(0, 0, 0, 0.6);
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
                margin-bottom: 20px;
            }
            .card-header {
                background-color: rgba(0, 0, 0, 0.3);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            .status-indicator {
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 8px;
            }
            .status-running {
                background-color: #28a745;
            }
            .status-stopped {
                background-color: #dc3545;
            }
            .info-section {
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                padding-top: 15px;
                margin-top: 15px;
            }
            .bot-image {
                max-width: 100px;
                border-radius: 50%;
                margin: 0 auto 15px;
                display: block;
                border: 3px solid white;
                box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
            }
            .nav-pills .nav-link {
                color: rgba(255, 255, 255, 0.8);
                background-color: rgba(0, 0, 0, 0.2);
                margin-right: 5px;
                border-radius: 10px;
                transition: all 0.3s;
            }
            .nav-pills .nav-link:hover {
                color: white;
                background-color: rgba(0, 0, 0, 0.4);
            }
            .nav-pills .nav-link.active {
                color: white;
                background-color: rgba(187, 78, 117, 0.8);
            }
            .stat-card {
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
                text-align: center;
                transition: all 0.3s;
            }
            .stat-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            }
            .stat-icon {
                font-size: 2rem;
                margin-bottom: 10px;
            }
            .control-btn {
                margin: 5px;
                min-width: 120px;
            }
            .tab-content {
                padding: 20px 0;
            }
            .action-btn {
                min-width: 140px;
                margin: 5px;
            }
            .progress {
                height: 10px;
                border-radius: 5px;
                margin-top: 5px;
            }
            .table {
                color: rgba(255, 255, 255, 0.9);
            }
            .table thead th {
                border-color: rgba(255, 255, 255, 0.1);
            }
            .table tbody td {
                border-color: rgba(255, 255, 255, 0.05);
            }
            .table-dark {
                background-color: rgba(0, 0, 0, 0.2);
            }
            .form-control, .form-select {
                background-color: rgba(0, 0, 0, 0.3);
                border-color: rgba(255, 255, 255, 0.1);
                color: white;
            }
            .form-control:focus, .form-select:focus {
                background-color: rgba(0, 0, 0, 0.4);
                color: white;
                border-color: rgba(255, 255, 255, 0.3);
                box-shadow: 0 0 0 0.25rem rgba(255, 255, 255, 0.1);
            }
        </style>
    </head>
    <body>
        <div class="container py-3">
            <div class="card mb-4">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h3 class="mb-0">好旺公群机器人控制中心</h3>
                    <span class="badge {{ 'bg-success' if status == '运行中' else 'bg-danger' }}">
                        <i class="bi {{ 'bi-robot' if status == '运行中' else 'bi-robot' }}"></i> {{ status }}
                    </span>
                </div>
                <div class="card-body">
                    <div class="row align-items-center mb-4">
                        <div class="col-md-3 text-center">
                            <img src="https://ui-avatars.com/api/?name=HW&background=bb4e75&color=fff&size=128" class="bot-image">
                        </div>
                        <div class="col-md-9">
                            <div class="row">
                                <div class="col-md-4">
                                    <div class="stat-card">
                                        <i class="bi bi-clock-history stat-icon text-warning"></i>
                                        <h5>运行时间</h5>
                                        <p class="mb-0">{{ uptime }}</p>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="stat-card">
                                        <i class="bi bi-chat-dots stat-icon text-info"></i>
                                        <h5>处理消息数</h5>
                                        <p class="mb-0">{{ messages }}</p>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="stat-card">
                                        <i class="bi bi-people stat-icon text-success"></i>
                                        <h5>用户数量</h5>
                                        <p class="mb-0">{{ phone_verifications }}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <ul class="nav nav-pills mb-3" id="pills-tab" role="tablist">
                        <li class="nav-item" role="presentation">
                            <button class="nav-link active" id="pills-dashboard-tab" data-bs-toggle="pill" data-bs-target="#pills-dashboard" type="button" role="tab" aria-controls="pills-dashboard" aria-selected="true">
                                <i class="bi bi-speedometer2"></i> 控制面板
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="pills-groups-tab" data-bs-toggle="pill" data-bs-target="#pills-groups" type="button" role="tab" aria-controls="pills-groups" aria-selected="false">
                                <i class="bi bi-people-fill"></i> 群组管理
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="pills-keywords-tab" data-bs-toggle="pill" data-bs-target="#pills-keywords" type="button" role="tab" aria-controls="pills-keywords" aria-selected="false">
                                <i class="bi bi-chat-square-text"></i> 关键词
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="pills-logs-tab" data-bs-toggle="pill" data-bs-target="#pills-logs" type="button" role="tab" aria-controls="pills-logs" aria-selected="false">
                                <i class="bi bi-journal-text"></i> 日志
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="pills-settings-tab" data-bs-toggle="pill" data-bs-target="#pills-settings" type="button" role="tab" aria-controls="pills-settings" aria-selected="false">
                                <i class="bi bi-gear"></i> 设置
                            </button>
                        </li>
                    </ul>
                    
                    <div class="tab-content" id="pills-tabContent">
                        <!-- 控制面板 -->
                        <div class="tab-pane fade show active" id="pills-dashboard" role="tabpanel" aria-labelledby="pills-dashboard-tab">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5 class="mb-0"><i class="bi bi-lightning-charge"></i> 快速操作</h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="d-flex flex-wrap justify-content-center">
                                                <button class="btn btn-success control-btn">
                                                    <i class="bi bi-power"></i> 重启机器人
                                                </button>
                                                <button class="btn btn-warning control-btn">
                                                    <i class="bi bi-arrow-clockwise"></i> 刷新缓存
                                                </button>
                                                <button class="btn btn-danger control-btn">
                                                    <i class="bi bi-stop-circle"></i> 停止机器人
                                                </button>
                                                <button class="btn btn-info control-btn">
                                                    <i class="bi bi-broadcast"></i> 发送广播
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5 class="mb-0"><i class="bi bi-activity"></i> 系统状态</h5>
                                        </div>
                                        <div class="card-body">
                                            <div>
                                                <div class="d-flex justify-content-between">
                                                    <span>CPU 使用率</span>
                                                    <span>42%</span>
                                                </div>
                                                <div class="progress">
                                                    <div class="progress-bar bg-info" role="progressbar" style="width: 42%" aria-valuenow="42" aria-valuemin="0" aria-valuemax="100"></div>
                                                </div>
                                            </div>
                                            <div class="mt-3">
                                                <div class="d-flex justify-content-between">
                                                    <span>内存使用率</span>
                                                    <span>68%</span>
                                                </div>
                                                <div class="progress">
                                                    <div class="progress-bar bg-warning" role="progressbar" style="width: 68%" aria-valuenow="68" aria-valuemin="0" aria-valuemax="100"></div>
                                                </div>
                                            </div>
                                            <div class="mt-3">
                                                <div class="d-flex justify-content-between">
                                                    <span>数据库连接</span>
                                                    <span>活跃</span>
                                                </div>
                                                <div class="progress">
                                                    <div class="progress-bar bg-success" role="progressbar" style="width: 100%" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100"></div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row mt-4">
                                <div class="col-12">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5 class="mb-0"><i class="bi bi-info-circle"></i> 机器人信息</h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="table-responsive">
                                                <table class="table table-dark table-striped">
                                                    <tbody>
                                                        <tr>
                                                            <th scope="row" style="width: 30%;">用户名</th>
                                                            <td>@qunguan_bot</td>
                                                        </tr>
                                                        <tr>
                                                            <th scope="row">启动时间</th>
                                                            <td>{{ bot_start_time }}</td>
                                                        </tr>
                                                        <tr>
                                                            <th scope="row">API状态</th>
                                                            <td><span class="badge bg-success">正常</span></td>
                                                        </tr>
                                                        <tr>
                                                            <th scope="row">自动回复模式</th>
                                                            <td>{{ '仅管理员' if is_admin_only else '所有用户' }}</td>
                                                        </tr>
                                                        <tr>
                                                            <th scope="row">软件版本</th>
                                                            <td>v1.3.0</td>
                                                        </tr>
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 群组管理 -->
                        <div class="tab-pane fade" id="pills-groups" role="tabpanel" aria-labelledby="pills-groups-tab">
                            <div class="d-flex justify-content-between mb-3">
                                <h5>群组列表</h5>
                                <button class="btn btn-sm btn-primary">
                                    <i class="bi bi-plus-circle"></i> 添加群组
                                </button>
                            </div>
                            <div class="table-responsive">
                                <table class="table table-dark table-hover">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>群组编号</th>
                                            <th>群组名称</th>
                                            <th>群组链接</th>
                                            <th>操作</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for group in groups %}
                                        <tr>
                                            <td>{{ group.id }}</td>
                                            <td>{{ group.group_number }}</td>
                                            <td>{{ group.name }}</td>
                                            <td><a href="{{ group.link }}" target="_blank" class="text-info">{{ group.link }}</a></td>
                                            <td>
                                                <button class="btn btn-sm btn-warning"><i class="bi bi-pencil"></i></button>
                                                <button class="btn btn-sm btn-danger"><i class="bi bi-trash"></i></button>
                                            </td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                            <nav>
                                <ul class="pagination justify-content-center">
                                    <li class="page-item disabled">
                                        <a class="page-link" href="#" tabindex="-1">上一页</a>
                                    </li>
                                    <li class="page-item active"><a class="page-link" href="#">1</a></li>
                                    <li class="page-item"><a class="page-link" href="#">2</a></li>
                                    <li class="page-item"><a class="page-link" href="#">3</a></li>
                                    <li class="page-item">
                                        <a class="page-link" href="#">下一页</a>
                                    </li>
                                </ul>
                            </nav>
                        </div>
                        
                        <!-- 关键词管理 -->
                        <div class="tab-pane fade" id="pills-keywords" role="tabpanel" aria-labelledby="pills-keywords-tab">
                            <div class="d-flex justify-content-between mb-3">
                                <h5>关键词回复配置</h5>
                                <button class="btn btn-sm btn-primary">
                                    <i class="bi bi-plus-circle"></i> 添加关键词
                                </button>
                            </div>
                            <div class="table-responsive">
                                <table class="table table-dark table-hover">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>关键词</th>
                                            <th>回复内容</th>
                                            <th>状态</th>
                                            <th>操作</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for kr in keyword_responses %}
                                        <tr>
                                            <td>{{ kr.id }}</td>
                                            <td>{{ kr.keyword }}</td>
                                            <td>{{ kr.response[:30] }}{% if kr.response|length > 30 %}...{% endif %}</td>
                                            <td>
                                                <span class="badge {{ 'bg-success' if kr.is_active else 'bg-secondary' }}">
                                                    {{ '启用' if kr.is_active else '禁用' }}
                                                </span>
                                            </td>
                                            <td>
                                                <button class="btn btn-sm btn-warning"><i class="bi bi-pencil"></i></button>
                                                <button class="btn btn-sm btn-info"><i class="bi bi-toggle-on"></i></button>
                                                <button class="btn btn-sm btn-danger"><i class="bi bi-trash"></i></button>
                                            </td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        
                        <!-- 日志 -->
                        <div class="tab-pane fade" id="pills-logs" role="tabpanel" aria-labelledby="pills-logs-tab">
                            <div class="d-flex justify-content-between mb-3">
                                <h5>消息日志</h5>
                                <div>
                                    <button class="btn btn-sm btn-info me-2">
                                        <i class="bi bi-download"></i> 导出日志
                                    </button>
                                    <button class="btn btn-sm btn-danger">
                                        <i class="bi bi-trash"></i> 清除日志
                                    </button>
                                </div>
                            </div>
                            <div class="table-responsive">
                                <table class="table table-dark table-hover">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>时间</th>
                                            <th>群组</th>
                                            <th>用户</th>
                                            <th>消息</th>
                                            <th>触发关键词</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for log in message_logs %}
                                        <tr>
                                            <td>{{ log.id }}</td>
                                            <td>{{ log.processed_at.strftime('%Y-%m-%d %H:%M:%S') }}</td>
                                            <td>{{ log.chat_title }}</td>
                                            <td>{{ log.username }}</td>
                                            <td>{{ log.message_text[:30] }}{% if log.message_text|length > 30 %}...{% endif %}</td>
                                            <td>{{ log.trigger_keyword }}</td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                            <nav>
                                <ul class="pagination justify-content-center">
                                    <li class="page-item disabled">
                                        <a class="page-link" href="#" tabindex="-1">上一页</a>
                                    </li>
                                    <li class="page-item active"><a class="page-link" href="#">1</a></li>
                                    <li class="page-item"><a class="page-link" href="#">2</a></li>
                                    <li class="page-item"><a class="page-link" href="#">3</a></li>
                                    <li class="page-item">
                                        <a class="page-link" href="#">下一页</a>
                                    </li>
                                </ul>
                            </nav>
                        </div>
                        
                        <!-- 设置 -->
                        <div class="tab-pane fade" id="pills-settings" role="tabpanel" aria-labelledby="pills-settings-tab">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5 class="mb-0"><i class="bi bi-chat-quote"></i> 自动回复设置</h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="form-check form-switch mb-3">
                                                <input class="form-check-input" type="checkbox" id="adminOnlyMode" {{ 'checked' if is_admin_only else '' }}>
                                                <label class="form-check-label" for="adminOnlyMode">仅管理员模式</label>
                                                <small class="form-text text-muted d-block">当启用时，仅群组管理员触发的关键词会被回复</small>
                                            </div>
                                            <div class="mb-3">
                                                <label for="welcomeMessage" class="form-label">入群欢迎消息</label>
                                                <textarea class="form-control" id="welcomeMessage" rows="3">{{ welcome_message }}</textarea>
                                            </div>
                                            <div class="mb-3">
                                                <label for="privateChatWelcome" class="form-label">私聊欢迎消息</label>
                                                <textarea class="form-control" id="privateChatWelcome" rows="3">{{ private_chat_welcome }}</textarea>
                                            </div>
                                            <button class="btn btn-primary">保存设置</button>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card">
                                        <div class="card-header">
                                            <h5 class="mb-0"><i class="bi bi-shield-lock"></i> 安全设置</h5>
                                        </div>
                                        <div class="card-body">
                                            <div class="form-check form-switch mb-3">
                                                <input class="form-check-input" type="checkbox" id="enablePhoneVerification" checked>
                                                <label class="form-check-label" for="enablePhoneVerification">启用手机验证</label>
                                                <small class="form-text text-muted d-block">当启用时，用户需要通过手机验证才能获取群组信息</small>
                                            </div>
                                            <div class="mb-3">
                                                <label for="verificationCodeLength" class="form-label">验证码长度</label>
                                                <select class="form-select" id="verificationCodeLength">
                                                    <option value="4">4位数字</option>
                                                    <option value="6" selected>6位数字</option>
                                                    <option value="8">8位数字</option>
                                                </select>
                                            </div>
                                            <div class="mb-3">
                                                <label for="verificationCodeExpiry" class="form-label">验证码有效期（分钟）</label>
                                                <input type="number" class="form-control" id="verificationCodeExpiry" value="10">
                                            </div>
                                            <button class="btn btn-primary">保存设置</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card-footer text-center">
                    <small>© 2025 好旺公群机器人团队 | 版本 1.3.0</small>
                </div>
            </div>
        </div>
        
        <!-- JavaScript 依赖 -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // 初始化工具提示
            document.addEventListener('DOMContentLoaded', function() {
                // 获取所有tooltips
                var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
                var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
                    return new bootstrap.Tooltip(tooltipTriggerEl)
                })
            });
        </script>
    </body>
    </html>
    """
    
    # 获取数据库数据用于显示
    from models import Group, Keyword, KeywordResponse, Channel, MessageLog, BotSettings, PhoneVerification
    
    # 分页显示，每页10条数据
    page = 1
    per_page = 10
    
    # 获取最新的10条消息日志
    message_logs = MessageLog.query.order_by(MessageLog.processed_at.desc()).limit(per_page).all()
    
    # 获取群组总数
    groups = Group.query.order_by(Group.group_number).limit(per_page).all()
    
    # 获取关键词回复
    keyword_responses = KeywordResponse.query.all()
    
    # 获取机器人设置
    bot_settings = BotSettings.query.first()
    is_admin_only = True
    welcome_message = ""
    private_chat_welcome = ""
    
    if bot_settings:
        is_admin_only = bot_settings.is_admin_only
        welcome_message = bot_settings.welcome_message
        private_chat_welcome = bot_settings.private_chat_welcome
    
    # 获取已验证手机号的数量
    phone_verifications_count = PhoneVerification.query.filter_by(is_verified=True).count()
    
    # 格式化机器人启动时间
    bot_start_time = bot_status["started_at"].strftime("%Y-%m-%d %H:%M:%S") if bot_status["started_at"] else "未知"
    
    return render_template_string(
        html, 
        status=status_text, 
        uptime=uptime, 
        messages=bot_status["messages_processed"],
        groups=groups,
        message_logs=message_logs,
        keyword_responses=keyword_responses,
        is_admin_only=is_admin_only,
        welcome_message=welcome_message,
        private_chat_welcome=private_chat_welcome,
        phone_verifications=phone_verifications_count,
        bot_start_time=bot_start_time
    )

# 导入并初始化数据库模型
with app.app_context():
    # 导入模型
    import models
    from models import Group, Keyword, KeywordResponse, Channel, MessageLog, BotSettings
    
    # 创建数据库表
    db.create_all()
    
    # 检查并初始化基本设置
    def init_default_data():
        # 初始化机器人设置
        if not BotSettings.query.first():
            from config import PRIVATE_CHAT_WELCOME, DEFAULT_WELCOME_MESSAGE, CHANNEL_INFO
            default_settings = BotSettings(
                welcome_message=DEFAULT_WELCOME_MESSAGE,
                private_chat_welcome=PRIVATE_CHAT_WELCOME,
                channel_info=CHANNEL_INFO,
                is_admin_only=True
            )
            db.session.add(default_settings)
            
        # 初始化关键词回复
        if KeywordResponse.query.count() == 0:
            from config import ADDITIONAL_KEYWORD_RESPONSES
            for keyword, response in ADDITIONAL_KEYWORD_RESPONSES.items():
                kr = KeywordResponse(keyword=keyword, response=response)
                db.session.add(kr)
            
        # 初始化频道信息
        if Channel.query.count() == 0:
            channels = [
                {"name": "好旺公群", "username": "hwgq", "link": "https://t.me/hwgq", "display_order": 1},
                {"name": "供求信息", "username": "hwtb2", "link": "https://t.me/hwtb2", "display_order": 2},
                {"name": "新开公群", "username": "xinqun", "link": "https://t.me/xinqun", "display_order": 3},
                {"name": "核心大群", "username": "daqun", "link": "https://t.me/daqun", "display_order": 4},
                {"name": "防骗指南", "username": "hwtb22", "link": "https://t.me/hwtb22", "display_order": 5},
                {"name": "担保教程", "username": "hwtb33", "link": "https://t.me/hwtb33", "display_order": 6},
                {"name": "联系好旺担保", "username": "hwdb", "link": "https://t.me/hwdb", "display_order": 7}
            ]
            for channel_data in channels:
                channel = Channel(**channel_data)
                db.session.add(channel)
        
        # 初始化群组数据
        if Group.query.count() == 0:
            from config import GROUP_DATABASE
            for group_number, group_data in GROUP_DATABASE["数字编号"].items():
                group = Group(
                    group_number=group_number,
                    name=group_data["name"],
                    link=group_data["link"],
                    description=group_data["description"]
                )
                db.session.add(group)
                
                # 提交以获取ID
                db.session.flush()
                
                # 查找关联的关键词
                for word, group_numbers in GROUP_DATABASE["关键词"].items():
                    if group_number in group_numbers:
                        # 检查关键词是否存在，不存在则创建
                        keyword = Keyword.query.filter_by(word=word).first()
                        if not keyword:
                            keyword = Keyword(word=word)
                            db.session.add(keyword)
                            db.session.flush()
                        
                        # 将关键词与群组关联
                        if keyword not in group.keywords:
                            group.keywords.append(keyword)
        
        # 提交所有更改
        db.session.commit()
    
    # 初始化默认数据
    init_default_data()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)