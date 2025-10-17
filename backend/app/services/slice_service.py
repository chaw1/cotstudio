"""
文档切片服务
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models.slice import Slice, SliceType
from app.models.file import File
from app.services.base_service import BaseService
from app.services.ocr_service import DocumentStructure, OCRResult
from app.core.exceptions import FileProcessingError

logger = logging.getLogger(__name__)


@dataclass
class SliceCandidate:
    """切片候选"""
    content: str
    slice_type: SliceType
    start_offset: int
    end_offset: int
    page_number: int
    confidence: float = 1.0
    metadata: Dict[str, Any] = None


class DocumentSlicer:
    """文档切片器"""
    
    def __init__(self):
        self.paragraph_patterns = [
            r'\n\s*\n',  # 双换行
            r'\.\s*\n',  # 句号后换行
            r'。\s*\n',  # 中文句号后换行
        ]
        
        self.header_patterns = [
            r'^#{1,6}\s+.+$',  # Markdown标题
            r'^\d+\.\s+.+$',   # 数字标题
            r'^[一二三四五六七八九十]+[、\.]\s*.+$',  # 中文数字标题
            r'^第[一二三四五六七八九十]+[章节部分]\s*.+$',  # 章节标题
        ]
        
        self.table_patterns = [
            r'\|.*\|',  # Markdown表格
            r'┌.*┐',    # 表格边框
            r'├.*┤',    # 表格分隔
        ]
    
    def slice_document(self, document: DocumentStructure, file_record: File) -> List[SliceCandidate]:
        """
        对文档进行切片
        
        Args:
            document: 文档结构
            file_record: 文件记录
            
        Returns:
            List[SliceCandidate]: 切片候选列表
        """
        slices = []
        
        # 基于文本内容进行切片
        if document.full_text:
            text_slices = self._slice_by_text_structure(document.full_text)
            slices.extend(text_slices)
        
        # 基于OCR结果进行切片（如果有位置信息）
        if document.text_blocks:
            ocr_slices = self._slice_by_ocr_blocks(document.text_blocks)
            slices.extend(ocr_slices)
        
        # 按页面进行切片
        page_slices = self._slice_by_pages(document)
        slices.extend(page_slices)
        
        # 去重和合并相似切片
        slices = self._deduplicate_slices(slices)
        
        # 排序切片
        slices.sort(key=lambda x: (x.page_number, x.start_offset))
        
        logger.info(f"Generated {len(slices)} slices for file {file_record.id}")
        return slices
    
    def _slice_by_text_structure(self, text: str) -> List[SliceCandidate]:
        """基于文本结构进行切片"""
        slices = []
        current_offset = 0
        
        # 按段落切片
        paragraphs = self._split_paragraphs(text)
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                current_offset += len(paragraph)
                continue
            
            # 确定切片类型
            slice_type = self._determine_slice_type(paragraph)
            
            # 计算偏移量
            start_offset = current_offset
            end_offset = current_offset + len(paragraph)
            
            # 估算页码（简单估算，每2000字符一页）
            page_number = (start_offset // 2000) + 1
            
            slice_candidate = SliceCandidate(
                content=paragraph.strip(),
                slice_type=slice_type,
                start_offset=start_offset,
                end_offset=end_offset,
                page_number=page_number,
                confidence=0.8,
                metadata={'source': 'text_structure'}
            )
            
            slices.append(slice_candidate)
            current_offset = end_offset
        
        return slices
    
    def _slice_by_ocr_blocks(self, text_blocks: List[Dict[str, Any]]) -> List[SliceCandidate]:
        """基于OCR文本块进行切片"""
        slices = []
        
        for block in text_blocks:
            if not block.get('text', '').strip():
                continue
            
            # 使用OCR块的位置信息
            page_number = block.get('page', 1)
            bbox = block.get('bbox')
            confidence = block.get('confidence', 0.9)
            
            # 根据位置和内容确定类型
            slice_type = self._determine_slice_type_from_ocr(block)
            
            slice_candidate = SliceCandidate(
                content=block['text'].strip(),
                slice_type=slice_type,
                start_offset=0,  # OCR块没有全文偏移量
                end_offset=len(block['text']),
                page_number=page_number,
                confidence=confidence,
                metadata={
                    'source': 'ocr_block',
                    'bbox': bbox,
                    'ocr_confidence': confidence
                }
            )
            
            slices.append(slice_candidate)
        
        return slices
    
    def _slice_by_pages(self, document: DocumentStructure) -> List[SliceCandidate]:
        """按页面进行切片"""
        slices = []
        
        for page_num, page_results in enumerate(document.page_results, 1):
            if not page_results:
                continue
            
            # 合并页面内容
            page_text = '\n'.join([result.text for result in page_results])
            
            if page_text.strip():
                slice_candidate = SliceCandidate(
                    content=page_text.strip(),
                    slice_type=SliceType.PARAGRAPH,
                    start_offset=0,
                    end_offset=len(page_text),
                    page_number=page_num,
                    confidence=0.7,
                    metadata={
                        'source': 'page_content',
                        'ocr_results_count': len(page_results)
                    }
                )
                
                slices.append(slice_candidate)
        
        return slices
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """分割段落"""
        # 使用多种模式分割段落
        paragraphs = [text]
        
        for pattern in self.paragraph_patterns:
            new_paragraphs = []
            for paragraph in paragraphs:
                parts = re.split(pattern, paragraph, flags=re.MULTILINE)
                new_paragraphs.extend(parts)
            paragraphs = new_paragraphs
        
        # 过滤空段落并保持原始分隔符
        result = []
        for paragraph in paragraphs:
            if paragraph.strip():
                result.append(paragraph)
        
        return result
    
    def _determine_slice_type(self, text: str) -> SliceType:
        """根据文本内容确定切片类型"""
        text_lines = text.strip().split('\n')
        first_line = text_lines[0].strip() if text_lines else ""
        
        # 检查是否为标题
        for pattern in self.header_patterns:
            if re.match(pattern, first_line, re.MULTILINE):
                return SliceType.HEADER
        
        # 检查是否为表格
        for pattern in self.table_patterns:
            if re.search(pattern, text):
                return SliceType.TABLE
        
        # 检查是否为页眉页脚（简单判断）
        if len(text.strip()) < 50 and (
            '页' in text or 'Page' in text or 
            re.search(r'\d+', text)  # 包含数字
        ):
            return SliceType.FOOTER
        
        # 默认为段落
        return SliceType.PARAGRAPH
    
    def _determine_slice_type_from_ocr(self, block: Dict[str, Any]) -> SliceType:
        """根据OCR块信息确定切片类型"""
        text = block.get('text', '')
        bbox = block.get('bbox')
        page = block.get('page', 1)
        
        # 根据位置判断（如果有边界框信息）
        if bbox:
            x1, y1, x2, y2 = bbox
            height = y2 - y1
            width = x2 - x1
            
            # 如果文本很短且位置在页面顶部或底部，可能是页眉页脚
            if len(text.strip()) < 50:
                if y1 < 100:  # 页面顶部
                    return SliceType.HEADER
                elif y1 > 700:  # 页面底部（假设页面高度约800）
                    return SliceType.FOOTER
            
            # 如果宽高比异常，可能是表格
            if width > height * 3:  # 很宽的文本块
                return SliceType.TABLE
        
        # 回退到基于文本内容的判断
        return self._determine_slice_type(text)
    
    def _deduplicate_slices(self, slices: List[SliceCandidate]) -> List[SliceCandidate]:
        """去重和合并相似切片"""
        if not slices:
            return slices
        
        # 按内容相似度去重
        unique_slices = []
        seen_contents = set()
        
        for slice_candidate in slices:
            # 简单的内容去重（可以改进为更复杂的相似度算法）
            content_key = slice_candidate.content.strip().lower()[:100]  # 取前100字符作为键
            
            if content_key not in seen_contents:
                seen_contents.add(content_key)
                unique_slices.append(slice_candidate)
            else:
                # 如果内容重复，选择置信度更高的
                for i, existing_slice in enumerate(unique_slices):
                    existing_key = existing_slice.content.strip().lower()[:100]
                    if existing_key == content_key:
                        if slice_candidate.confidence > existing_slice.confidence:
                            unique_slices[i] = slice_candidate
                        break
        
        return unique_slices


class SliceService(BaseService[Slice]):
    """切片服务"""
    
    def __init__(self):
        super().__init__(Slice)
        self.slicer = DocumentSlicer()
    
    def get_by_file(self, db: Session, file_id: str) -> List[Slice]:
        """根据文件ID获取切片列表"""
        return db.query(Slice).filter(Slice.file_id == file_id).order_by(Slice.sequence_number).all()
    
    def get_by_project(self, db: Session, project_id: str) -> List[Slice]:
        """根据项目ID获取所有切片"""
        from app.models.file import File
        return db.query(Slice).join(File).filter(File.project_id == project_id).all()
    
    def create_slices_from_document(self, db: Session, file_record: File, document: DocumentStructure) -> List[Slice]:
        """
        从文档结构创建切片
        
        Args:
            db: 数据库会话
            file_record: 文件记录
            document: 文档结构
            
        Returns:
            List[Slice]: 创建的切片列表
        """
        try:
            # 生成切片候选
            slice_candidates = self.slicer.slice_document(document, file_record)
            
            # 创建切片记录
            slices = []
            for i, candidate in enumerate(slice_candidates):
                slice_data = {
                    'file_id': file_record.id,
                    'content': candidate.content,
                    'start_offset': candidate.start_offset,
                    'end_offset': candidate.end_offset,
                    'slice_type': candidate.slice_type,
                    'page_number': candidate.page_number,
                    'sequence_number': i + 1
                }
                
                slice_record = self.create(db, obj_in=slice_data)
                slices.append(slice_record)
            
            logger.info(f"Created {len(slices)} slices for file {file_record.id}")
            return slices
            
        except Exception as e:
            logger.error(f"Failed to create slices for file {file_record.id}: {e}")
            raise FileProcessingError(f"Slice creation failed: {str(e)}", "SLICE_CREATION_FAILED")
    
    def get_slice_context(self, db: Session, slice_id: str, context_size: int = 2) -> Dict[str, Any]:
        """
        获取切片的上下文信息
        
        Args:
            db: 数据库会话
            slice_id: 切片ID
            context_size: 上下文大小（前后各几个切片）
            
        Returns:
            Dict[str, Any]: 包含切片及其上下文的信息
        """
        slice_record = self.get(db, id=slice_id)
        if not slice_record:
            return None
        
        # 获取同文件的相邻切片
        file_slices = self.get_by_file(db, slice_record.file_id)
        
        # 找到当前切片的位置
        current_index = -1
        for i, s in enumerate(file_slices):
            if s.id == slice_id:
                current_index = i
                break
        
        if current_index == -1:
            return None
        
        # 获取上下文切片
        start_index = max(0, current_index - context_size)
        end_index = min(len(file_slices), current_index + context_size + 1)
        
        context_slices = file_slices[start_index:end_index]
        
        return {
            'current_slice': slice_record,
            'context_slices': context_slices,
            'current_index': current_index,
            'total_slices': len(file_slices),
            'file_id': slice_record.file_id
        }
    
    def search_slices(self, db: Session, project_id: str, query: str, limit: int = 50) -> List[Slice]:
        """
        在项目中搜索切片
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            query: 搜索查询
            limit: 结果限制
            
        Returns:
            List[Slice]: 匹配的切片列表
        """
        from app.models.file import File
        
        return db.query(Slice).join(File).filter(
            File.project_id == project_id,
            Slice.content.contains(query)
        ).limit(limit).all()
    
    def get_file_slice_stats(self, db: Session, file_id: str) -> Dict[str, Any]:
        """
        获取文件的切片统计信息
        
        Args:
            db: 数据库会话
            file_id: 文件ID
            
        Returns:
            Dict[str, Any]: 切片统计信息
        """
        from sqlalchemy import func
        
        stats = db.query(
            func.count(Slice.id).label('total_slices'),
            func.count(Slice.id).filter(Slice.slice_type == SliceType.PARAGRAPH).label('paragraph_count'),
            func.count(Slice.id).filter(Slice.slice_type == SliceType.HEADER).label('header_count'),
            func.count(Slice.id).filter(Slice.slice_type == SliceType.TABLE).label('table_count'),
            func.count(Slice.id).filter(Slice.slice_type == SliceType.IMAGE).label('image_count'),
            func.max(Slice.page_number).label('max_page')
        ).filter(Slice.file_id == file_id).first()
        
        return {
            'total_slices': stats.total_slices or 0,
            'paragraph_count': stats.paragraph_count or 0,
            'header_count': stats.header_count or 0,
            'table_count': stats.table_count or 0,
            'image_count': stats.image_count or 0,
            'max_page': stats.max_page or 0
        }


# 创建全局切片服务实例
slice_service = SliceService()