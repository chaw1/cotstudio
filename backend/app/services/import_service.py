"""
导入服务
"""
import json
import os
import zipfile
import hashlib
import tempfile
import shutil
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models import Project, File, Slice, COTItem, COTCandidate, User
from ..models.project import ProjectStatus, ProjectType
from ..models.file import OCRStatus
from ..models.cot import COTSource, COTStatus
from ..schemas.import_schemas import (
    ImportRequest, ImportAnalysisResult, ImportResult, ImportValidationResult,
    DataDifference, DifferenceType, ImportMode, ConflictResolution
)
from ..schemas.export import ProjectExportData, ExportMetadata, COTExportItem
from ..core.config import settings
from .base_service import BaseService
from .export_service import ExportService


class ImportService(BaseService):
    """导入服务类"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.temp_dir = Path(tempfile.gettempdir()) / "cot_studio_imports"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def validate_import_file(self, file_path: str) -> ImportValidationResult:
        """
        验证导入文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        metadata = None
        estimated_items = {}
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                errors.append("文件不存在")
                return ImportValidationResult(
                    is_valid=False,
                    file_format="unknown",
                    data_integrity=False,
                    validation_errors=errors
                )
            
            # 检查文件格式
            file_format = self._detect_file_format(file_path)
            
            if file_format == "json":
                metadata, items_count, file_errors = await self._validate_json_import(file_path)
                errors.extend(file_errors)
                estimated_items = items_count
            elif file_format == "zip":
                metadata, items_count, file_errors, file_warnings = await self._validate_zip_import(file_path)
                errors.extend(file_errors)
                warnings.extend(file_warnings)
                estimated_items = items_count
            else:
                errors.append(f"不支持的文件格式: {file_format}")
            
            is_valid = len(errors) == 0
            data_integrity = is_valid and metadata is not None
            
            return ImportValidationResult(
                is_valid=is_valid,
                file_format=file_format,
                metadata=metadata,
                data_integrity=data_integrity,
                validation_errors=errors,
                warnings=warnings,
                estimated_items=estimated_items
            )
        
        except Exception as e:
            return ImportValidationResult(
                is_valid=False,
                file_format="unknown",
                data_integrity=False,
                validation_errors=[f"验证失败: {str(e)}"]
            )
    
    async def analyze_import_differences(
        self, 
        file_path: str, 
        target_project_id: Optional[str] = None
    ) -> ImportAnalysisResult:
        """
        分析导入数据与现有数据的差异
        
        Args:
            file_path: 导入文件路径
            target_project_id: 目标项目ID（可选）
            
        Returns:
            分析结果
        """
        try:
            # 加载导入数据
            import_data = await self._load_import_data(file_path)
            
            # 获取目标项目数据（如果指定）
            target_data = None
            if target_project_id:
                target_data = await self._load_project_data(target_project_id)
            
            # 分析差异
            differences = []
            conflicts = []
            
            if target_data:
                # 比较项目元数据
                project_diffs = self._compare_project_metadata(
                    import_data.metadata, target_data.metadata
                )
                differences.extend(project_diffs)
                
                # 比较CoT数据
                cot_diffs, cot_conflicts = self._compare_cot_data(
                    import_data.cot_items, target_data.cot_items
                )
                differences.extend(cot_diffs)
                conflicts.extend(cot_conflicts)
                
                # 比较文件数据
                file_diffs = self._compare_file_data(
                    import_data.files_info, target_data.files_info
                )
                differences.extend(file_diffs)
            else:
                # 新项目模式，所有数据都是新增
                differences = self._create_new_project_differences(import_data)
            
            # 统计信息
            statistics = {
                "total_differences": len(differences),
                "total_conflicts": len(conflicts),
                "new_items": len([d for d in differences if d.type == DifferenceType.NEW]),
                "modified_items": len([d for d in differences if d.type == DifferenceType.MODIFIED]),
                "deleted_items": len([d for d in differences if d.type == DifferenceType.DELETED])
            }
            
            return ImportAnalysisResult(
                is_valid=True,
                source_metadata=import_data.metadata.dict(),
                target_metadata=target_data.metadata.dict() if target_data else None,
                differences=differences,
                conflicts=conflicts,
                statistics=statistics
            )
        
        except Exception as e:
            return ImportAnalysisResult(
                is_valid=False,
                source_metadata={},
                validation_errors=[f"分析失败: {str(e)}"]
            )
    
    async def execute_import(
        self, 
        request: ImportRequest, 
        confirmed_differences: List[str],
        conflict_resolutions: Dict[str, ConflictResolution],
        current_user: User
    ) -> ImportResult:
        """
        执行导入操作
        
        Args:
            request: 导入请求
            confirmed_differences: 确认的差异ID列表
            conflict_resolutions: 冲突解决方案
            current_user: 当前用户
            
        Returns:
            导入结果
        """
        start_time = datetime.now()
        imported_items = {}
        skipped_items = {}
        errors = []
        warnings = []
        
        try:
            # 加载导入数据
            import_data = await self._load_import_data(request.file_path)
            
            # 确定目标项目
            if request.import_mode == ImportMode.CREATE_NEW:
                project = await self._create_new_project(import_data, request, current_user)
            elif request.import_mode == ImportMode.MERGE and request.target_project_id:
                project = self.db.query(Project).filter(Project.id == request.target_project_id).first()
                if not project:
                    raise ValueError(f"目标项目不存在: {request.target_project_id}")
            else:
                raise ValueError("无效的导入模式或缺少目标项目ID")
            
            # 导入文件数据
            file_stats = await self._import_files(
                import_data.files_info, project.id, confirmed_differences
            )
            imported_items.update(file_stats["imported"])
            skipped_items.update(file_stats["skipped"])
            
            # 导入CoT数据
            cot_stats = await self._import_cot_data(
                import_data.cot_items, project.id, confirmed_differences, 
                conflict_resolutions, current_user.username
            )
            imported_items.update(cot_stats["imported"])
            skipped_items.update(cot_stats["skipped"])
            errors.extend(cot_stats["errors"])
            warnings.extend(cot_stats["warnings"])
            
            # 导入知识图谱数据（如果有）
            if import_data.kg_data:
                kg_stats = await self._import_kg_data(import_data.kg_data, project.id)
                imported_items.update(kg_stats["imported"])
                skipped_items.update(kg_stats["skipped"])
            
            # 提交事务
            self.db.commit()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ImportResult(
                success=True,
                project_id=str(project.id),
                imported_items=imported_items,
                skipped_items=skipped_items,
                errors=errors,
                warnings=warnings,
                execution_time=execution_time
            )
        
        except Exception as e:
            self.db.rollback()
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ImportResult(
                success=False,
                project_id="",
                imported_items=imported_items,
                skipped_items=skipped_items,
                errors=[f"导入失败: {str(e)}"],
                warnings=warnings,
                execution_time=execution_time
            )
    
    def _detect_file_format(self, file_path: str) -> str:
        """检测文件格式"""
        if file_path.endswith('.json'):
            return "json"
        elif file_path.endswith('.zip'):
            return "zip"
        else:
            return "unknown"
    
    async def _validate_json_import(self, file_path: str) -> Tuple[Dict[str, Any], Dict[str, int], List[str]]:
        """验证JSON导入文件"""
        errors = []
        metadata = {}
        items_count = {}
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 检查必需字段
            required_fields = ["metadata", "cot_items", "files_info"]
            for field in required_fields:
                if field not in data:
                    errors.append(f"缺少必需字段: {field}")
            
            if "metadata" in data:
                metadata = data["metadata"]
                
            # 统计项目数量
            items_count = {
                "cot_items": len(data.get("cot_items", [])),
                "files": len(data.get("files_info", [])),
                "candidates": sum(len(item.get("candidates", [])) for item in data.get("cot_items", []))
            }
            
            # 验证CoT数据结构
            for i, item in enumerate(data.get("cot_items", [])):
                if not item.get("question"):
                    errors.append(f"CoT项 {i}: 缺少问题")
                if not item.get("candidates"):
                    errors.append(f"CoT项 {i}: 缺少候选答案")
        
        except json.JSONDecodeError as e:
            errors.append(f"无效的JSON格式: {str(e)}")
        except Exception as e:
            errors.append(f"验证错误: {str(e)}")
        
        return metadata, items_count, errors
    
    async def _validate_zip_import(self, file_path: str) -> Tuple[Dict[str, Any], Dict[str, int], List[str], List[str]]:
        """验证ZIP导入文件"""
        errors = []
        warnings = []
        metadata = {}
        items_count = {}
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                file_list = zipf.namelist()
                
                # 检查必需文件
                required_files = ["metadata.json", "data.json"]
                for required_file in required_files:
                    if required_file not in file_list:
                        errors.append(f"缺少必需文件: {required_file}")
                
                # 读取元数据
                if "metadata.json" in file_list:
                    try:
                        metadata_content = zipf.read("metadata.json")
                        metadata = json.loads(metadata_content.decode("utf-8"))
                    except Exception as e:
                        errors.append(f"无效的metadata.json: {str(e)}")
                
                # 读取主数据文件
                if "data.json" in file_list:
                    try:
                        data_content = zipf.read("data.json")
                        data = json.loads(data_content.decode("utf-8"))
                        
                        items_count = {
                            "cot_items": len(data.get("cot_items", [])),
                            "files": len(data.get("files_info", [])),
                            "candidates": sum(len(item.get("candidates", [])) for item in data.get("cot_items", []))
                        }
                    except Exception as e:
                        errors.append(f"无效的data.json: {str(e)}")
                
                # 检查可选文件
                optional_files = ["knowledge_graph.json", "data.md"]
                for optional_file in optional_files:
                    if optional_file not in file_list:
                        warnings.append(f"可选文件未找到: {optional_file}")
        
        except zipfile.BadZipFile:
            errors.append("无效的ZIP文件格式")
        except Exception as e:
            errors.append(f"包验证错误: {str(e)}")
        
        return metadata, items_count, errors, warnings
    
    async def _load_import_data(self, file_path: str) -> ProjectExportData:
        """加载导入数据"""
        file_format = self._detect_file_format(file_path)
        
        if file_format == "json":
            return await self._load_json_data(file_path)
        elif file_format == "zip":
            return await self._load_zip_data(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_format}")
    
    async def _load_json_data(self, file_path: str) -> ProjectExportData:
        """从JSON文件加载数据"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 转换为ProjectExportData对象
        metadata = ExportMetadata(**data["metadata"])
        cot_items = [COTExportItem(**item) for item in data["cot_items"]]
        
        return ProjectExportData(
            metadata=metadata,
            cot_items=cot_items,
            files_info=data["files_info"],
            kg_data=data.get("kg_data")
        )
    
    async def _load_zip_data(self, file_path: str) -> ProjectExportData:
        """从ZIP文件加载数据"""
        with zipfile.ZipFile(file_path, 'r') as zipf:
            # 读取主数据文件
            data_content = zipf.read("data.json")
            data = json.loads(data_content.decode("utf-8"))
            
            # 读取知识图谱数据（如果存在）
            kg_data = None
            if "knowledge_graph.json" in zipf.namelist():
                kg_content = zipf.read("knowledge_graph.json")
                kg_data = json.loads(kg_content.decode("utf-8"))
            
            # 转换为ProjectExportData对象
            metadata = ExportMetadata(**data["metadata"])
            cot_items = [COTExportItem(**item) for item in data["cot_items"]]
            
            return ProjectExportData(
                metadata=metadata,
                cot_items=cot_items,
                files_info=data["files_info"],
                kg_data=kg_data or data.get("kg_data")
            )
    
    async def _load_project_data(self, project_id: str) -> ProjectExportData:
        """加载现有项目数据"""
        # 使用导出服务获取项目数据
        export_service = ExportService(self.db)
        from ..schemas.export import ExportRequest, ExportFormat
        
        export_request = ExportRequest(
            project_id=project_id,
            format=ExportFormat.JSON,
            include_metadata=True,
            include_files=True,
            include_kg_data=True
        )
        
        return await export_service._collect_project_data(export_request)
    
    def _compare_project_metadata(
        self, 
        source_metadata: ExportMetadata, 
        target_metadata: ExportMetadata
    ) -> List[DataDifference]:
        """比较项目元数据"""
        differences = []
        
        # 比较项目名称
        if source_metadata.project_name != target_metadata.project_name:
            differences.append(DataDifference(
                id=f"project_name_{hash(source_metadata.project_name)}",
                type=DifferenceType.MODIFIED,
                category="project",
                field_name="name",
                current_value=target_metadata.project_name,
                new_value=source_metadata.project_name,
                description=f"项目名称从 '{target_metadata.project_name}' 更改为 '{source_metadata.project_name}'"
            ))
        
        # 比较项目描述
        if source_metadata.project_description != target_metadata.project_description:
            differences.append(DataDifference(
                id=f"project_description_{hash(str(source_metadata.project_description))}",
                type=DifferenceType.MODIFIED,
                category="project",
                field_name="description",
                current_value=target_metadata.project_description,
                new_value=source_metadata.project_description,
                description="项目描述已更改"
            ))
        
        return differences
    
    def _compare_cot_data(
        self, 
        source_items: List[COTExportItem], 
        target_items: List[COTExportItem]
    ) -> Tuple[List[DataDifference], List[DataDifference]]:
        """比较CoT数据"""
        differences = []
        conflicts = []
        
        # 创建目标项目的索引
        target_index = {item.id: item for item in target_items}
        source_index = {item.id: item for item in source_items}
        
        # 检查新增和修改的项目
        for source_item in source_items:
            if source_item.id not in target_index:
                # 新增项目
                differences.append(DataDifference(
                    id=f"cot_new_{source_item.id}",
                    type=DifferenceType.NEW,
                    category="cot_item",
                    new_value=source_item.dict(),
                    description=f"新增CoT项目: {source_item.question[:50]}..."
                ))
            else:
                # 检查修改
                target_item = target_index[source_item.id]
                item_diffs = self._compare_cot_item(source_item, target_item)
                differences.extend(item_diffs)
                
                # 检查冲突（例如，两个版本都有修改）
                if (source_item.status != target_item.status and 
                    source_item.status in [COTStatus.REVIEWED.value, COTStatus.APPROVED.value] and
                    target_item.status in [COTStatus.REVIEWED.value, COTStatus.APPROVED.value]):
                    conflicts.append(DataDifference(
                        id=f"cot_conflict_{source_item.id}",
                        type=DifferenceType.CONFLICT,
                        category="cot_item",
                        field_name="status",
                        current_value=target_item.status,
                        new_value=source_item.status,
                        description=f"CoT项目状态冲突: {source_item.question[:50]}...",
                        severity="high"
                    ))
        
        # 检查删除的项目
        for target_item in target_items:
            if target_item.id not in source_index:
                differences.append(DataDifference(
                    id=f"cot_deleted_{target_item.id}",
                    type=DifferenceType.DELETED,
                    category="cot_item",
                    current_value=target_item.dict(),
                    description=f"删除CoT项目: {target_item.question[:50]}..."
                ))
        
        return differences, conflicts
    
    def _compare_cot_item(self, source: COTExportItem, target: COTExportItem) -> List[DataDifference]:
        """比较单个CoT项目"""
        differences = []
        
        # 比较问题
        if source.question != target.question:
            differences.append(DataDifference(
                id=f"cot_question_{source.id}",
                type=DifferenceType.MODIFIED,
                category="cot_item",
                field_name="question",
                current_value=target.question,
                new_value=source.question,
                description="问题内容已修改"
            ))
        
        # 比较思维链
        if source.chain_of_thought != target.chain_of_thought:
            differences.append(DataDifference(
                id=f"cot_chain_{source.id}",
                type=DifferenceType.MODIFIED,
                category="cot_item",
                field_name="chain_of_thought",
                current_value=target.chain_of_thought,
                new_value=source.chain_of_thought,
                description="思维链已修改"
            ))
        
        # 比较状态
        if source.status != target.status:
            differences.append(DataDifference(
                id=f"cot_status_{source.id}",
                type=DifferenceType.MODIFIED,
                category="cot_item",
                field_name="status",
                current_value=target.status,
                new_value=source.status,
                description=f"状态从 {target.status} 更改为 {source.status}"
            ))
        
        # 比较候选答案
        candidate_diffs = self._compare_candidates(source.candidates, target.candidates, source.id)
        differences.extend(candidate_diffs)
        
        return differences
    
    def _compare_candidates(
        self, 
        source_candidates: List[Dict[str, Any]], 
        target_candidates: List[Dict[str, Any]], 
        cot_item_id: str
    ) -> List[DataDifference]:
        """比较候选答案"""
        differences = []
        
        # 创建索引
        target_index = {c["id"]: c for c in target_candidates}
        source_index = {c["id"]: c for c in source_candidates}
        
        # 检查新增和修改
        for source_candidate in source_candidates:
            candidate_id = source_candidate["id"]
            if candidate_id not in target_index:
                differences.append(DataDifference(
                    id=f"candidate_new_{candidate_id}",
                    type=DifferenceType.NEW,
                    category="candidate",
                    new_value=source_candidate,
                    description=f"新增候选答案: {source_candidate['text'][:30]}..."
                ))
            else:
                target_candidate = target_index[candidate_id]
                
                # 比较评分
                if source_candidate["score"] != target_candidate["score"]:
                    differences.append(DataDifference(
                        id=f"candidate_score_{candidate_id}",
                        type=DifferenceType.MODIFIED,
                        category="candidate",
                        field_name="score",
                        current_value=target_candidate["score"],
                        new_value=source_candidate["score"],
                        description=f"候选答案评分从 {target_candidate['score']} 更改为 {source_candidate['score']}"
                    ))
                
                # 比较chosen状态
                if source_candidate["chosen"] != target_candidate["chosen"]:
                    differences.append(DataDifference(
                        id=f"candidate_chosen_{candidate_id}",
                        type=DifferenceType.MODIFIED,
                        category="candidate",
                        field_name="chosen",
                        current_value=target_candidate["chosen"],
                        new_value=source_candidate["chosen"],
                        description=f"候选答案选择状态已更改"
                    ))
        
        # 检查删除
        for target_candidate in target_candidates:
            candidate_id = target_candidate["id"]
            if candidate_id not in source_index:
                differences.append(DataDifference(
                    id=f"candidate_deleted_{candidate_id}",
                    type=DifferenceType.DELETED,
                    category="candidate",
                    current_value=target_candidate,
                    description=f"删除候选答案: {target_candidate['text'][:30]}..."
                ))
        
        return differences
    
    def _compare_file_data(
        self, 
        source_files: List[Dict[str, Any]], 
        target_files: List[Dict[str, Any]]
    ) -> List[DataDifference]:
        """比较文件数据"""
        differences = []
        
        # 创建文件哈希索引
        target_hash_index = {f["file_hash"]: f for f in target_files}
        source_hash_index = {f["file_hash"]: f for f in source_files}
        
        # 检查新增文件
        for source_file in source_files:
            file_hash = source_file["file_hash"]
            if file_hash not in target_hash_index:
                differences.append(DataDifference(
                    id=f"file_new_{file_hash}",
                    type=DifferenceType.NEW,
                    category="file",
                    new_value=source_file,
                    description=f"新增文件: {source_file['filename']}"
                ))
        
        # 检查删除文件
        for target_file in target_files:
            file_hash = target_file["file_hash"]
            if file_hash not in source_hash_index:
                differences.append(DataDifference(
                    id=f"file_deleted_{file_hash}",
                    type=DifferenceType.DELETED,
                    category="file",
                    current_value=target_file,
                    description=f"删除文件: {target_file['filename']}"
                ))
        
        return differences
    
    def _create_new_project_differences(self, import_data: ProjectExportData) -> List[DataDifference]:
        """为新项目创建差异列表"""
        differences = []
        
        # 项目元数据
        differences.append(DataDifference(
            id="project_new",
            type=DifferenceType.NEW,
            category="project",
            new_value=import_data.metadata.dict(),
            description=f"创建新项目: {import_data.metadata.project_name}"
        ))
        
        # 文件
        for file_info in import_data.files_info:
            differences.append(DataDifference(
                id=f"file_new_{file_info['file_hash']}",
                type=DifferenceType.NEW,
                category="file",
                new_value=file_info,
                description=f"新增文件: {file_info['filename']}"
            ))
        
        # CoT项目
        for cot_item in import_data.cot_items:
            differences.append(DataDifference(
                id=f"cot_new_{cot_item.id}",
                type=DifferenceType.NEW,
                category="cot_item",
                new_value=cot_item.dict(),
                description=f"新增CoT项目: {cot_item.question[:50]}..."
            ))
        
        return differences
    
    async def _create_new_project(
        self, 
        import_data: ProjectExportData, 
        request: ImportRequest, 
        current_user: User
    ) -> Project:
        """创建新项目"""
        project_name = request.new_project_name or import_data.metadata.project_name
        
        project = Project(
            name=project_name,
            description=import_data.metadata.project_description,
            owner_id=current_user.id,
            project_type=ProjectType.STANDARD,
            status=ProjectStatus.ACTIVE
        )
        
        self.db.add(project)
        self.db.flush()  # 获取ID但不提交
        
        return project
    
    async def _import_files(
        self, 
        files_info: List[Dict[str, Any]], 
        project_id: str, 
        confirmed_differences: List[str]
    ) -> Dict[str, Dict[str, int]]:
        """导入文件数据"""
        imported = {"files": 0}
        skipped = {"files": 0}
        
        for file_info in files_info:
            file_hash = file_info["file_hash"]
            diff_id = f"file_new_{file_hash}"
            
            if diff_id in confirmed_differences:
                # 检查文件是否已存在
                existing_file = self.db.query(File).filter(
                    and_(File.project_id == project_id, File.file_hash == file_hash)
                ).first()
                
                if not existing_file:
                    file_obj = File(
                        project_id=project_id,
                        filename=file_info["filename"],
                        original_filename=file_info["filename"],
                        file_path=f"imported/{file_info['filename']}",  # 临时路径
                        file_hash=file_hash,
                        size=file_info["size"],
                        mime_type=file_info["mime_type"],
                        ocr_status=OCRStatus(file_info["ocr_status"])
                    )
                    
                    self.db.add(file_obj)
                    imported["files"] += 1
                else:
                    skipped["files"] += 1
            else:
                skipped["files"] += 1
        
        return {"imported": imported, "skipped": skipped}
    
    async def _import_cot_data(
        self, 
        cot_items: List[COTExportItem], 
        project_id: str, 
        confirmed_differences: List[str],
        conflict_resolutions: Dict[str, ConflictResolution],
        created_by: str
    ) -> Dict[str, Any]:
        """导入CoT数据"""
        imported = {"cot_items": 0, "candidates": 0}
        skipped = {"cot_items": 0, "candidates": 0}
        errors = []
        warnings = []
        
        for cot_item in cot_items:
            diff_id = f"cot_new_{cot_item.id}"
            
            if diff_id in confirmed_differences:
                try:
                    # 检查是否已存在
                    existing_cot = self.db.query(COTItem).filter(COTItem.id == cot_item.id).first()
                    
                    if not existing_cot:
                        # 创建新的CoT项目
                        cot_obj = COTItem(
                            project_id=project_id,
                            slice_id=cot_item.id,  # 临时使用，实际应该映射到正确的slice_id
                            question=cot_item.question,
                            chain_of_thought=cot_item.chain_of_thought,
                            source=COTSource(cot_item.source),
                            status=COTStatus(cot_item.status),
                            created_by=created_by
                        )
                        
                        self.db.add(cot_obj)
                        self.db.flush()  # 获取ID
                        
                        # 导入候选答案
                        for candidate_data in cot_item.candidates:
                            candidate = COTCandidate(
                                cot_item_id=str(cot_obj.id),
                                text=candidate_data["text"],
                                chain_of_thought=candidate_data.get("chain_of_thought"),
                                score=candidate_data["score"],
                                chosen=candidate_data["chosen"],
                                rank=candidate_data["rank"]
                            )
                            
                            self.db.add(candidate)
                            imported["candidates"] += 1
                        
                        imported["cot_items"] += 1
                    else:
                        # 处理冲突解决
                        conflict_id = f"cot_conflict_{cot_item.id}"
                        if conflict_id in conflict_resolutions:
                            resolution = conflict_resolutions[conflict_id]
                            if resolution.resolution == "use_new":
                                # 更新现有项目
                                existing_cot.question = cot_item.question
                                existing_cot.chain_of_thought = cot_item.chain_of_thought
                                existing_cot.status = COTStatus(cot_item.status)
                                imported["cot_items"] += 1
                            else:
                                skipped["cot_items"] += 1
                        else:
                            skipped["cot_items"] += 1
                
                except Exception as e:
                    errors.append(f"导入CoT项目失败 {cot_item.id}: {str(e)}")
                    skipped["cot_items"] += 1
            else:
                skipped["cot_items"] += 1
        
        return {
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
            "warnings": warnings
        }
    
    async def _import_kg_data(
        self, 
        kg_data: Dict[str, Any], 
        project_id: str
    ) -> Dict[str, Dict[str, int]]:
        """导入知识图谱数据"""
        imported = {"kg_entities": 0, "kg_relations": 0}
        skipped = {"kg_entities": 0, "kg_relations": 0}
        
        # 这里应该调用知识图谱服务来导入数据
        # 暂时返回空统计
        return {"imported": imported, "skipped": skipped}