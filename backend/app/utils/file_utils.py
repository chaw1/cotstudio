"""
文件处理工具函数
"""
import hashlib
import mimetypes
from typing import BinaryIO, Tuple, Optional
from pathlib import Path

from ..core.config import settings


def calculate_file_hash(file_data: BinaryIO) -> str:
    """
    计算文件的SHA256哈希值
    
    Args:
        file_data: 文件数据流
        
    Returns:
        str: 文件的SHA256哈希值
    """
    sha256_hash = hashlib.sha256()
    
    # 重置文件指针到开始位置
    file_data.seek(0)
    
    # 分块读取文件计算哈希
    for chunk in iter(lambda: file_data.read(8192), b""):
        sha256_hash.update(chunk)
    
    # 重置文件指针到开始位置
    file_data.seek(0)
    
    return sha256_hash.hexdigest()


def validate_file_type(filename: str, content_type: str) -> bool:
    """
    验证文件类型是否被允许
    
    Args:
        filename: 文件名
        content_type: MIME类型
        
    Returns:
        bool: 文件类型是否被允许
    """
    # 检查MIME类型
    if content_type in settings.ALLOWED_FILE_TYPES:
        return True
    
    # 根据文件扩展名推断MIME类型
    guessed_type, _ = mimetypes.guess_type(filename)
    if guessed_type and guessed_type in settings.ALLOWED_FILE_TYPES:
        return True
    
    # 特殊处理一些常见的文件扩展名
    file_ext = Path(filename).suffix.lower()
    ext_mime_map = {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain',
        '.md': 'text/markdown',
        '.markdown': 'text/markdown',
        '.tex': 'application/x-latex',
        '.latex': 'application/x-latex',
        '.json': 'application/json'
    }
    
    if file_ext in ext_mime_map:
        return ext_mime_map[file_ext] in settings.ALLOWED_FILE_TYPES
    
    return False


def validate_file_content(file_content: bytes, filename: str) -> bool:
    """
    验证文件内容安全性
    
    Args:
        file_content: 文件内容
        filename: 文件名
        
    Returns:
        bool: 文件内容是否安全
    """
    # 检查文件是否为空
    if not file_content:
        return False
    
    # 基本的文件头检查
    file_ext = Path(filename).suffix.lower()
    
    # PDF文件头检查
    if file_ext == '.pdf':
        return file_content.startswith(b'%PDF-')
    
    # JSON文件检查
    if file_ext == '.json':
        try:
            import json
            json.loads(file_content.decode('utf-8'))
            return True
        except (json.JSONDecodeError, UnicodeDecodeError):
            return False
    
    # 文本文件检查（TXT, MD, TEX等）
    if file_ext in ['.txt', '.md', '.markdown', '.tex', '.latex']:
        try:
            # 尝试解码为UTF-8
            file_content.decode('utf-8')
            return True
        except UnicodeDecodeError:
            # 尝试其他常见编码
            for encoding in ['gbk', 'gb2312', 'latin-1']:
                try:
                    file_content.decode(encoding)
                    return True
                except UnicodeDecodeError:
                    continue
            return False
    
    # Word文档检查
    if file_ext in ['.doc', '.docx']:
        # DOC文件头
        if file_ext == '.doc':
            return file_content.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1')
        # DOCX文件头（ZIP格式）
        elif file_ext == '.docx':
            return file_content.startswith(b'PK\x03\x04')
    
    # 默认允许其他文件类型
    return True


def scan_for_malicious_content(file_content: bytes, filename: str) -> bool:
    """
    扫描文件中的恶意内容
    
    Args:
        file_content: 文件内容
        filename: 文件名
        
    Returns:
        bool: 文件是否安全（True表示安全）
    """
    # 检查可执行文件头
    executable_signatures = [
        b'MZ',  # Windows PE
        b'\x7fELF',  # Linux ELF
        b'\xca\xfe\xba\xbe',  # Mach-O
        b'\xfe\xed\xfa\xce',  # Mach-O
    ]
    
    for signature in executable_signatures:
        if file_content.startswith(signature):
            return False
    
    # 检查脚本文件头
    script_signatures = [
        b'#!/bin/sh',
        b'#!/bin/bash',
        b'#!/usr/bin/python',
        b'#!/usr/bin/perl',
        b'@echo off',
    ]
    
    for signature in script_signatures:
        if file_content.startswith(signature):
            return False
    
    # 检查可疑的文本内容（仅对文本文件）
    file_ext = Path(filename).suffix.lower()
    if file_ext in ['.txt', '.md', '.markdown', '.tex', '.latex', '.json']:
        try:
            content_str = file_content.decode('utf-8', errors='ignore').lower()
            
            # 检查可疑关键词
            suspicious_keywords = [
                'eval(',
                'exec(',
                'system(',
                'shell_exec(',
                'passthru(',
                'proc_open(',
                '<script',
                'javascript:',
                'vbscript:',
                'onload=',
                'onerror=',
            ]
            
            for keyword in suspicious_keywords:
                if keyword in content_str:
                    return False
                    
        except UnicodeDecodeError:
            pass
    
    return True


def validate_file_size(file_size: int) -> bool:
    """
    验证文件大小是否在允许范围内
    
    Args:
        file_size: 文件大小（字节）
        
    Returns:
        bool: 文件大小是否合法
    """
    return 0 < file_size <= settings.MAX_FILE_SIZE


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    # 移除路径分隔符和其他不安全字符
    unsafe_chars = ['/', '\\', '<', '>', ':', '"', '|', '?', '*']
    sanitized = filename
    
    # 处理 .. 特殊情况 - 替换为 ..（保持不变）
    # 但是如果文件名以 .. 开头，则第一个 . 替换为 _
    if sanitized.startswith('..'):
        sanitized = '_' + sanitized[1:]
    
    # 处理其他不安全字符
    for char in unsafe_chars:
        sanitized = sanitized.replace(char, '_')
    
    # 限制文件名长度
    if len(sanitized) > 255:
        name_part = Path(sanitized).stem[:200]
        ext_part = Path(sanitized).suffix
        sanitized = name_part + ext_part
    
    return sanitized


def generate_file_path(project_id: str, filename: str, file_hash: str) -> str:
    """
    生成文件在对象存储中的路径
    
    Args:
        project_id: 项目ID
        filename: 文件名
        file_hash: 文件哈希值
        
    Returns:
        str: 文件存储路径
    """
    # 使用哈希值的前两位作为目录分层，避免单个目录文件过多
    hash_prefix = file_hash[:2]
    hash_suffix = file_hash[2:4]
    
    # 清理文件名
    safe_filename = sanitize_filename(filename)
    
    return f"projects/{project_id}/files/{hash_prefix}/{hash_suffix}/{file_hash}_{safe_filename}"


def get_file_extension_info(filename: str) -> Tuple[str, Optional[str]]:
    """
    获取文件扩展名和对应的MIME类型
    
    Args:
        filename: 文件名
        
    Returns:
        Tuple[str, Optional[str]]: (扩展名, MIME类型)
    """
    file_path = Path(filename)
    extension = file_path.suffix.lower()
    mime_type, _ = mimetypes.guess_type(filename)
    
    return extension, mime_type


def is_duplicate_file(file_hash: str, existing_hashes: list) -> bool:
    """
    检查是否为重复文件
    
    Args:
        file_hash: 文件哈希值
        existing_hashes: 已存在的文件哈希列表
        
    Returns:
        bool: 是否为重复文件
    """
    return file_hash in existing_hashes