# -*- coding: utf-8 -*-
"""
UTF-8 验证和修复工具
用于检测和修复应用中的UTF-8编码问题
"""
import json
import logging
import re
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

class UTF8Validator:
    """UTF-8编码验证和修复工具"""
    
    @staticmethod
    def is_valid_utf8(data: Union[str, bytes]) -> bool:
        """
        检查数据是否为有效的UTF-8编码
        
        Args:
            data: 要检查的数据
            
        Returns:
            bool: 是否为有效UTF-8
        """
        try:
            if isinstance(data, bytes):
                data.decode('utf-8')
            elif isinstance(data, str):
                data.encode('utf-8')
            return True
        except UnicodeDecodeError:
            return False
        except UnicodeEncodeError:
            return False
    
    @staticmethod
    def clean_string(text: str) -> str:
        """
        清理字符串中的无效UTF-8字符
        
        Args:
            text: 输入字符串
            
        Returns:
            str: 清理后的字符串
        """
        if not isinstance(text, str):
            return str(text)
        
        try:
            # 尝试编码和解码来清理无效字符
            cleaned = text.encode('utf-8', errors='ignore').decode('utf-8')
            return cleaned
        except Exception as e:
            logger.warning(f"清理字符串时出错: {e}")
            # 如果出错，返回ASCII安全版本
            return ''.join(char for char in text if ord(char) < 128)
    
    @staticmethod
    def validate_json_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证和清理JSON数据中的UTF-8字符
        
        Args:
            data: JSON数据字典
            
        Returns:
            Dict: 清理后的数据
        """
        def clean_value(value):
            if isinstance(value, str):
                return UTF8Validator.clean_string(value)
            elif isinstance(value, dict):
                return {k: clean_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [clean_value(item) for item in value]
            else:
                return value
        
        try:
            return clean_value(data)
        except Exception as e:
            logger.error(f"清理JSON数据时出错: {e}")
            return {}
    
    @staticmethod
    def safe_json_dumps(data: Any, **kwargs) -> str:
        """
        安全的JSON序列化，确保UTF-8兼容
        
        Args:
            data: 要序列化的数据
            **kwargs: json.dumps的其他参数
            
        Returns:
            str: JSON字符串
        """
        try:
            # 设置默认参数确保UTF-8安全
            kwargs.setdefault('ensure_ascii', False)
            kwargs.setdefault('separators', (',', ':'))
            
            # 先清理数据
            if isinstance(data, dict):
                cleaned_data = UTF8Validator.validate_json_data(data)
            else:
                cleaned_data = data
            
            return json.dumps(cleaned_data, **kwargs)
        except UnicodeEncodeError as e:
            logger.error(f"JSON序列化UTF-8错误: {e}")
            # 回退到ASCII安全模式
            kwargs['ensure_ascii'] = True
            return json.dumps(data, **kwargs)
        except Exception as e:
            logger.error(f"JSON序列化失败: {e}")
            return json.dumps({"error": "serialization_failed"})
    
    @staticmethod
    def safe_json_loads(json_str: str) -> Any:
        """
        安全的JSON反序列化
        
        Args:
            json_str: JSON字符串
            
        Returns:
            Any: 反序列化的数据
        """
        try:
            # 先清理字符串
            cleaned_str = UTF8Validator.clean_string(json_str)
            return json.loads(cleaned_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return None
        except Exception as e:
            logger.error(f"JSON解析失败: {e}")
            return None
    
    @staticmethod
    def validate_database_string(value: str, max_length: Optional[int] = None) -> str:
        """
        验证数据库字符串字段
        
        Args:
            value: 字符串值
            max_length: 最大长度限制
            
        Returns:
            str: 验证后的字符串
        """
        if not isinstance(value, str):
            value = str(value)
        
        # 清理UTF-8字符
        cleaned = UTF8Validator.clean_string(value)
        
        # 限制长度
        if max_length and len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
        
        return cleaned
    
    @staticmethod
    def fix_file_encoding(file_path: str) -> bool:
        """
        修复文件的UTF-8编码问题
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否成功修复
        """
        try:
            # 尝试以不同编码读取文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                logger.error(f"无法读取文件: {file_path}")
                return False
            
            # 清理内容并以UTF-8保存
            cleaned_content = UTF8Validator.clean_string(content)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            logger.info(f"已修复文件编码: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"修复文件编码失败: {file_path}, 错误: {e}")
            return False
