# -*- coding: utf-8 -*-
"""
构造OpenAI GPT模型的输入消息模块
"""
from typing import Dict, List, Any, Optional
import pandas as pd
import json

class PromptConstructor:
    """
    负责构造发送给GPT模型的提示
    """
    
    @staticmethod
    def construct_system_message(intent: str = "analyze") -> Dict[str, str]:
        """
        根据意图构造GPT系统消息
        
        Args:
            intent: 用户意图，如"analyze"(分析), "trade"(交易), "monitor"(价格监控)
        
        Returns:
            Dict: 包含角色和内容的系统消息字典
        """
        # 基础系统角色描述
        base_content = """你是一位专业的加密货币投资顾问，名为"CoinGPT"。你熟悉区块链技术、加密货币市场和技术分析。
请根据我提供的市场数据和技术指标，提供专业、客观的解答。

【严格要求】当给出交易建议时：
- 禁止使用"附近"、"大约"、"可以考虑"、"左右"等模糊词汇
- 必须使用我提供的具体价格数值
- 必须给出明确的数字（如：101400.0000 USDT，而不是"支撑位附近"）

请记住，你的建议仅供参考，不构成投资建议，任何投资决策都应由用户自行承担风险。
"""
        
        # 基于不同意图的特定指导
        intent_guidance = {
            "analyze": """你的回复应当聚焦于K线技术分析:
1. 简洁明了地总结当前市场趋势
2. 解释关键的技术指标含义及其说明的市场状态
3. 提供可能的支撑位和阻力位
4. 给出合理的风险提示
""",
            
            "trade": """你的回复应当聚焦于交易建议:
1. 根据当前市场状况分析是否适合交易
2. **必须提供具体的进场点位和出场点位（使用我提供的当前价格、支撑位、阻力位等具体数值）**
3. **必须给出明确的止损位置和目标价格（具体数值，不要使用"附近"、"大约"等模糊词）**
4. 强调交易的风险和交易管理原则
5. 注意强调这只是分析不是投资建议

【严格格式要求】给出交易建议时必须这样写：

做多示例：
- 当前价格：104769.25 USDT
- 建议进场：104800.00 USDT（突破阻力位）
- 止损价格：101400.00 USDT（第一支撑位，约3.2%止损）
- 止盈目标1：107000.00 USDT（盈亏比 1:0.65）
- 止盈目标2：109500.00 USDT（盈亏比 1:1.4）

做空示例：
- 当前价格：104769.25 USDT  
- 建议进场：104700.00 USDT（当前价格）
- 止损价格：106500.00 USDT（阻力位上方，约1.7%止损）
- 止盈目标1：101500.00 USDT（第二支撑位，盈亏比 1:1.8）
- 止盈目标2：101400.00 USDT（第一支撑位，盈亏比 1:1.9）

【禁止的表述】：
❌ "可以考虑在支撑位附近设置止损"
❌ "止损设在101400左右"
❌ "大约在104800附近"
✅ 正确："止损价格：101400.00 USDT"
""",
            
            "monitor": """你的回复应当聚焦于价格监控:
1. 提供当前币种的最新价格和24小时涨跌幅
2. 分析当前价格位于相对历史区间的位置
3. 列出重要的价格节点（ATH, ATL, 当前支撑/阻力位）
4. 如果有重要价格趋势变化，给出提醒
""",
            
            "chat": """你是一位友好的加密货币助手:
1. 回答用户的问题，包括但不限于加密货币相关话题
2. 提供有关区块链、加密货币和金融技术的信息
3. 帮助用户理解加密货币市场的基本概念和原理
4. 保持聊天的开放性和轻松性

当用户没有明确要求分析特定币种时，以自然对话方式交流。
"""
        }
        
        # 获取特定意图的指导，如果没有匹配到则使用分析指导
        specific_guidance = intent_guidance.get(intent, intent_guidance["analyze"])
        
        # 组合完整的系统消息
        system_content = base_content + "\n" + specific_guidance
        
        return {"role": "system", "content": system_content}
    
    @staticmethod
    def construct_analysis_message(
        symbol: str,
        timeframe: str,
        analysis_data: Dict[str, Any],
        recent_price_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, str]:
        """
        构造包含分析结果的消息
        
        Args:
            symbol: 分析的货币符号
            timeframe: 时间窗口
            analysis_data: 趋势分析结果
            recent_price_data: 最近的价格数据
            
        Returns:
            Dict: 包含角色和内容的消息字典
        """
        # 格式化货币符号，确保正确显示（如将BTC/USDT中的/替换为兑）
        display_symbol = symbol.replace("/", "兑")
        
        # 构建分析内容
        content = f"### {display_symbol} {timeframe} 技术分析数据\n\n"
        
        # 检查是否有错误
        if "error" in analysis_data:
            content += f"**错误:** {analysis_data['error']}\n"
            return {"role": "assistant", "content": content}
        
        # 当前价格和涨跌幅
        content += f"**当前价格:** {analysis_data['price']:.4f}\n"
        content += f"**24小时涨跌:** {analysis_data['price_change_pct_24h']:.2f}%\n"
        
        if analysis_data.get('change_20d') is not None:
            content += f"**20天涨跌幅:** {analysis_data['change_20d']:.2f}%\n"
        
        # 整体趋势
        content += f"**整体趋势:** {analysis_data['overall_trend']}\n"
        content += f"**均线排列:** {analysis_data['ma_trend']}\n"
        
        # 技术指标
        content += f"**RSI:** {analysis_data['rsi']:.2f}"
        if analysis_data['overbought']:
            content += " (超买)\n"
        elif analysis_data['oversold']:
            content += " (超卖)\n"
        else:
            content += " (中性)\n"
        
        content += f"**MACD信号:** {analysis_data['macd_signal']}\n"
        content += f"**布林带状态:** {analysis_data['bollinger_status']}\n"
        
        # 支撑位和阻力位
        if analysis_data['support_levels']:
            support_levels = [f"{level:.4f}" for level in analysis_data['support_levels']]
            content += f"**主要支撑位:** {', '.join(support_levels)}\n"
        
        if analysis_data['resistance_levels']:
            resistance_levels = [f"{level:.4f}" for level in analysis_data['resistance_levels']]
            content += f"**主要阻力位:** {', '.join(resistance_levels)}\n"
        
        # 添加最近价格数据的简要描述
        if recent_price_data is not None and not recent_price_data.empty:
            last_5_days = recent_price_data.tail(5)
            content += "\n**最近5天价格走势:**\n"
            for _, row in last_5_days.iterrows():
                date = row['timestamp'].strftime('%Y-%m-%d')
                content += f"- {date}: 开:{row['open']:.4f} 高:{row['high']:.4f} 低:{row['low']:.4f} 收:{row['close']:.4f} 量:{row['volume']:.2f}\n"
        
        return {"role": "assistant", "content": content}
    
    @staticmethod
    def construct_user_message(user_prompt: str, extracted_info: Dict[str, Any]) -> Dict[str, str]:
        """
        构造包含用户消息和提取的信息的消息
        
        Args:
            user_prompt: 用户原始提示
            extracted_info: 从用户提示中提取的信息
            
        Returns:
            Dict: 包含角色和内容的用户消息字典
        """
        # 构建增强后的提示
        extracted_info_str = json.dumps(extracted_info, ensure_ascii=False, indent=2)
        
        content = f"{user_prompt}\n\n[提取的信息]\n```json\n{extracted_info_str}\n```"
        
        return {"role": "user", "content": content}
    
    @staticmethod
    def construct_messages(
        user_prompt: str,
        extracted_info: Dict[str, Any],
        analysis_results: Dict[str, Dict[str, Any]],
        price_data: Dict[str, pd.DataFrame],
        previous_messages: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """
        构造完整的消息列表
        
        Args:
            user_prompt: 用户原始提示
            extracted_info: 从用户提示中提取的信息
            analysis_results: 每个符号的分析结果
            price_data: 每个符号的价格数据
            previous_messages: 上下文中的前序消息
            
        Returns:
            List[Dict[str, str]]: 消息列表
        """
        # 初始化消息列表
        messages = []
        
        # 获取用户意图
        intent = extracted_info.get("intent", "analyze")
        
        # 添加基于意图的系统消息
        messages.append(PromptConstructor.construct_system_message(intent))
        
        # 添加前序消息（如果有）
        if previous_messages:
            for msg in previous_messages:
                if msg["role"] != "system":  # 避免重复的系统消息
                    messages.append(msg)
        
        # 为每个符号添加分析消息
        symbols = extracted_info.get('symbols', [])
        timeframe = extracted_info.get('time_window', '1d')
        
        for symbol in symbols:
            if symbol in analysis_results:
                if '/' not in symbol:
                    symbol_key = f"{symbol}/USDT"
                else:
                    symbol_key = symbol
                    
                recent_data = price_data.get(symbol_key)
                analysis_msg = PromptConstructor.construct_analysis_message(
                    symbol_key, 
                    timeframe, 
                    analysis_results[symbol], 
                    recent_data
                )
                messages.append(analysis_msg)
        
        # 添加用户消息
        messages.append(PromptConstructor.construct_user_message(user_prompt, extracted_info))
        
        return messages
