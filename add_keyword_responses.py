#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
添加关键词回复到数据库
这个脚本用于将 config.py 中的关键词回复添加到数据库
"""

import logging
from app import app, db
from models import KeywordResponse
from config import ADDITIONAL_KEYWORD_RESPONSES

# 设置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_keyword_responses_to_database():
    """添加关键词回复到数据库"""
    with app.app_context():
        # 检查数据库连接
        try:
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return False
        
        responses_added = 0
        responses_updated = 0
        
        # 添加关键词回复
        for keyword, response in ADDITIONAL_KEYWORD_RESPONSES.items():
            # 检查关键词是否已存在
            existing_response = KeywordResponse.query.filter_by(keyword=keyword).first()
            
            if existing_response:
                logger.info(f"更新已存在的关键词回复: {keyword}")
                # 更新现有关键词回复
                existing_response.response = response
                existing_response.is_active = True
                responses_updated += 1
            else:
                logger.info(f"添加新关键词回复: {keyword}")
                # 创建新关键词回复
                new_response = KeywordResponse(
                    keyword=keyword,
                    response=response,
                    is_active=True
                )
                db.session.add(new_response)
                responses_added += 1
        
        # 提交所有更改
        db.session.commit()
        logger.info(f"成功添加 {responses_added} 个新关键词回复，更新 {responses_updated} 个已存在的回复")
        return True

if __name__ == "__main__":
    logger.info("开始添加关键词回复...")
    success = add_keyword_responses_to_database()
    if success:
        logger.info("关键词回复添加完成!")
    else:
        logger.error("添加关键词回复时出错!")