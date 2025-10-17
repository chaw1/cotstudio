"""
安全扫描器 - 文件安全检查和病毒扫描
"""
import os
import re
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, BinaryIO
from pathlib import Path
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    magic = None

try:
    import yara
    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False
    yara = None
from io import BytesIO

from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityScanner:
    """
    安全扫描器类
    """
    
    def __init__(self):
        self.yara_rules = None
        self._load_yara_rules()
    
    def _load_yara_rules(self):
        """
        加载YARA规则
        """
        if not YARA_AVAILABLE:
            logger.warning("YARA not available, skipping rule loading")
            return
            
        try:
            # 创建基础的恶意软件检测规则
            yara_rules_content = '''
            rule SuspiciousExecutable {
                meta:
                    description = "检测可执行文件"
                strings:
                    $mz = { 4D 5A }  // MZ header
                    $elf = { 7F 45 4C 46 }  // ELF header
                    $macho32 = { FE ED FA CE }  // Mach-O 32-bit
                    $macho64 = { FE ED FA CF }  // Mach-O 64-bit
                condition:
                    $mz at 0 or $elf at 0 or $macho32 at 0 or $macho64 at 0
            }
            
            rule SuspiciousScript {
                meta:
                    description = "检测可疑脚本"
                strings:
                    $bash = "#!/bin/bash"
                    $sh = "#!/bin/sh"
                    $python = "#!/usr/bin/python"
                    $perl = "#!/usr/bin/perl"
                    $cmd = "@echo off"
                    $powershell = "powershell"
                condition:
                    any of them
            }
            
            rule MaliciousJavaScript {
                meta:
                    description = "检测恶意JavaScript"
                strings:
                    $eval = "eval("
                    $unescape = "unescape("
                    $fromcharcode = "fromCharCode("
                    $activex = "ActiveXObject"
                    $wscript = "WScript.Shell"
                condition:
                    2 of them
            }
            
            rule SuspiciousArchive {
                meta:
                    description = "检测可疑压缩文件"
                strings:
                    $zip_bomb1 = { 50 4B 03 04 14 00 00 00 08 00 }
                    $zip_bomb2 = { 50 4B 03 04 0A 00 00 00 00 00 }
                condition:
                    $zip_bomb1 at 0 or $zip_bomb2 at 0
            }
            
            rule MacroDocument {
                meta:
                    description = "检测包含宏的Office文档"
                strings:
                    $ole = { D0 CF 11 E0 A1 B1 1A E1 }
                    $macro1 = "Microsoft Office Word"
                    $macro2 = "VBA"
                    $macro3 = "Macros"
                condition:
                    $ole at 0 and any of ($macro*)
            }
            '''
            
            self.yara_rules = yara.compile(source=yara_rules_content)
            logger.info("YARA rules loaded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to load YARA rules: {e}")
            self.yara_rules = None
    
    def scan_file_content(self, file_content: bytes, filename: str) -> Dict[str, any]:
        """
        扫描文件内容安全性
        
        Args:
            file_content: 文件内容
            filename: 文件名
            
        Returns:
            Dict: 扫描结果
        """
        scan_result = {
            'safe': True,
            'threats': [],
            'warnings': [],
            'file_type': None,
            'mime_type': None,
            'file_size': len(file_content),
            'md5_hash': hashlib.md5(file_content).hexdigest(),
            'sha256_hash': hashlib.sha256(file_content).hexdigest()
        }
        
        try:
            # 1. 文件类型检测
            file_type_result = self._detect_file_type(file_content, filename)
            scan_result.update(file_type_result)
            
            # 2. 文件大小检查
            size_result = self._check_file_size(file_content)
            if not size_result['safe']:
                scan_result['safe'] = False
                scan_result['threats'].extend(size_result['threats'])
            
            # 3. 文件头验证
            header_result = self._validate_file_header(file_content, filename)
            if not header_result['safe']:
                scan_result['safe'] = False
                scan_result['threats'].extend(header_result['threats'])
            
            # 4. 恶意内容扫描
            malware_result = self._scan_malware(file_content)
            if not malware_result['safe']:
                scan_result['safe'] = False
                scan_result['threats'].extend(malware_result['threats'])
            
            # 5. 文档宏检测
            macro_result = self._detect_macros(file_content, filename)
            if not macro_result['safe']:
                scan_result['warnings'].extend(macro_result['warnings'])
            
            # 6. 压缩文件炸弹检测
            zip_bomb_result = self._detect_zip_bomb(file_content, filename)
            if not zip_bomb_result['safe']:
                scan_result['safe'] = False
                scan_result['threats'].extend(zip_bomb_result['threats'])
            
            # 7. 嵌入式内容检测
            embedded_result = self._detect_embedded_content(file_content)
            if embedded_result['warnings']:
                scan_result['warnings'].extend(embedded_result['warnings'])
            
        except Exception as e:
            logger.error(f"Error during file security scan: {e}")
            scan_result['safe'] = False
            scan_result['threats'].append({
                'type': 'SCAN_ERROR',
                'description': '文件扫描过程中发生错误',
                'severity': 'HIGH'
            })
        
        return scan_result
    
    def _detect_file_type(self, file_content: bytes, filename: str) -> Dict[str, any]:
        """
        检测文件类型
        """
        result = {
            'file_type': None,
            'mime_type': None,
            'safe': True,
            'threats': []
        }
        
        try:
            if MAGIC_AVAILABLE:
                # 使用python-magic检测MIME类型
                mime_type = magic.from_buffer(file_content, mime=True)
                result['mime_type'] = mime_type
                
                # 获取文件类型描述
                file_type = magic.from_buffer(file_content)
                result['file_type'] = file_type
            else:
                # 回退到基于文件扩展名的检测
                import mimetypes
                mime_type, _ = mimetypes.guess_type(filename)
                result['mime_type'] = mime_type or 'application/octet-stream'
                result['file_type'] = f'File based on extension: {Path(filename).suffix}'
            
            # 检查是否为允许的文件类型
            if mime_type not in settings.ALLOWED_FILE_TYPES:
                result['safe'] = False
                result['threats'].append({
                    'type': 'UNSUPPORTED_FILE_TYPE',
                    'description': f'不支持的文件类型: {mime_type}',
                    'severity': 'MEDIUM'
                })
            
            # 检查文件扩展名与MIME类型是否匹配
            file_ext = Path(filename).suffix.lower()
            expected_mime = self._get_expected_mime_type(file_ext)
            if expected_mime and mime_type != expected_mime:
                result['threats'].append({
                    'type': 'MIME_TYPE_MISMATCH',
                    'description': f'文件扩展名与MIME类型不匹配: {file_ext} vs {mime_type}',
                    'severity': 'MEDIUM'
                })
            
        except Exception as e:
            logger.error(f"Error detecting file type: {e}")
            result['threats'].append({
                'type': 'FILE_TYPE_DETECTION_ERROR',
                'description': '无法检测文件类型',
                'severity': 'HIGH'
            })
        
        return result
    
    def _get_expected_mime_type(self, file_ext: str) -> Optional[str]:
        """
        根据文件扩展名获取期望的MIME类型
        """
        mime_map = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.tex': 'text/x-tex',
            '.latex': 'text/x-tex',
            '.json': 'application/json'
        }
        return mime_map.get(file_ext)
    
    def _check_file_size(self, file_content: bytes) -> Dict[str, any]:
        """
        检查文件大小
        """
        result = {
            'safe': True,
            'threats': []
        }
        
        file_size = len(file_content)
        
        if file_size > settings.MAX_FILE_SIZE:
            result['safe'] = False
            result['threats'].append({
                'type': 'FILE_SIZE_EXCEEDED',
                'description': f'文件大小超出限制: {file_size} bytes > {settings.MAX_FILE_SIZE} bytes',
                'severity': 'HIGH'
            })
        
        # 检查异常小的文件
        if file_size < 10:
            result['threats'].append({
                'type': 'SUSPICIOUS_FILE_SIZE',
                'description': f'文件大小异常小: {file_size} bytes',
                'severity': 'LOW'
            })
        
        return result
    
    def _validate_file_header(self, file_content: bytes, filename: str) -> Dict[str, any]:
        """
        验证文件头
        """
        result = {
            'safe': True,
            'threats': []
        }
        
        if len(file_content) < 4:
            return result
        
        file_ext = Path(filename).suffix.lower()
        header = file_content[:16]
        
        # 定义文件头签名
        file_signatures = {
            '.pdf': [b'%PDF-'],
            '.doc': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
            '.docx': [b'PK\x03\x04'],
            '.zip': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
            '.exe': [b'MZ'],
            '.elf': [b'\x7fELF'],
        }
        
        # 检查可执行文件头
        executable_headers = [b'MZ', b'\x7fELF', b'\xca\xfe\xba\xbe', b'\xfe\xed\xfa\xce']
        for exe_header in executable_headers:
            if header.startswith(exe_header):
                result['safe'] = False
                result['threats'].append({
                    'type': 'EXECUTABLE_FILE_DETECTED',
                    'description': '检测到可执行文件',
                    'severity': 'HIGH'
                })
                break
        
        # 验证已知文件类型的头部
        if file_ext in file_signatures:
            expected_headers = file_signatures[file_ext]
            header_match = any(header.startswith(sig) for sig in expected_headers)
            
            if not header_match:
                result['threats'].append({
                    'type': 'INVALID_FILE_HEADER',
                    'description': f'文件头与扩展名不匹配: {file_ext}',
                    'severity': 'MEDIUM'
                })
        
        return result
    
    def _scan_malware(self, file_content: bytes) -> Dict[str, any]:
        """
        恶意软件扫描
        """
        result = {
            'safe': True,
            'threats': []
        }
        
        if not YARA_AVAILABLE or not self.yara_rules:
            return result
        
        try:
            matches = self.yara_rules.match(data=file_content)
            
            for match in matches:
                severity = 'HIGH' if 'Executable' in match.rule else 'MEDIUM'
                result['threats'].append({
                    'type': 'YARA_RULE_MATCH',
                    'description': f'YARA规则匹配: {match.rule}',
                    'rule': match.rule,
                    'severity': severity
                })
                
                if severity == 'HIGH':
                    result['safe'] = False
        
        except Exception as e:
            logger.error(f"YARA scanning error: {e}")
        
        return result
    
    def _detect_macros(self, file_content: bytes, filename: str) -> Dict[str, any]:
        """
        检测Office文档中的宏
        """
        result = {
            'safe': True,
            'warnings': []
        }
        
        file_ext = Path(filename).suffix.lower()
        
        # 检查Office文档
        if file_ext in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
            # 检查OLE文件头（旧版Office文档）
            if file_content.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):
                # 搜索VBA相关字符串
                content_lower = file_content.lower()
                macro_indicators = [b'vba', b'macro', b'autoopen', b'autoexec', b'document_open']
                
                for indicator in macro_indicators:
                    if indicator in content_lower:
                        result['warnings'].append({
                            'type': 'MACRO_DETECTED',
                            'description': f'检测到可能包含宏的Office文档: {indicator.decode()}',
                            'severity': 'MEDIUM'
                        })
                        break
        
        return result
    
    def _detect_zip_bomb(self, file_content: bytes, filename: str) -> Dict[str, any]:
        """
        检测ZIP炸弹
        """
        result = {
            'safe': True,
            'threats': []
        }
        
        # 检查ZIP文件
        if file_content.startswith(b'PK'):
            try:
                import zipfile
                from io import BytesIO
                
                zip_buffer = BytesIO(file_content)
                
                with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                    total_uncompressed_size = 0
                    compressed_size = len(file_content)
                    
                    for info in zip_file.infolist():
                        total_uncompressed_size += info.file_size
                    
                    # 检查压缩比
                    if compressed_size > 0:
                        compression_ratio = total_uncompressed_size / compressed_size
                        
                        # 如果压缩比超过1000:1，可能是ZIP炸弹
                        if compression_ratio > 1000:
                            result['safe'] = False
                            result['threats'].append({
                                'type': 'ZIP_BOMB_DETECTED',
                                'description': f'检测到可能的ZIP炸弹，压缩比: {compression_ratio:.1f}:1',
                                'severity': 'HIGH'
                            })
                        elif compression_ratio > 100:
                            result['threats'].append({
                                'type': 'HIGH_COMPRESSION_RATIO',
                                'description': f'高压缩比文件，压缩比: {compression_ratio:.1f}:1',
                                'severity': 'MEDIUM'
                            })
            
            except Exception as e:
                logger.warning(f"Error checking ZIP file: {e}")
        
        return result
    
    def _detect_embedded_content(self, file_content: bytes) -> Dict[str, any]:
        """
        检测嵌入式内容
        """
        result = {
            'warnings': []
        }
        
        # 检查嵌入的可执行内容
        embedded_patterns = [
            (b'<script', 'JavaScript代码'),
            (b'javascript:', 'JavaScript URL'),
            (b'vbscript:', 'VBScript代码'),
            (b'data:text/html', 'HTML数据URI'),
            (b'<?php', 'PHP代码'),
            (b'<%', 'ASP/JSP代码'),
        ]
        
        content_lower = file_content.lower()
        
        for pattern, description in embedded_patterns:
            if pattern in content_lower:
                result['warnings'].append({
                    'type': 'EMBEDDED_CONTENT',
                    'description': f'检测到嵌入式内容: {description}',
                    'severity': 'MEDIUM'
                })
        
        return result
    
    def quarantine_file(self, file_content: bytes, filename: str, threat_info: Dict) -> str:
        """
        隔离可疑文件
        
        Args:
            file_content: 文件内容
            filename: 文件名
            threat_info: 威胁信息
            
        Returns:
            str: 隔离文件路径
        """
        try:
            # 创建隔离目录
            quarantine_dir = Path("quarantine")
            quarantine_dir.mkdir(exist_ok=True)
            
            # 生成隔离文件名
            import uuid
            quarantine_filename = f"{uuid.uuid4()}_{filename}.quarantine"
            quarantine_path = quarantine_dir / quarantine_filename
            
            # 保存文件到隔离区
            with open(quarantine_path, 'wb') as f:
                f.write(file_content)
            
            # 保存威胁信息
            threat_info_path = quarantine_path.with_suffix('.threat_info.json')
            import json
            with open(threat_info_path, 'w') as f:
                json.dump(threat_info, f, indent=2, ensure_ascii=False)
            
            logger.warning(f"File quarantined: {quarantine_path}")
            return str(quarantine_path)
            
        except Exception as e:
            logger.error(f"Failed to quarantine file: {e}")
            return ""


# 全局安全扫描器实例
security_scanner = SecurityScanner()


def scan_uploaded_file(file_content: bytes, filename: str) -> Dict[str, any]:
    """
    扫描上传的文件
    
    Args:
        file_content: 文件内容
        filename: 文件名
        
    Returns:
        Dict: 扫描结果
    """
    return security_scanner.scan_file_content(file_content, filename)


def is_file_safe(scan_result: Dict[str, any]) -> bool:
    """
    判断文件是否安全
    
    Args:
        scan_result: 扫描结果
        
    Returns:
        bool: True表示文件安全
    """
    return scan_result.get('safe', False)


def get_threat_summary(scan_result: Dict[str, any]) -> str:
    """
    获取威胁摘要
    
    Args:
        scan_result: 扫描结果
        
    Returns:
        str: 威胁摘要
    """
    threats = scan_result.get('threats', [])
    if not threats:
        return "文件安全"
    
    high_threats = [t for t in threats if t.get('severity') == 'HIGH']
    medium_threats = [t for t in threats if t.get('severity') == 'MEDIUM']
    
    summary_parts = []
    if high_threats:
        summary_parts.append(f"{len(high_threats)}个高危威胁")
    if medium_threats:
        summary_parts.append(f"{len(medium_threats)}个中危威胁")
    
    return "检测到: " + ", ".join(summary_parts)