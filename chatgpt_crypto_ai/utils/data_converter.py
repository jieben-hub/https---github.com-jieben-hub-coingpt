# -*- coding: utf-8 -*-
"""
数据转换工具
用于安全地转换API返回的数据，处理空值、空字符串等异常情况
"""
from typing import Any, Union, Optional
import logging

logger = logging.getLogger(__name__)

class SafeDataConverter:
    """安全数据转换器"""
    
    @staticmethod
    def to_float(value: Any, default: float = 0.0) -> float:
        """
        安全转换为浮点数
        
        Args:
            value: 要转换的值
            default: 默认值
            
        Returns:
            float: 转换后的浮点数
        """
        try:
            if value is None or value == '' or value == 'null':
                return default
            
            # 如果是字符串，先去除空格
            if isinstance(value, str):
                value = value.strip()
                if value == '':
                    return default
            
            return float(value)
        except (ValueError, TypeError) as e:
            logger.debug(f"转换浮点数失败: {value} -> {default}, 错误: {e}")
            return default
    
    @staticmethod
    def to_int(value: Any, default: int = 0) -> int:
        """
        安全转换为整数
        
        Args:
            value: 要转换的值
            default: 默认值
            
        Returns:
            int: 转换后的整数
        """
        try:
            if value is None or value == '' or value == 'null':
                return default
            
            # 如果是字符串，先去除空格
            if isinstance(value, str):
                value = value.strip()
                if value == '':
                    return default
            
            # 先转换为浮点数，再转换为整数（处理小数字符串）
            return int(float(value))
        except (ValueError, TypeError) as e:
            logger.debug(f"转换整数失败: {value} -> {default}, 错误: {e}")
            return default
    
    @staticmethod
    def to_string(value: Any, default: str = '') -> str:
        """
        安全转换为字符串
        
        Args:
            value: 要转换的值
            default: 默认值
            
        Returns:
            str: 转换后的字符串
        """
        try:
            if value is None or value == 'null':
                return default
            
            return str(value).strip()
        except Exception as e:
            logger.debug(f"转换字符串失败: {value} -> {default}, 错误: {e}")
            return default
    
    @staticmethod
    def to_bool(value: Any, default: bool = False) -> bool:
        """
        安全转换为布尔值
        
        Args:
            value: 要转换的值
            default: 默认值
            
        Returns:
            bool: 转换后的布尔值
        """
        try:
            if value is None or value == '' or value == 'null':
                return default
            
            if isinstance(value, bool):
                return value
            
            if isinstance(value, str):
                value = value.strip().lower()
                if value in ('true', '1', 'yes', 'on'):
                    return True
                elif value in ('false', '0', 'no', 'off'):
                    return False
                else:
                    return default
            
            if isinstance(value, (int, float)):
                return bool(value)
            
            return default
        except Exception as e:
            logger.debug(f"转换布尔值失败: {value} -> {default}, 错误: {e}")
            return default
    
    @staticmethod
    def safe_get(data: dict, key: str, converter_func=None, default=None):
        """
        安全获取字典值并转换
        
        Args:
            data: 字典数据
            key: 键名
            converter_func: 转换函数
            default: 默认值
            
        Returns:
            Any: 转换后的值
        """
        try:
            value = data.get(key, default)
            if converter_func:
                return converter_func(value, default if default is not None else 0)
            return value
        except Exception as e:
            logger.debug(f"安全获取值失败: key={key}, 错误: {e}")
            return default
    
    @staticmethod
    def clean_api_response(data: dict, field_types: dict) -> dict:
        """
        清理API响应数据
        
        Args:
            data: 原始数据
            field_types: 字段类型映射 {'field_name': (converter_func, default_value)}
            
        Returns:
            dict: 清理后的数据
        """
        cleaned = {}
        
        for field, (converter, default) in field_types.items():
            try:
                raw_value = data.get(field)
                if converter == float:
                    cleaned[field] = SafeDataConverter.to_float(raw_value, default)
                elif converter == int:
                    cleaned[field] = SafeDataConverter.to_int(raw_value, default)
                elif converter == str:
                    cleaned[field] = SafeDataConverter.to_string(raw_value, default)
                elif converter == bool:
                    cleaned[field] = SafeDataConverter.to_bool(raw_value, default)
                else:
                    cleaned[field] = converter(raw_value, default) if converter else raw_value
            except Exception as e:
                logger.warning(f"清理字段失败: {field}, 错误: {e}")
                cleaned[field] = default
        
        return cleaned

# 便捷函数
def safe_float(value: Any, default: float = 0.0) -> float:
    """便捷的安全浮点数转换函数"""
    return SafeDataConverter.to_float(value, default)

def safe_int(value: Any, default: int = 0) -> int:
    """便捷的安全整数转换函数"""
    return SafeDataConverter.to_int(value, default)

def safe_str(value: Any, default: str = '') -> str:
    """便捷的安全字符串转换函数"""
    return SafeDataConverter.to_string(value, default)

def safe_bool(value: Any, default: bool = False) -> bool:
    """便捷的安全布尔值转换函数"""
    return SafeDataConverter.to_bool(value, default)
