"""
MinerU解析结果导入服务
用于将MinerU本地解析的结果导入到数据库
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.app_logging import logger
from app.models.slice import Slice, SliceType
from app.models.file import File, OCRStatus
from app.services.file_service import file_service
from app.services.slice_service import slice_service


class MinerUImportService:
    """MinerU解析结果导入服务"""
    
    def __init__(self, mineru_output_dir: str = "./mineru/output"):
        self.mineru_output_dir = Path(mineru_output_dir)
        
    def get_available_documents(self) -> List[Dict[str, Any]]:
        """获取可用的MinerU解析文档列表"""
        documents = []
        
        if not self.mineru_output_dir.exists():
            logger.warning(f"MinerU output directory not found: {self.mineru_output_dir}")
            return documents
        
        # 遍历output目录下的所有子目录
        for doc_dir in self.mineru_output_dir.iterdir():
            if not doc_dir.is_dir():
                continue
            
            # 检查vlm和pipeline模式的解析结果
            for mode in ['vlm', 'pipeline']:
                mode_dir = doc_dir / mode
                if not mode_dir.exists():
                    continue
                
                content_list_file = mode_dir / f"{doc_dir.name}_content_list.json"
                markdown_file = mode_dir / f"{doc_dir.name}.md"
                
                if content_list_file.exists():
                    try:
                        with open(content_list_file, 'r', encoding='utf-8') as f:
                            content_list = json.load(f)
                        
                        # 读取markdown文件获取全文
                        full_text = ""
                        if markdown_file.exists():
                            with open(markdown_file, 'r', encoding='utf-8') as f:
                                full_text = f.read()
                        
                        documents.append({
                            'name': doc_dir.name,
                            'mode': mode,
                            'path': str(mode_dir),
                            'content_list_file': str(content_list_file),
                            'markdown_file': str(markdown_file),
                            'total_blocks': len(content_list),
                            'has_markdown': markdown_file.exists(),
                            'full_text_length': len(full_text)
                        })
                    except Exception as e:
                        logger.error(f"Failed to read {content_list_file}: {e}")
        
        return documents
    
    def _determine_slice_type(self, block: Dict[str, Any]) -> SliceType:
        """根据MinerU的block确定切片类型"""
        block_type = block.get('type', 'text')
        text_level = block.get('text_level', 0)
        
        # 根据type和text_level判断
        if block_type == 'image':
            return SliceType.IMAGE
        elif block_type == 'table':
            return SliceType.TABLE
        elif text_level > 0:  # text_level > 0 表示标题
            return SliceType.HEADER
        else:
            return SliceType.PARAGRAPH
    
    def import_document(
        self,
        db: Session,
        document_name: str,
        mode: str,
        project_id: Optional[str] = None,
        file_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        导入MinerU解析的文档
        
        Args:
            db: 数据库会话
            document_name: 文档名称（output目录下的子目录名）
            mode: 解析模式（vlm或pipeline）
            project_id: 关联的项目ID
            file_id: 关联的文件ID（如果已存在）
        
        Returns:
            导入结果统计
        """
        mode_dir = self.mineru_output_dir / document_name / mode
        if not mode_dir.exists():
            raise ValueError(f"Document not found: {document_name}/{mode}")
        
        content_list_file = mode_dir / f"{document_name}_content_list.json"
        markdown_file = mode_dir / f"{document_name}.md"
        
        if not content_list_file.exists():
            raise ValueError(f"Content list file not found: {content_list_file}")
        
        # 读取content_list.json
        with open(content_list_file, 'r', encoding='utf-8') as f:
            content_list = json.load(f)
        
        # 读取markdown全文
        full_text = ""
        if markdown_file.exists():
            with open(markdown_file, 'r', encoding='utf-8') as f:
                full_text = f.read()
        
        # 如果没有提供file_id，创建新的文件记录
        if not file_id:
            # 查找或创建文件记录
            # 尝试在pdfs目录找到原始PDF文件
            pdf_file = self.mineru_output_dir.parent / "pdfs" / f"{document_name}.pdf"
            
            # 计算文件hash（如果文件存在）
            import hashlib
            file_hash = f"mineru_{document_name}_{mode}"  # 简单hash标识
            if pdf_file.exists():
                with open(pdf_file, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
            
            file_data = {
                'filename': f"{document_name}.pdf",
                'original_filename': f"{document_name}.pdf",
                'file_path': str(pdf_file) if pdf_file.exists() else f"mineru/output/{document_name}",
                'file_hash': file_hash,
                'mime_type': 'application/pdf',
                'size': pdf_file.stat().st_size if pdf_file.exists() else 0,
                'ocr_status': OCRStatus.COMPLETED,
                'ocr_engine': f'mineru_{mode}',
                'ocr_result': full_text
            }
            
            if project_id:
                file_data['project_id'] = project_id
            
            file_record = file_service.create(db, obj_in=file_data)
            file_id = str(file_record.id)
            logger.info(f"Created file record: {file_id}")
        else:
            # 更新现有文件记录的OCR结果
            file_record = file_service.get(db, id=file_id)
            if not file_record:
                raise ValueError(f"File not found: {file_id}")
            
            file_service.update(db, db_obj=file_record, obj_in={
                'ocr_status': OCRStatus.COMPLETED,
                'ocr_engine': f'mineru_{mode}',
                'ocr_result': full_text
            })
            logger.info(f"Updated file record: {file_id}")
        
        # 删除现有切片（如果有）
        existing_slices = slice_service.get_by_file(db, file_id)
        for slice_obj in existing_slices:
            slice_service.remove(db, id=str(slice_obj.id))
        logger.info(f"Removed {len(existing_slices)} existing slices")
        
        # 导入切片
        slices_created = []
        stats = {
            'total_blocks': len(content_list),
            'imported_slices': 0,
            'skipped_blocks': 0,
            'slice_types': {}
        }
        
        for i, block in enumerate(content_list):
            try:
                block_type = block.get('type', 'text')
                text = block.get('text', '').strip()
                
                # 处理图片类型的block
                if block_type == 'image':
                    # 对于图片，使用图片说明作为内容
                    image_caption = block.get('image_caption', [])
                    image_path = block.get('img_path', '')
                    
                    if image_caption and len(image_caption) > 0:
                        # 使用图片说明
                        text = ' '.join(image_caption)
                    elif image_path:
                        # 如果没有说明，使用图片文件名
                        import os
                        image_filename = os.path.basename(image_path)
                        text = f"[图片: {image_filename}]"
                    else:
                        text = "[图片]"
                
                # 如果既没有文本也不是图片，跳过
                if not text and block_type != 'image':
                    stats['skipped_blocks'] += 1
                    continue
                
                slice_type = self._determine_slice_type(block)
                page_number = block.get('page_idx', 0) + 1  # page_idx从0开始
                bbox = block.get('bbox', [])
                
                # 计算偏移量（如果有bbox信息）
                start_offset = i * 1000  # 简单估算
                end_offset = start_offset + len(text) if text else start_offset + 100
                
                # 构建metadata，包含图片路径
                metadata = {
                    'mineru_type': block.get('type'),
                    'text_level': block.get('text_level'),
                    'bbox': bbox,
                    'mode': mode
                }
                
                # 如果是图片，添加图片相关信息到metadata
                if block_type == 'image':
                    if block.get('img_path'):
                        metadata['image_path'] = block.get('img_path')
                    if block.get('image_caption'):
                        metadata['image_caption'] = block.get('image_caption')
                    if block.get('image_footnote'):
                        metadata['image_footnote'] = block.get('image_footnote')
                
                slice_data = {
                    'file_id': file_id,
                    'content': text,
                    'slice_type': slice_type,
                    'page_number': page_number,
                    'sequence_number': i + 1,
                    'start_offset': start_offset,
                    'end_offset': end_offset,
                    'metadata': metadata
                }
                
                slice_record = slice_service.create(db, obj_in=slice_data)
                slices_created.append(slice_record)
                
                # 统计切片类型
                slice_type_value = slice_type.value
                stats['slice_types'][slice_type_value] = stats['slice_types'].get(slice_type_value, 0) + 1
                stats['imported_slices'] += 1
                
            except Exception as e:
                logger.error(f"Failed to import block {i}: {e}")
                stats['skipped_blocks'] += 1
        
        logger.info(f"Imported {stats['imported_slices']} slices for document {document_name}/{mode}")
        
        return {
            'file_id': file_id,
            'document_name': document_name,
            'mode': mode,
            'statistics': stats
        }
    
    def import_all_documents(
        self,
        db: Session,
        project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        导入所有可用的MinerU解析文档
        
        Args:
            db: 数据库会话
            project_id: 关联的项目ID
        
        Returns:
            导入结果列表
        """
        available_docs = self.get_available_documents()
        results = []
        
        for doc in available_docs:
            try:
                result = self.import_document(
                    db,
                    document_name=doc['name'],
                    mode=doc['mode'],
                    project_id=project_id
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to import {doc['name']}/{doc['mode']}: {e}")
                results.append({
                    'document_name': doc['name'],
                    'mode': doc['mode'],
                    'error': str(e)
                })
        
        return results


# 创建全局服务实例
mineru_import_service = MinerUImportService()
