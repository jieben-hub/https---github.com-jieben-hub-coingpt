"""
运行数据库迁移的脚本
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入应用和迁移函数
from chatgpt_crypto_ai.app import create_app
from flask_migrate import upgrade

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # 应用所有未应用的迁移
        upgrade()
        print("数据库迁移完成！")
