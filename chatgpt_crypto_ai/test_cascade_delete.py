# -*- coding: utf-8 -*-
"""
测试级联删除功能
"""
from app import create_app
from models import db, Session, Message, MessageFeedback

app = create_app()

with app.app_context():
    print("测试级联删除功能")
    print("=" * 80)
    
    # 查找一个有反馈的消息
    message_with_feedback = db.session.query(Message).join(
        MessageFeedback, Message.id == MessageFeedback.message_id
    ).first()
    
    if message_with_feedback:
        message_id = message_with_feedback.id
        session_id = message_with_feedback.session_id
        
        # 查询该消息的反馈数量
        feedback_count = db.session.query(MessageFeedback).filter_by(
            message_id=message_id
        ).count()
        
        print(f"找到消息 ID: {message_id}")
        print(f"该消息有 {feedback_count} 条反馈记录")
        print(f"所属会话 ID: {session_id}")
        
        # 测试删除消息
        print(f"\n尝试删除消息 {message_id}...")
        
        try:
            db.session.delete(message_with_feedback)
            db.session.commit()
            
            # 验证反馈是否被删除
            remaining_feedback = db.session.query(MessageFeedback).filter_by(
                message_id=message_id
            ).count()
            
            print(f"✅ 消息删除成功！")
            print(f"✅ 相关反馈记录已自动删除（剩余 {remaining_feedback} 条）")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 删除失败: {e}")
            
    else:
        print("⚠ 未找到有反馈记录的消息，无法测试")
        print("\n提示: 可以先创建一些测试数据")
    
    print("\n" + "=" * 80)
    print("测试完成！")
