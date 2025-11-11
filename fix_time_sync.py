#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复Bybit API时间同步问题
"""
import os
import sys
import time
import requests
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_time_sync():
    """检查本地时间与Bybit服务器时间的同步情况"""
    try:
        # 获取本地时间
        local_time = int(time.time() * 1000)
        local_datetime = datetime.fromtimestamp(local_time / 1000)
        
        # 获取Bybit服务器时间
        response = requests.get("https://api.bybit.com/v5/market/time", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('retCode') == 0:
                server_time = int(data['result']['timeSecond']) * 1000
                server_datetime = datetime.fromtimestamp(server_time / 1000)
                
                # 计算时间差
                time_diff = server_time - local_time
                
                print("="*50)
                print("时间同步检查结果")
                print("="*50)
                print(f"本地时间: {local_datetime} ({local_time})")
                print(f"服务器时间: {server_datetime} ({server_time})")
                print(f"时间差: {time_diff}ms ({time_diff/1000:.2f}秒)")
                print()
                
                if abs(time_diff) > 5000:  # 超过5秒
                    print("⚠️  警告: 时间差超过5秒，这会导致API请求失败!")
                    print("建议:")
                    print("1. 同步系统时间")
                    print("2. 检查时区设置")
                    print("3. 使用NTP服务器同步时间")
                    return False
                elif abs(time_diff) > 1000:  # 超过1秒
                    print("⚠️  注意: 时间差超过1秒，可能影响API稳定性")
                    print("建议同步系统时间")
                    return True
                else:
                    print("✅ 时间同步正常")
                    return True
            else:
                print(f"❌ 获取服务器时间失败: {data}")
                return False
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 检查时间同步时出错: {e}")
        return False

def sync_system_time():
    """尝试同步系统时间"""
    try:
        import platform
        system = platform.system()
        
        print("\n尝试同步系统时间...")
        
        if system == "Windows":
            # Windows系统
            import subprocess
            try:
                # 尝试使用w32tm同步时间
                result = subprocess.run(
                    ["w32tm", "/resync"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    print("✅ Windows时间同步成功")
                    return True
                else:
                    print(f"⚠️  Windows时间同步失败: {result.stderr}")
                    
                    # 尝试手动设置时间服务器
                    subprocess.run(
                        ["w32tm", "/config", "/manualpeerlist:time.windows.com", "/syncfromflags:manual"],
                        timeout=10
                    )
                    subprocess.run(["w32tm", "/resync"], timeout=10)
                    print("已尝试重新配置时间服务器")
                    
            except subprocess.TimeoutExpired:
                print("⚠️  时间同步超时")
            except FileNotFoundError:
                print("⚠️  找不到w32tm命令，请手动同步时间")
                
        elif system == "Linux":
            # Linux系统
            import subprocess
            try:
                # 尝试使用ntpdate
                result = subprocess.run(
                    ["sudo", "ntpdate", "-s", "time.nist.gov"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    print("✅ Linux时间同步成功")
                    return True
                else:
                    # 尝试使用timedatectl
                    subprocess.run(["sudo", "timedatectl", "set-ntp", "true"], timeout=10)
                    print("已启用NTP同步")
                    
            except subprocess.TimeoutExpired:
                print("⚠️  时间同步超时")
            except FileNotFoundError:
                print("⚠️  找不到时间同步命令，请手动同步时间")
                
        else:
            print(f"⚠️  不支持的操作系统: {system}")
            
    except Exception as e:
        print(f"❌ 同步系统时间时出错: {e}")
        
    return False

def main():
    """主函数"""
    print("Bybit API 时间同步修复工具")
    print("="*50)
    
    # 检查时间同步
    is_synced = check_time_sync()
    
    if not is_synced:
        print("\n尝试修复时间同步问题...")
        
        # 尝试同步系统时间
        sync_success = sync_system_time()
        
        if sync_success:
            print("\n重新检查时间同步...")
            time.sleep(2)  # 等待时间同步生效
            check_time_sync()
        else:
            print("\n手动修复建议:")
            print("1. Windows: 右键点击任务栏时间 -> 调整日期/时间 -> 立即同步")
            print("2. Linux: sudo ntpdate -s time.nist.gov")
            print("3. macOS: sudo sntp -sS time.apple.com")
    
    print("\n" + "="*50)
    print("修复完成后，请重启你的应用程序")

if __name__ == "__main__":
    main()
