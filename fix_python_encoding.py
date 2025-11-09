#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复Python文件编码声明的脚本
自动为缺少编码声明的Python文件添加UTF-8编码声明
"""
import os
import re
from pathlib import Path

# 编码声明正则表达式
ENCODING_PATTERN = re.compile(r'#.*?coding[:=]\s*([-\w.]+)')
# 标准编码声明
ENCODING_DECLARATION = '# -*- coding: utf-8 -*-\n'

def has_encoding_declaration(content):
    """检查文件内容是否有编码声明"""
    lines = content.split('\n', 2)[:2]  # 只检查前两行
    for line in lines:
        if ENCODING_PATTERN.search(line):
            return True
    return False

def fix_file_encoding(file_path):
    """为文件添加编码声明"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if not has_encoding_declaration(content):
            # 如果文件以#!/usr/bin/env开头，保留第一行，在第二行添加编码声明
            if content.startswith('#!/'):
                first_line, rest = content.split('\n', 1)
                new_content = first_line + '\n' + ENCODING_DECLARATION + rest
            else:
                new_content = ENCODING_DECLARATION + content
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True
        return False
    except Exception as e:
        print(f"处理文件时出错: {file_path}, 错误: {e}")
        return False

def scan_and_fix_directory(directory):
    """扫描目录并修复所有Python文件"""
    fixed_files = []
    skipped_files = []
    directory_path = Path(directory)
    
    for file_path in directory_path.glob('**/*.py'):
        if fix_file_encoding(file_path):
            fixed_files.append(str(file_path))
        else:
            skipped_files.append(str(file_path))
    
    return fixed_files, skipped_files

if __name__ == "__main__":
    import sys
    
    # 默认检查当前目录
    directory = os.getcwd()
    
    # 如果提供了命令行参数，使用指定的目录
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    
    print(f"正在扫描并修复目录: {directory}")
    fixed_files, skipped_files = scan_and_fix_directory(directory)
    
    print(f"\n已修复 {len(fixed_files)} 个文件")
    print(f"跳过 {len(skipped_files)} 个文件 (已有编码声明或处理失败)")
    print(skipped_files)
    
    if fixed_files:
        print("\n修复的文件列表:")
        for file in fixed_files:
            print(f"- {file}")
