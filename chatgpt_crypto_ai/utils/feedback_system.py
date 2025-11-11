# -*- coding: utf-8 -*-
"""
对话反馈和评分系统，用于收集用户反馈并改进系统响应质量
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# 导入数据库模型
from models import db, SessionFeedback, MessageFeedback
from utils.utf8_validator import UTF8Validator

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('feedback_system')

class FeedbackSystem:
    """
    对话反馈系统，用于收集用户对回复的评分和反馈，并用于系统自我改进
    """
    
    # 反馈数据存储路径
    FEEDBACK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'feedback')
    
    # 确保反馈目录存在
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    
    @staticmethod
    def save_feedback(session_id: str, conversation_id: str, user_id: str, 
                     rating: int, feedback_text: Optional[str] = None, 
                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        保存用户对特定对话的反馈
        
        Args:
            session_id: 会话ID
            conversation_id: 对话ID
            user_id: 用户ID
            rating: 评分(1-5)
            feedback_text: 文字反馈(可选)
            context: 相关上下文信息(可选)，如币种、意图等
            
        Returns:
            Dict: 包含操作结果的字典
        """
        try:
            # 验证评分范围
            if rating < 1 or rating > 5:
                return {"status": "error", "message": "评分必须在1-5之间"}
            
            # 准备反馈数据并清理UTF-8字符
            feedback_data = {
                "session_id": session_id,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "rating": rating,
                "feedback_text": UTF8Validator.clean_string(feedback_text) if feedback_text else None,
                "context": UTF8Validator.validate_json_data(context or {}),
                "timestamp": datetime.now().isoformat()
            }
            
            # 1. 保存到数据库
            try:
                # 转换ID为整数
                session_id_int = int(session_id)
                user_id_int = int(user_id)
                
                # 调用数据库模型保存评分
                db_result = SessionFeedback.save_feedback(
                    session_id=session_id_int,
                    user_id=user_id_int,
                    rating=rating,
                    feedback_text=feedback_text,
                    context=context
                )
                
                logger.info(f"已保存会话评分到数据库: session_id={session_id}, rating={rating}")
                
            except Exception as db_error:
                logger.error(f"保存评分到数据库时出错: {db_error}")
                # 数据库保存失败不影响文件保存
            
            # 2. 保存到文件系统（作为备份）
            filename = f"{session_id}_{conversation_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            filepath = os.path.join(FeedbackSystem.FEEDBACK_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(UTF8Validator.safe_json_dumps(feedback_data, indent=2))
                
            logger.info(f"已保存用户反馈到文件: {filepath}")
            
            return {
                "status": "success", 
                "message": "反馈已保存", 
                "file": filepath,
                "db_saved": db_result["status"] == "success" if "db_result" in locals() else False
            }
            
        except Exception as e:
            logger.error(f"保存反馈时出错: {e}")
            return {"status": "error", "message": f"保存反馈失败: {e}"}
    
    @staticmethod
    def get_session_feedback(session_id: str) -> List[Dict[str, Any]]:
        """
        获取特定会话的所有反馈
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[Dict]: 包含会话所有反馈的列表
        """
        feedbacks = []
        
        try:
            # 遍历反馈目录
            for filename in os.listdir(FeedbackSystem.FEEDBACK_DIR):
                if filename.startswith(f"{session_id}_") and filename.endswith(".json"):
                    filepath = os.path.join(FeedbackSystem.FEEDBACK_DIR, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        feedback_data = json.load(f)
                        feedbacks.append(feedback_data)
                        
            return feedbacks
        
        except Exception as e:
            logger.error(f"获取会话反馈时出错: {e}")
            return []
    
    @staticmethod
    def analyze_feedback(session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        分析反馈数据，生成统计报告
        
        Args:
            session_id: 可选的会话ID，如果提供则只分析该会话的反馈
            
        Returns:
            Dict: 包含反馈分析结果的字典
        """
        try:
            all_feedbacks = []
            
            # 收集反馈数据
            if session_id:
                all_feedbacks = FeedbackSystem.get_session_feedback(session_id)
            else:
                # 遍历所有反馈文件
                for filename in os.listdir(FeedbackSystem.FEEDBACK_DIR):
                    if filename.endswith(".json"):
                        filepath = os.path.join(FeedbackSystem.FEEDBACK_DIR, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            feedback_data = json.load(f)
                            all_feedbacks.append(feedback_data)
            
            if not all_feedbacks:
                return {"status": "info", "message": "没有找到反馈数据"}
            
            # 计算统计数据
            total_count = len(all_feedbacks)
            rating_sum = sum(fb["rating"] for fb in all_feedbacks)
            avg_rating = rating_sum / total_count if total_count > 0 else 0
            
            # 按评分分组
            rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for fb in all_feedbacks:
                rating = fb["rating"]
                rating_distribution[rating] = rating_distribution.get(rating, 0) + 1
            
            # 分析上下文数据
            context_analysis = {}
            for fb in all_feedbacks:
                context = fb.get("context", {})
                for key, value in context.items():
                    if key not in context_analysis:
                        context_analysis[key] = {}
                    
                    str_value = str(value)
                    if str_value not in context_analysis[key]:
                        context_analysis[key][str_value] = {"count": 0, "total_rating": 0}
                    
                    context_analysis[key][str_value]["count"] += 1
                    context_analysis[key][str_value]["total_rating"] += fb["rating"]
            
            # 计算每个上下文值的平均评分
            for key in context_analysis:
                for value in context_analysis[key]:
                    count = context_analysis[key][value]["count"]
                    total = context_analysis[key][value]["total_rating"]
                    context_analysis[key][value]["avg_rating"] = total / count if count > 0 else 0
            
            return {
                "status": "success",
                "total_feedbacks": total_count,
                "average_rating": avg_rating,
                "rating_distribution": rating_distribution,
                "context_analysis": context_analysis
            }
            
        except Exception as e:
            logger.error(f"分析反馈数据时出错: {e}")
            return {"status": "error", "message": f"分析反馈失败: {e}"}
    
    @staticmethod
    def save_message_feedback(message_id: str, user_id: str, rating: int, 
                           feedback_text: Optional[str] = None) -> Dict[str, Any]:
        """
        保存用户对单条AI回复消息的评分
        
        Args:
            message_id: 消息ID
            user_id: 用户ID
            rating: 评分(1-5)
            feedback_text: 文字反馈(可选)
            
        Returns:
            Dict: 包含操作结果的字典
        """
        try:
            # 验证评分范围
            if rating < 1 or rating > 5:
                return {"status": "error", "message": "评分必须在1-5之间"}
            
            # 准备反馈数据
            feedback_data = {
                "message_id": message_id,
                "user_id": user_id,
                "rating": rating,
                "feedback_text": feedback_text,
                "timestamp": datetime.now().isoformat()
            }
            
            # 1. 保存到数据库
            try:
                # 转换ID为整数
                message_id_int = int(message_id)
                user_id_int = int(user_id)
                
                # 调用数据库模型保存评分
                db_result = MessageFeedback.save_feedback(
                    message_id=message_id_int,
                    user_id=user_id_int,
                    rating=rating,
                    feedback_text=feedback_text
                )
                
                logger.info(f"已保存消息评分到数据库: message_id={message_id}, rating={rating}")
                
            except Exception as db_error:
                logger.error(f"保存消息评分到数据库时出错: {db_error}")
                # 数据库保存失败不影响文件保存
            
            # 2. 保存到文件系统（作为备份）
            filename = f"msg_{message_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            filepath = os.path.join(FeedbackSystem.FEEDBACK_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(feedback_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"已保存消息评分到文件: {filepath}")
            
            return {
                "status": "success", 
                "message": "消息评分已保存", 
                "file": filepath,
                "db_saved": db_result["status"] == "success" if "db_result" in locals() else False
            }
            
        except Exception as e:
            logger.error(f"保存消息评分时出错: {e}")
            return {"status": "error", "message": f"保存消息评分失败: {e}"}
    
    @staticmethod
    def get_improvement_suggestions(recent_count: int = 10) -> List[Dict[str, Any]]:
        """
        基于最近的低评分反馈，生成改进建议
        
        Args:
            recent_count: 考虑的最近反馈数量
            
        Returns:
            List[Dict]: 改进建议列表
        """
        try:
            # 获取所有反馈文件并按时间排序
            feedback_files = []
            for filename in os.listdir(FeedbackSystem.FEEDBACK_DIR):
                if filename.endswith(".json"):
                    filepath = os.path.join(FeedbackSystem.FEEDBACK_DIR, filename)
                    file_stat = os.stat(filepath)
                    feedback_files.append((filepath, file_stat.st_mtime))
            
            # 按修改时间排序，最新的在前
            feedback_files.sort(key=lambda x: x[1], reverse=True)
            
            # 获取最近的反馈
            recent_feedbacks = []
            for filepath, _ in feedback_files[:recent_count]:
                with open(filepath, 'r', encoding='utf-8') as f:
                    feedback_data = json.load(f)
                    recent_feedbacks.append(feedback_data)
            
            # 筛选低评分反馈(评分<=3)
            low_rating_feedbacks = [fb for fb in recent_feedbacks if fb["rating"] <= 3]
            
            # 生成改进建议
            suggestions = []
            for fb in low_rating_feedbacks:
                context = fb.get("context", {})
                feedback_text = fb.get("feedback_text", "")
                
                suggestion = {
                    "rating": fb["rating"],
                    "timestamp": fb["timestamp"],
                    "context": context,
                    "feedback": feedback_text,
                    "suggestion": "需要改进的领域"
                }
                
                # 根据上下文和反馈生成具体建议
                if "intent" in context:
                    intent = context["intent"]
                    if intent == "analyze":
                        suggestion["suggestion"] = "改进分析质量和深度"
                    elif intent == "trade":
                        suggestion["suggestion"] = "提高交易建议的准确性和实用性"
                    elif intent == "monitor":
                        suggestion["suggestion"] = "确保价格和市场数据的准确性和及时性"
                    elif intent == "chat":
                        suggestion["suggestion"] = "提高聊天回复的相关性和自然度"
                
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"生成改进建议时出错: {e}")
            return []
