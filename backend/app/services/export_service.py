"""
导出服务
"""
import json
import os
import zipfile
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models import Project, File, Slice, COTItem, COTCandidate
from ..schemas.export import (
    ExportFormat, ExportRequest, ExportMetadata, COTExportItem, 
    ProjectExportData, ExportValidationResult
)
from ..core.config import settings
from .base_service import BaseService


class ExportService(BaseService):
    """导出服务类"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.export_dir = Path(settings.EXPORT_DIR or "exports")
        self.export_dir.mkdir(exist_ok=True)
    
    async def export_project(self, request: ExportRequest) -> str:
        """
        导出项目数据
        
        Args:
            request: 导出请求
            
        Returns:
            导出文件路径
        """
        # 获取项目数据
        project_data = await self._collect_project_data(request)
        
        # 根据格式导出
        if request.format == ExportFormat.JSON:
            return await self._export_json(project_data, request.project_id)
        elif request.format == ExportFormat.MARKDOWN:
            return await self._export_markdown(project_data, request.project_id)
        elif request.format == ExportFormat.LATEX:
            return await self._export_latex(project_data, request.project_id)
        elif request.format == ExportFormat.TXT:
            return await self._export_txt(project_data, request.project_id)
        else:
            raise ValueError(f"Unsupported export format: {request.format}")
    
    async def create_project_package(self, request: ExportRequest) -> str:
        """
        创建项目包（包含所有数据和元数据）
        
        Args:
            request: 导出请求
            
        Returns:
            项目包文件路径
        """
        project_data = await self._collect_project_data(request)
        
        # 创建临时目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        package_name = f"project_{request.project_id}_{timestamp}"
        temp_dir = self.export_dir / package_name
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # 导出各种格式的数据
            await self._export_json(project_data, request.project_id, temp_dir / "data.json")
            await self._export_markdown(project_data, request.project_id, temp_dir / "data.md")
            
            # 复制原始文件
            if request.include_files:
                await self._copy_original_files(project_data, temp_dir / "files")
            
            # 导出知识图谱数据
            if request.include_kg_data and project_data.kg_data:
                with open(temp_dir / "knowledge_graph.json", "w", encoding="utf-8") as f:
                    json.dump(project_data.kg_data, f, ensure_ascii=False, indent=2)
            
            # 创建元数据文件
            with open(temp_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(project_data.metadata.model_dump(), f, ensure_ascii=False, indent=2, default=str)
            
            # 创建ZIP包
            zip_path = self.export_dir / f"{package_name}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_dir)
                        zipf.write(file_path, arcname)
            
            return str(zip_path)
        
        finally:
            # 清理临时目录
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    async def validate_export_data(self, file_path: str) -> ExportValidationResult:
        """
        验证导出数据的完整性
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        total_items = 0
        
        try:
            # 计算文件校验和
            checksum = self._calculate_checksum(file_path)
            
            # 根据文件类型进行验证
            if file_path.endswith('.json'):
                total_items, file_errors = await self._validate_json_export(file_path)
                errors.extend(file_errors)
            elif file_path.endswith('.zip'):
                total_items, file_errors, file_warnings = await self._validate_package_export(file_path)
                errors.extend(file_errors)
                warnings.extend(file_warnings)
            
            is_valid = len(errors) == 0
            
            return ExportValidationResult(
                is_valid=is_valid,
                total_items=total_items,
                validation_errors=errors,
                warnings=warnings,
                checksum=checksum
            )
        
        except Exception as e:
            return ExportValidationResult(
                is_valid=False,
                total_items=0,
                validation_errors=[f"Validation failed: {str(e)}"],
                warnings=[],
                checksum=""
            )
    
    async def _collect_project_data(self, request: ExportRequest) -> ProjectExportData:
        """收集项目数据"""
        # 获取项目信息
        project = self.db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise ValueError(f"Project not found: {request.project_id}")
        
        # 获取CoT数据
        cot_query = self.db.query(COTItem).filter(COTItem.project_id == request.project_id)
        
        # 应用状态过滤
        if request.cot_status_filter:
            cot_query = cot_query.filter(COTItem.status.in_(request.cot_status_filter))
        
        cot_items = cot_query.all()
        
        # 构建导出数据
        export_items = []
        for cot_item in cot_items:
            # 获取关联的切片和文件信息
            slice_obj = self.db.query(Slice).filter(Slice.id == cot_item.slice_id).first()
            file_obj = self.db.query(File).filter(File.id == slice_obj.file_id).first() if slice_obj else None
            
            # 获取候选答案
            candidates = self.db.query(COTCandidate).filter(
                COTCandidate.cot_item_id == cot_item.id
            ).order_by(COTCandidate.rank).all()
            
            candidate_data = [
                {
                    "id": str(candidate.id),
                    "text": candidate.text,
                    "chain_of_thought": candidate.chain_of_thought,
                    "score": candidate.score,
                    "chosen": candidate.chosen,
                    "rank": candidate.rank
                }
                for candidate in candidates
            ]
            
            export_item = COTExportItem(
                id=str(cot_item.id),
                question=cot_item.question,
                chain_of_thought=cot_item.chain_of_thought,
                source=cot_item.source.value,
                status=cot_item.status.value,
                created_by=cot_item.created_by,
                created_at=cot_item.created_at,
                slice_content=slice_obj.content if slice_obj else "",
                slice_type=slice_obj.slice_type.value if slice_obj else "",
                file_name=file_obj.original_filename if file_obj else "",
                candidates=candidate_data
            )
            export_items.append(export_item)
        
        # 获取文件信息
        files = self.db.query(File).filter(File.project_id == request.project_id).all()
        files_info = [
            {
                "id": str(file.id),
                "filename": file.original_filename,
                "size": file.size,
                "mime_type": file.mime_type,
                "file_hash": file.file_hash,
                "ocr_status": file.ocr_status.value,
                "created_at": file.created_at.isoformat()
            }
            for file in files
        ]
        
        # 获取知识图谱数据（如果需要）
        kg_data = None
        if request.include_kg_data:
            # 这里应该调用知识图谱服务获取数据
            # kg_data = await self.kg_service.export_project_kg(request.project_id)
            kg_data = {"entities": [], "relations": [], "note": "KG export not implemented yet"}
        
        # 创建元数据
        metadata = ExportMetadata(
            project_name=project.name,
            project_description=project.description,
            export_format=request.format,
            export_timestamp=datetime.now(),
            total_files=len(files),
            total_cot_items=len(cot_items),
            total_candidates=sum(len(item.candidates) for item in export_items),
            export_settings=request.model_dump()
        )
        
        return ProjectExportData(
            metadata=metadata,
            cot_items=export_items,
            files_info=files_info,
            kg_data=kg_data
        )
    
    async def _export_json(self, data: ProjectExportData, project_id: str, output_path: Optional[Path] = None) -> str:
        """导出JSON格式"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.export_dir / f"project_{project_id}_{timestamp}.json"
        
        export_dict = {
            "metadata": data.metadata.model_dump(),
            "cot_items": [item.model_dump() for item in data.cot_items],
            "files_info": data.files_info,
            "kg_data": data.kg_data
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_dict, f, ensure_ascii=False, indent=2, default=str)
        
        return str(output_path)
    
    async def _export_markdown(self, data: ProjectExportData, project_id: str, output_path: Optional[Path] = None) -> str:
        """导出Markdown格式"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.export_dir / f"project_{project_id}_{timestamp}.md"
        
        content = []
        
        # 项目信息
        content.append(f"# {data.metadata.project_name}")
        content.append("")
        if data.metadata.project_description:
            content.append(data.metadata.project_description)
            content.append("")
        
        # 导出信息
        content.append("## 导出信息")
        content.append("")
        content.append(f"- **导出时间**: {data.metadata.export_timestamp}")
        content.append(f"- **文件数量**: {data.metadata.total_files}")
        content.append(f"- **CoT数据项**: {data.metadata.total_cot_items}")
        content.append(f"- **候选答案**: {data.metadata.total_candidates}")
        content.append("")
        
        # CoT数据
        content.append("## CoT数据")
        content.append("")
        
        for i, item in enumerate(data.cot_items, 1):
            content.append(f"### {i}. {item.question}")
            content.append("")
            content.append(f"**来源文件**: {item.file_name}")
            content.append(f"**状态**: {item.status}")
            content.append(f"**创建者**: {item.created_by}")
            content.append("")
            
            content.append("**原文片段**:")
            content.append(f"> {item.slice_content}")
            content.append("")
            
            if item.chain_of_thought:
                content.append("**思维链**:")
                content.append(item.chain_of_thought)
                content.append("")
            
            content.append("**候选答案**:")
            for candidate in item.candidates:
                chosen_mark = "✓" if candidate["chosen"] else ""
                content.append(f"{candidate['rank']}. {chosen_mark} **评分**: {candidate['score']}")
                content.append(f"   {candidate['text']}")
                if candidate["chain_of_thought"]:
                    content.append(f"   *思维链*: {candidate['chain_of_thought']}")
                content.append("")
            
            content.append("---")
            content.append("")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        
        return str(output_path)
    
    async def _export_latex(self, data: ProjectExportData, project_id: str, output_path: Optional[Path] = None) -> str:
        """导出LaTeX格式"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.export_dir / f"project_{project_id}_{timestamp}.tex"
        
        content = []
        
        # LaTeX文档头
        content.extend([
            "\\documentclass[12pt]{article}",
            "\\usepackage[utf8]{inputenc}",
            "\\usepackage{xeCJK}",
            "\\usepackage{geometry}",
            "\\usepackage{enumitem}",
            "\\usepackage{longtable}",
            "\\geometry{a4paper,margin=2cm}",
            "",
            "\\title{" + self._escape_latex(data.metadata.project_name) + "}",
            "\\author{CoT Studio Export}",
            "\\date{" + data.metadata.export_timestamp.strftime("%Y-%m-%d %H:%M:%S") + "}",
            "",
            "\\begin{document}",
            "\\maketitle",
            ""
        ])
        
        # 项目描述
        if data.metadata.project_description:
            content.extend([
                "\\section{项目描述}",
                self._escape_latex(data.metadata.project_description),
                ""
            ])
        
        # 导出统计
        content.extend([
            "\\section{导出统计}",
            "\\begin{itemize}",
            f"\\item 文件数量: {data.metadata.total_files}",
            f"\\item CoT数据项: {data.metadata.total_cot_items}",
            f"\\item 候选答案: {data.metadata.total_candidates}",
            "\\end{itemize}",
            ""
        ])
        
        # CoT数据
        content.extend([
            "\\section{CoT数据}",
            ""
        ])
        
        for i, item in enumerate(data.cot_items, 1):
            content.extend([
                f"\\subsection{{{i}. {self._escape_latex(item.question)}}}",
                "",
                f"\\textbf{{来源文件}}: {self._escape_latex(item.file_name)} \\\\",
                f"\\textbf{{状态}}: {item.status} \\\\",
                f"\\textbf{{创建者}}: {self._escape_latex(item.created_by)}",
                "",
                "\\textbf{原文片段}:",
                "\\begin{quote}",
                self._escape_latex(item.slice_content),
                "\\end{quote}",
                ""
            ])
            
            if item.chain_of_thought:
                content.extend([
                    "\\textbf{思维链}:",
                    self._escape_latex(item.chain_of_thought),
                    ""
                ])
            
            content.extend([
                "\\textbf{候选答案}:",
                "\\begin{enumerate}",
            ])
            
            for candidate in item.candidates:
                chosen_mark = "\\checkmark" if candidate["chosen"] else ""
                content.append(f"\\item {chosen_mark} \\textbf{{评分}}: {candidate['score']}")
                content.append(f"      {self._escape_latex(candidate['text'])}")
                if candidate["chain_of_thought"]:
                    content.append(f"      \\textit{{思维链}}: {self._escape_latex(candidate['chain_of_thought'])}")
            
            content.extend([
                "\\end{enumerate}",
                ""
            ])
        
        content.append("\\end{document}")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        
        return str(output_path)
    
    async def _export_txt(self, data: ProjectExportData, project_id: str, output_path: Optional[Path] = None) -> str:
        """导出纯文本格式"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.export_dir / f"project_{project_id}_{timestamp}.txt"
        
        content = []
        
        # 项目信息
        content.append(f"项目名称: {data.metadata.project_name}")
        content.append("=" * 50)
        content.append("")
        
        if data.metadata.project_description:
            content.append(f"项目描述: {data.metadata.project_description}")
            content.append("")
        
        # 导出信息
        content.append("导出信息:")
        content.append(f"  导出时间: {data.metadata.export_timestamp}")
        content.append(f"  文件数量: {data.metadata.total_files}")
        content.append(f"  CoT数据项: {data.metadata.total_cot_items}")
        content.append(f"  候选答案: {data.metadata.total_candidates}")
        content.append("")
        
        # CoT数据
        content.append("CoT数据:")
        content.append("-" * 50)
        content.append("")
        
        for i, item in enumerate(data.cot_items, 1):
            content.append(f"{i}. {item.question}")
            content.append("")
            content.append(f"   来源文件: {item.file_name}")
            content.append(f"   状态: {item.status}")
            content.append(f"   创建者: {item.created_by}")
            content.append("")
            
            content.append("   原文片段:")
            content.append(f"   > {item.slice_content}")
            content.append("")
            
            if item.chain_of_thought:
                content.append("   思维链:")
                content.append(f"   {item.chain_of_thought}")
                content.append("")
            
            content.append("   候选答案:")
            for candidate in item.candidates:
                chosen_mark = "[✓]" if candidate["chosen"] else "[ ]"
                content.append(f"   {candidate['rank']}. {chosen_mark} 评分: {candidate['score']}")
                content.append(f"      {candidate['text']}")
                if candidate["chain_of_thought"]:
                    content.append(f"      思维链: {candidate['chain_of_thought']}")
                content.append("")
            
            content.append("-" * 30)
            content.append("")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        
        return str(output_path)
    
    async def _copy_original_files(self, data: ProjectExportData, files_dir: Path):
        """复制原始文件"""
        files_dir.mkdir(exist_ok=True)
        
        for file_info in data.files_info:
            # 这里需要根据实际的文件存储路径来复制文件
            # 暂时跳过实际文件复制，只创建文件信息
            info_file = files_dir / f"{file_info['filename']}.info"
            with open(info_file, "w", encoding="utf-8") as f:
                json.dump(file_info, f, ensure_ascii=False, indent=2, default=str)
    
    def _escape_latex(self, text: str) -> str:
        """转义LaTeX特殊字符"""
        if not text:
            return ""
        
        replacements = {
            '\\': '\\textbackslash{}',
            '{': '\\{',
            '}': '\\}',
            '$': '\\$',
            '&': '\\&',
            '%': '\\%',
            '#': '\\#',
            '^': '\\textasciicircum{}',
            '_': '\\_',
            '~': '\\textasciitilde{}'
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text
    
    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    async def _validate_json_export(self, file_path: str) -> tuple[int, List[str]]:
        """验证JSON导出文件"""
        errors = []
        total_items = 0
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 检查必需字段
            required_fields = ["metadata", "cot_items", "files_info"]
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
            
            # 验证CoT数据
            if "cot_items" in data:
                total_items = len(data["cot_items"])
                for i, item in enumerate(data["cot_items"]):
                    if not item.get("question"):
                        errors.append(f"CoT item {i}: Missing question")
                    if not item.get("candidates"):
                        errors.append(f"CoT item {i}: Missing candidates")
        
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return total_items, errors
    
    async def _validate_package_export(self, file_path: str) -> tuple[int, List[str], List[str]]:
        """验证项目包导出文件"""
        errors = []
        warnings = []
        total_items = 0
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                file_list = zipf.namelist()
                
                # 检查必需文件
                required_files = ["metadata.json", "data.json"]
                for required_file in required_files:
                    if required_file not in file_list:
                        errors.append(f"Missing required file: {required_file}")
                
                # 验证metadata.json
                if "metadata.json" in file_list:
                    try:
                        metadata_content = zipf.read("metadata.json")
                        metadata = json.loads(metadata_content.decode("utf-8"))
                        total_items = metadata.get("total_cot_items", 0)
                    except Exception as e:
                        errors.append(f"Invalid metadata.json: {str(e)}")
                
                # 检查可选文件
                optional_files = ["data.md", "knowledge_graph.json"]
                for optional_file in optional_files:
                    if optional_file not in file_list:
                        warnings.append(f"Optional file not found: {optional_file}")
        
        except zipfile.BadZipFile:
            errors.append("Invalid ZIP file format")
        except Exception as e:
            errors.append(f"Package validation error: {str(e)}")
        
        return total_items, errors, warnings