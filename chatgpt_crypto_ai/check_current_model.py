# -*- coding: utf-8 -*-
"""检查当前使用的模型"""
import config

print("=" * 80)
print("当前配置检查")
print("=" * 80)
print(f"\n当前使用的模型: {config.OPENAI_MODEL}")
print(f"OpenAI API Key: {'已配置' if config.OPENAI_API_KEY else '未配置'}")
print(f"API 超时时间: {config.OPENAI_TIMEOUT}秒")

print("\n" + "=" * 80)
print("建议")
print("=" * 80)

if config.OPENAI_MODEL == 'gpt-3.5-turbo':
    print("⚠️  当前使用 gpt-3.5-turbo")
    print("\n强烈建议升级到以下模型之一：")
    print("  1. gpt-4o-mini（推荐，性价比高）")
    print("  2. gpt-4o（最佳质量）")
    print("\n修改方法：")
    print("  在 .env 文件中添加或修改：")
    print("  OPENAI_MODEL=gpt-4o-mini")
elif 'gpt-4' in config.OPENAI_MODEL:
    print(f"✅ 当前使用 {config.OPENAI_MODEL}，这是一个好的选择！")
else:
    print(f"ℹ️  当前使用 {config.OPENAI_MODEL}")

print("\n" + "=" * 80)
