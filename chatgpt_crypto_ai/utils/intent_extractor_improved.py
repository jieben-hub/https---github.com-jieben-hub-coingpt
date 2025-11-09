# -*- coding: utf-8 -*-
"""
从用户输入中提取币种、时间框架和意图的模块
"""
from typing import Dict, Any, List, Optional
import json
import logging
import os
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('intent_extractor')

# 加载OpenAI API密钥
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("未找到OPENAI_API_KEY环境变量")

# 初始化OpenAI客户端
client = OpenAI(api_key=OPENAI_API_KEY)

# 意图类型
INTENT_TYPES = {
    "analyze": "分析",  # K线分析
    "trade": "交易",    # 买卖建议
    "monitor": "监控",   # 价格监控
    "chat": "聊天"      # 普通聊天
}

class IntentExtractor:
    """
    使用OpenAI API从用户输入中提取意图、币种和时间框架
    """
    
    @staticmethod
    def build_intent_prompt(user_input: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """
        构建用于意图提取的prompt
        
        Args:
            user_input: 用户输入的文本
            conversation_history: 对话历史记录
        
        Returns:
            str: 用于意图提取的prompt
        """
        # 准备对话历史上下文文本
        context_text = ""
        previously_mentioned_coins = []
        
        if conversation_history and len(conversation_history) > 0:
            # 最多取最近10轮对话作为上下文
            recent_history = conversation_history[-10:]
            context_text = "\n以下是最近的对话历史（用于理解上下文）：\n"
            
            # 第一次扫描，提取可能提到的币种
            for msg in recent_history:
                if msg["role"] == "user":
                    # 简单的币种检测逻辑，查找常见币种符号
                    content = msg["content"].upper()
                    for coin in ["BTC", "ETH", "SOL", "XRP", "ADA", "DOT", "DOGE", "SHIB", "AVAX", "MATIC"]:
                        if coin in content or coin.lower() in content.lower():
                            previously_mentioned_coins.append(coin)
                    # 检查全名
                    coin_names = {"比特币": "BTC", "以太坊": "ETH", "索拉纳": "SOL", "瑞波币": "XRP"}
                    for name, symbol in coin_names.items():
                        if name in msg["content"]:
                            previously_mentioned_coins.append(symbol)
            
            # 添加对话历史
            for msg in recent_history:
                role = "用户" if msg["role"] == "user" else "助手"
                context_text += f"{role}: {msg['content']}\n"
            
            # 强化上下文理解指导
            context_text += "\n【重要】基于以上对话历史和当前用户输入提取信息。特别注意：\n"
            context_text += "1. 如果当前输入中使用代词（如'它'、'这个币'、'这个'等）指代之前提到的币种，必须从历史中找出对应币种。\n"
            context_text += "2. 如果用户提到'现货'、'期货'、'合约'等交易类型但未指明币种，应假定用户指的是之前讨论的币种。\n"
            
            # 添加之前提到的币种信息
            if previously_mentioned_coins:
                unique_coins = list(dict.fromkeys(previously_mentioned_coins))  # 去重
                context_text += f"3. 对话中已明确提到的币种: {', '.join(unique_coins)}\n"
                context_text += f"4. 如果当前输入没有明确指定币种，但与加密货币交易或分析相关，默认使用最近提到的币种: {unique_coins[-1]}\n"
        
        # 构建提示
        prompt = f"""你是一个专业的加密货币分析助手，擅长处理中文输入和多轮对话。请从用户输入和对话历史中精准提取以下信息：

1. 币种（如BTC、ETH、SOL、ADA等）。
2. 时间框架（如1小时、4小时、日线、周线，若未指定，默认1小时）。
3. 意图（以下四种类型）：
   - analyze: 分析K线、趋势、技术指标、行情走势等
   - trade: 交易建议、买卖时机、入场点位、止损位置等
   - monitor: 仅询问当前价格、涨跌幅等简单信息
   - chat: 一般性聊天或加密货币教育问题，如概念解释等

【重要判断规则】
1. 上下文连贯性是首要考虑因素。如果当前消息提到"现货"、"期货"、"合约"等但未指明币种，应从对话历史中推断用户指的是哪种币。
2. 如果用户使用"它"、"这个"、"这种币"等代词，必须从历史中找出对应币种。
3. 优先根据动词和需求词判断意图（如"分析"→analyze，"值不值得买"→trade，"多少钱"→monitor）。
4. 如果用户输入与加密货币完全无关，且历史中也没有提到过任何币种，才将intent设为"chat"。
5. 即使识别出币种，如果问题是关于概念解释或教育性内容，也应判断为chat类型。

【示例】
- 输入: "BTC最近走势如何" → {{"coin": "BTC", "timeframe": "1h", "intent": "analyze", "confidence": 0.95}}
- 输入: "以太坊现在值得买入吗" → {{"coin": "ETH", "timeframe": "1h", "intent": "trade", "confidence": 0.9}}
- 输入: "它现在多少价格" (历史提到BTC) → {{"coin": "BTC", "timeframe": null, "intent": "monitor", "confidence": 0.8}}
- 输入: "现货值得入手吗" (历史提到BTC) → {{"coin": "BTC", "timeframe": "1h", "intent": "trade", "confidence": 0.85}}
- 输入: "看看4小时图" (历史提到SOL) → {{"coin": "SOL", "timeframe": "4h", "intent": "analyze", "confidence": 0.85}}
- 输入: "这个币最近表现如何" (历史提到ETH) → {{"coin": "ETH", "timeframe": "1h", "intent": "analyze", "confidence": 0.8}}

{context_text}
输出严格的JSON格式：
{{
  "coin": "币种或null",
  "timeframe": "时间框架（如1h、4h、1d、1w）或null",
  "intent": "意图（analyze、trade、monitor、chat）",
  "error": "错误信息（如果有）",
  "confidence": "介于0.0-1.0之间的数字，表示对判断的信心程度"
}}

当前用户输入：{user_input}"""
        
        return prompt
        
    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def extract_intent(user_input: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        从用户输入中提取币种、时间框架和意图，支持多轮对话上下文
        
        Args:
            user_input: 用户输入的文本
            conversation_history: 对话历史记录，格式为[{"role": "user"|"assistant", "content": "消息内容"}]
            
        Returns:
            Dict: 包含提取信息的字典，格式如下:
            {
                "coin": 币种符号或null,
                "timeframe": 时间框架或null,
                "intent": 意图类型或null,
                "error": 错误信息或null
            }
        """
        try:
            # 使用帮助函数构建提示
            prompt = IntentExtractor.build_intent_prompt(user_input, conversation_history)

            # 调用OpenAI API
            logger.info(f"正在从用户输入中提取意图: {user_input}")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专注于提取加密货币相关信息的AI助手。你只输出JSON格式的结果。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 低温度以获得更确定的结果
                max_tokens=200    # 限制token以获得简洁结果
            )
            
            # 提取回复内容
            reply_content = response.choices[0].message.content
            logger.info(f"GPT提取结果: {reply_content}")
            
            # 尝试解析JSON
            try:
                # 处理可能包含的代码块标记
                if "```json" in reply_content:
                    json_start = reply_content.find("```json") + 7
                    json_end = reply_content.find("```", json_start)
                    json_content = reply_content[json_start:json_end].strip()
                    extracted_data = json.loads(json_content)
                elif "```" in reply_content:
                    json_start = reply_content.find("```") + 3
                    json_end = reply_content.find("```", json_start)
                    json_content = reply_content[json_start:json_end].strip()
                    extracted_data = json.loads(json_content)
                else:
                    # 直接尝试解析整个内容
                    extracted_data = json.loads(reply_content)
                
                # 规范化输出
                result = {
                    "coin": extracted_data.get("coin"),
                    "timeframe": extracted_data.get("timeframe"),
                    "intent": extracted_data.get("intent"),
                    "error": extracted_data.get("error"),
                    "confidence": extracted_data.get("confidence", 0.8)  # 默认值为0.8
                }
                
                logger.info(f"成功提取意图: {result}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析错误: {e}")
                return {
                    "coin": None,
                    "timeframe": None,
                    "intent": "chat",  # 默认回退到聊天模式
                    "error": f"无法解析GPT返回的JSON: {e}",
                    "confidence": 0.3  # 低置信度
                }
                
        except Exception as e:
            logger.error(f"意图提取过程中出现错误: {e}")
            return {
                "coin": None,
                "timeframe": None,
                "intent": "chat",  # 默认回退到聊天模式
                "error": f"意图提取失败: {e}",
                "confidence": 0.2  # 非常低的置信度
            }
