#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
添加好旺公群数据到数据库
这个脚本用于从hwtb2频道获取并添加公群数据
"""

import os
import logging
from app import app, db
from models import Group, Keyword

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 好旺公群数据 - 从https://t.me/hwgq和https://t.me/hwtb2频道获取
GROUPS_DATA = [
    # 格式：群号，群名，链接，描述，关键词列表
    {
        "group_number": "1001",
        "name": "万利国际集团",
        "link": "https://t.me/wlgp0",
        "description": "万利国际集团官方公群，提供全球金融服务，支付接口，虚拟资产交易，投资理财，顶级交易平台。24小时专业客服在线服务。",
        "keywords": ["万利国际", "万利集团", "国际金融", "支付接口", "虚拟资产", "交易平台", "官方公群", "投资理财"]
    },
    {
        "group_number": "1096",
        "name": "公群1096",
        "link": "https://t.me/+j-t956sDejs3NGU0",
        "description": "万利集团一道码接口，本公群主营/微信支付宝个人码经营/银行直拉/网关/群引导/各种下载付/花呗信用卡/一切丝滑入金通道！",
        "keywords": ["钱钱", "万利", "支付", "个人码", "银行直拉", "网关", "群引导", "下载付", "花呗", "信用卡"]
    },
    {
        "group_number": "888",
        "name": "公群888",
        "link": "https://t.me/+UVZStkCnG4lmM2Y1",
        "description": "好旺平台旗下公群，专为卡商提供资源对接，各种卡，任何POS机，金融服务，商户直营！",
        "keywords": ["卡商", "POS机", "金融服务", "商户", "好旺平台"]
    },
    {
        "group_number": "777",
        "name": "公群777",
        "link": "https://t.me/+gUVL0Y_ZBn5lOTY1",
        "description": "代收代付专用公群，支持USDT、支付宝、微信、银行卡等各种入款方式，24小时客服在线！",
        "keywords": ["代收", "代付", "USDT", "支付宝", "微信", "银行卡", "入款"]
    },
    {
        "group_number": "666",
        "name": "白资公群666",
        "link": "https://t.me/+K8LH-LD1Q1RjNWU1",
        "description": "专业白资服务公群，提供优质白资，大量收白资，价格实惠，长期合作！",
        "keywords": ["白资", "收白资", "白资公群"]
    },
    {
        "group_number": "555",
        "name": "承兑公群555",
        "link": "https://t.me/+gPR0ShXGQwZiNDFl",
        "description": "专业USDT/RMB互换承兑公群，价格优惠，安全可靠，大量长期收U！",
        "keywords": ["承兑", "USDT", "RMB", "收U", "互换"]
    },
    {
        "group_number": "444",
        "name": "换汇公群444",
        "link": "https://t.me/+FkJQzVjvvCU3YTVl",
        "description": "专业换汇公群，全球货币兑换，支持美元、欧元、港币、日元等，汇率优惠！",
        "keywords": ["换汇", "货币兑换", "美元", "欧元", "港币", "日元"]
    },
    {
        "group_number": "333",
        "name": "包网公群333",
        "link": "https://t.me/+Lqz_gLcITvkzMWNl",
        "description": "专业包网公群，提供各类博彩、游戏、娱乐网站搭建，技术支持，运营指导！",
        "keywords": ["包网", "网站搭建", "博彩", "游戏", "娱乐网站"]
    },
    {
        "group_number": "222",
        "name": "技术公群222",
        "link": "https://t.me/+abMxEh_yqU8xZThl",
        "description": "各类技术服务公群，提供网站开发、APP开发、支付接口开发、区块链开发等服务！",
        "keywords": ["技术", "网站开发", "APP开发", "支付接口", "区块链"]
    },
    {
        "group_number": "111",
        "name": "公群111",
        "link": "https://t.me/+TSLHD-6jUGA2MGZl",
        "description": "好旺平台总群，各类资源汇总，需求对接，助力您的业务发展！",
        "keywords": ["好旺", "平台", "资源", "需求对接", "业务发展"]
    },
    # 添加更多从hwgq频道获取的群组
    {
        "group_number": "999",
        "name": "金融公群999",
        "link": "https://t.me/+KjHxRnlp3Vw2ZDFl",
        "description": "专业金融服务公群，提供各类贷款、理财、保险等金融产品咨询和办理服务。",
        "keywords": ["金融", "贷款", "理财", "保险", "金融产品"]
    },
    {
        "group_number": "621",
        "name": "支付公群621",
        "link": "https://t.me/+PqR2VxJf9hkzNjY1",
        "description": "专业支付通道公群，提供各类收款码、跑分平台、四方支付接口等服务。",
        "keywords": ["支付", "收款码", "跑分", "四方支付", "支付接口"]
    },
    {
        "group_number": "520",
        "name": "招商公群520",
        "link": "https://t.me/+LmH4o5w2qXQzMTVl",
        "description": "招商引流专用公群，提供各类合作机会，招代理、招商户、诚邀各界人士加入。",
        "keywords": ["招商", "引流", "代理", "合作", "招商引流"]
    },
    {
        "group_number": "188",
        "name": "棋牌公群188",
        "link": "https://t.me/+TjQqF6zTK642YzE1",
        "description": "专业棋牌游戏公群，提供各类棋牌游戏资源，技术支持，玩家交流。",
        "keywords": ["棋牌", "游戏", "棋牌游戏", "玩家", "技术支持"]
    },
    {
        "group_number": "168",
        "name": "资源公群168",
        "link": "https://t.me/+CfPLlpzT_NY3MTJl",
        "description": "综合资源公群，提供各类互联网资源，吃瓜爆料，实时热点，最新资讯。",
        "keywords": ["资源", "互联网", "吃瓜", "热点", "资讯"]
    },
    {
        "group_number": "158",
        "name": "交易公群158",
        "link": "https://t.me/+NwKhjXQS8483ZjVl",
        "description": "专业交易公群，提供各类虚拟资产交易，币圈交流，投资理财。",
        "keywords": ["交易", "虚拟资产", "币圈", "投资", "理财"]
    },
    {
        "group_number": "128",
        "name": "电影公群128",
        "link": "https://t.me/+HgTHxF5jR7E3NzFl",
        "description": "电影资源分享公群，提供最新电影、电视剧、动漫、综艺节目资源。",
        "keywords": ["电影", "资源", "电视剧", "动漫", "综艺"]
    },
    {
        "group_number": "118",
        "name": "娱乐公群118",
        "link": "https://t.me/+XqSvMqZ4tYY0MDY1",
        "description": "综合娱乐公群，提供各类娱乐资源，游戏交流，社交互动。",
        "keywords": ["娱乐", "游戏", "社交", "互动", "娱乐资源"]
    },
    {
        "group_number": "998",
        "name": "跑分公群998",
        "link": "https://t.me/+ZhTnL6HjlJY4YjJl",
        "description": "专业跑分公群，提供高价跑分、稳定通道、实时结算、7*24小时客服。",
        "keywords": ["跑分", "高价", "稳定通道", "实时结算", "客服"]
    },
    {
        "group_number": "996",
        "name": "信用卡公群996",
        "link": "https://t.me/+QjTgUp8L5xI2NDFl",
        "description": "信用卡业务专用公群，提供各类信用卡办理、代还、提额、养卡等服务。",
        "keywords": ["信用卡", "办卡", "代还", "提额", "养卡"]
    }
]

def add_groups_to_database():
    """添加群组数据到数据库"""
    with app.app_context():
        # 检查数据库连接
        try:
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return False
        
        groups_added = 0
        keywords_added = 0
        
        # 添加群组
        for group_data in GROUPS_DATA:
            # 检查群组是否已存在
            existing_group = Group.query.filter_by(group_number=group_data["group_number"]).first()
            
            if existing_group:
                logger.info(f"更新已存在的群组: {group_data['group_number']} - {group_data['name']}")
                # 更新现有群组信息
                existing_group.name = group_data["name"]
                existing_group.link = group_data["link"]
                existing_group.description = group_data["description"]
            else:
                logger.info(f"添加新群组: {group_data['group_number']} - {group_data['name']}")
                # 创建新群组
                new_group = Group(
                    group_number=group_data["group_number"],
                    name=group_data["name"],
                    link=group_data["link"],
                    description=group_data["description"]
                )
                db.session.add(new_group)
                groups_added += 1
                
                # 需要先提交以获取group_id
                db.session.commit()
                
                # 处理关键词
                if "keywords" in group_data and group_data["keywords"]:
                    group_obj = Group.query.filter_by(group_number=group_data["group_number"]).first()
                    
                    if group_obj:
                        for kw_text in group_data["keywords"]:
                            # 检查关键词是否存在
                            keyword = Keyword.query.filter_by(word=kw_text).first()
                            
                            if not keyword:
                                # 创建新关键词
                                keyword = Keyword(word=kw_text)
                                db.session.add(keyword)
                                keywords_added += 1
                                db.session.commit()
                            
                            # 将关键词与群组关联
                            if keyword not in group_obj.keywords:
                                group_obj.keywords.append(keyword)
        
        # 最终提交所有更改
        db.session.commit()
        logger.info(f"成功添加 {groups_added} 个新群组和 {keywords_added} 个新关键词")
        return True

if __name__ == "__main__":
    logger.info("开始添加群组数据...")
    success = add_groups_to_database()
    if success:
        logger.info("群组数据添加完成!")
    else:
        logger.error("添加群组数据时出错!")