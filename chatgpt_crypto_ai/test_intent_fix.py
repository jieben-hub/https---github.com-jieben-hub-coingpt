# -*- coding: utf-8 -*-
"""测试意图提取修复"""
from utils.intent_extractor import IntentExtractor

# 测试用例
test_cases = [
    {
        "input": "分析最近BTC走势如何，目前值得入场吗",
        "expected_intent": "trade",
        "reason": "包含'值得入场'关键词"
    },
    {
        "input": "BTC最近走势如何",
        "expected_intent": "analyze",
        "reason": "纯技术分析问题"
    },
    {
        "input": "以太坊现在值得买入吗",
        "expected_intent": "trade",
        "reason": "包含'值得买入'关键词"
    },
    {
        "input": "BTC能买吗",
        "expected_intent": "trade",
        "reason": "包含'能买'关键词"
    },
    {
        "input": "BTC现在多少钱",
        "expected_intent": "monitor",
        "reason": "只询问价格"
    },
    {
        "input": "分析一下SOL的4小时图，适合建仓吗",
        "expected_intent": "trade",
        "reason": "包含'适合建仓'关键词"
    }
]

print("=" * 80)
print("意图提取测试")
print("=" * 80)

for i, test in enumerate(test_cases, 1):
    print(f"\n测试 {i}: {test['input']}")
    print(f"预期意图: {test['expected_intent']}")
    print(f"原因: {test['reason']}")
    
    result = IntentExtractor.extract_intent(test['input'])
    
    print(f"提取结果: {result}")
    
    if result['intent'] == test['expected_intent']:
        print("✅ 通过")
    else:
        print(f"❌ 失败 - 实际意图: {result['intent']}")
    
    print("-" * 80)

print("\n测试完成！")
