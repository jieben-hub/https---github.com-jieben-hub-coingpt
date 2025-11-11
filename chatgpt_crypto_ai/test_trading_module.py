# -*- coding: utf-8 -*-
"""
交易模块测试脚本
"""
from services.trading_service import TradingService
from exchanges.exchange_factory import ExchangeFactory
import config

def test_connection():
    """测试连接"""
    print("=" * 60)
    print("测试 1: 连接交易所")
    print("=" * 60)
    
    try:
        exchange = TradingService.get_exchange()
        print(f"✅ 成功连接到 {exchange.get_exchange_name()}")
        print(f"   测试网: {config.TRADING_TESTNET}")
        return True
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


def test_balance():
    """测试获取余额"""
    print("\n" + "=" * 60)
    print("测试 2: 获取账户余额")
    print("=" * 60)
    
    try:
        balance = TradingService.get_balance(coin="USDT")
        print(f"✅ 余额查询成功:")
        print(f"   币种: {balance['coin']}")
        print(f"   可用: {balance['available']} USDT")
        print(f"   总额: {balance['total']} USDT")
        return True
    except Exception as e:
        print(f"❌ 获取余额失败: {e}")
        return False


def test_positions():
    """测试获取持仓"""
    print("\n" + "=" * 60)
    print("测试 3: 获取持仓")
    print("=" * 60)
    
    try:
        positions = TradingService.get_positions()
        if positions:
            print(f"✅ 当前持仓 ({len(positions)} 个):")
            for pos in positions:
                print(f"   {pos['symbol']}: {pos['side']} {pos['size']} @ {pos['entry_price']}")
                print(f"      未实现盈亏: {pos['unrealized_pnl']} USDT")
        else:
            print("✅ 当前无持仓")
        return True
    except Exception as e:
        print(f"❌ 获取持仓失败: {e}")
        return False


def test_open_orders():
    """测试获取挂单"""
    print("\n" + "=" * 60)
    print("测试 4: 获取挂单")
    print("=" * 60)
    
    try:
        orders = TradingService.get_open_orders()
        if orders:
            print(f"✅ 当前挂单 ({len(orders)} 个):")
            for order in orders:
                print(f"   {order['symbol']}: {order['side']} {order['quantity']} @ {order['price']}")
        else:
            print("✅ 当前无挂单")
        return True
    except Exception as e:
        print(f"❌ 获取挂单失败: {e}")
        return False


def test_supported_exchanges():
    """测试支持的交易所"""
    print("\n" + "=" * 60)
    print("测试 5: 支持的交易所")
    print("=" * 60)
    
    exchanges = ExchangeFactory.get_supported_exchanges()
    print(f"✅ 当前支持 {len(exchanges)} 个交易所:")
    for ex in exchanges:
        print(f"   - {ex}")
    return True


def test_create_small_order():
    """测试创建小额订单（可选）"""
    print("\n" + "=" * 60)
    print("测试 6: 创建小额订单（跳过）")
    print("=" * 60)
    
    print("⚠️  为了安全，跳过真实下单测试")
    print("   如需测试下单，请手动调用:")
    print("   TradingService.create_order(")
    print("       symbol='BTCUSDT',")
    print("       side='buy',")
    print("       quantity=0.001,")
    print("       order_type='market',")
    print("       position_side='long'")
    print("   )")
    return True


def main():
    """运行所有测试"""
    print("\n" + "🚀" * 30)
    print("交易模块测试")
    print("🚀" * 30)
    
    print(f"\n配置信息:")
    print(f"  交易所: {config.TRADING_EXCHANGE}")
    print(f"  测试网: {config.TRADING_TESTNET}")
    print(f"  API Key: {config.TRADING_API_KEY[:10]}..." if config.TRADING_API_KEY else "  API Key: 未配置")
    
    # 运行测试
    results = []
    
    results.append(("连接测试", test_connection()))
    
    if results[0][1]:  # 如果连接成功，继续其他测试
        results.append(("余额查询", test_balance()))
        results.append(("持仓查询", test_positions()))
        results.append(("挂单查询", test_open_orders()))
        results.append(("支持的交易所", test_supported_exchanges()))
        results.append(("创建订单", test_create_small_order()))
    
    # 打印测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败，请检查配置")


if __name__ == "__main__":
    main()
