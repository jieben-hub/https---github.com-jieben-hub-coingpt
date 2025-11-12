# -*- coding: utf-8 -*-
"""
添加活动表迁移脚本
"""
from sqlalchemy import text
from models import db

def upgrade():
    """创建活动表"""
    # 创建活动表
    db.session.execute(text("""
    CREATE TABLE IF NOT EXISTS activities (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        title VARCHAR(255) NOT NULL,
        description TEXT NOT NULL,
        start_time DATETIME NOT NULL,
        end_time DATETIME NOT NULL,
        is_active BOOLEAN DEFAULT TRUE NOT NULL,
        priority INT DEFAULT 0 NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """))
    db.session.commit()
    print("活动表创建成功")

def downgrade():
    """删除活动表"""
    db.session.execute(text("DROP TABLE IF EXISTS activities"))
    db.session.commit()
    print("活动表删除成功")

if __name__ == '__main__':
    # 直接运行时的测试代码
    from app import create_app
    app = create_app()
    with app.app_context():
        upgrade()
        print("数据库迁移完成")