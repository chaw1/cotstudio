"""
导入相关的Pydantic模式
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ImportStatus(str, Enum):
    """导入状态枚举"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPARING = "comparing"
    WAITING_CONFIRMATION = "waiting_confirmation"
    IMPORTING = "importing"
    COMPLETED = "completed"
    FAILED = "failed"


class DifferenceType(str, Enum):
    """差异类型枚举"""
    NEW = "new"           # 新增项
    MODIFIED = "modified" # 修改项
    DELETED = "deleted"   # 删除项
    CONFLICT = "conflict" # 冲突项


class ImportMode(str, Enum):
    """导入模式枚举"""
    MERGE = "merge"           # 合并模式
    REPLACE = "replace"       # 替换模式
    CREATE_NEW = "create_new" # 创建新项目模式


class ImportRequest(BaseModel):
    """导入请求模式"""
    file_path: str = Field(..., description="导入文件路径")
    import_mode: ImportMode = Field(default=ImportMode.MERGE, description="导入模式")
    target_project_id: Optional[str] = Field(default=None, description="目标项目ID（合并模式时使用）")
    new_project_name: Optional[str] = Field(default=None, description="新项目名称（创建新项目模式时使用）")
    conflict_resolution: Dict[str, str] = Field(default_factory=dict, description="冲突解决策略")


class ImportTaskResponse(BaseModel):
    """导入任务响应模式"""
    task_id: str = Field(..., description="任务ID")
    status: ImportStatus = Field(..., description="任务状态")
    progress: float = Field(default=0.0, description="进度百分比")
    message: Optional[str] = Field(default=None, description="状态消息")
    created_at: datetime = Field(..., description="创建时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    differences_summary: Optional[Dict[str, int]] = Field(default=None, description="差异摘要")


class DataDifference(BaseModel):
    """数据差异模式"""
    id: str = Field(..., description="差异项ID")
    type: DifferenceType = Field(..., description="差异类型")
    category: str = Field(..., description="数据类别（project/file/cot_item/candidate）")
    field_name: Optional[str] = Field(default=None, description="字段名称")
    current_value: Optional[Any] = Field(default=None, description="当前值")
    new_value: Optional[Any] = Field(default=None, description="新值")
    description: str = Field(..., description="差异描述")
    severity: str = Field(default="normal", description="严重程度（low/normal/high）")


class ImportAnalysisResult(BaseModel):
    """导入分析结果模式"""
    is_valid: bool = Field(..., description="数据是否有效")
    source_metadata: Dict[str, Any] = Field(..., description="源数据元信息")
    target_metadata: Optional[Dict[str, Any]] = Field(default=None, description="目标数据元信息")
    differences: List[DataDifference] = Field(default_factory=list, description="差异列表")
    conflicts: List[DataDifference] = Field(default_factory=list, description="冲突列表")
    validation_errors: List[str] = Field(default_factory=list, description="验证错误")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    statistics: Dict[str, int] = Field(default_factory=dict, description="统计信息")


class ImportConfirmation(BaseModel):
    """导入确认模式"""
    task_id: str = Field(..., description="任务ID")
    confirmed_differences: List[str] = Field(..., description="确认的差异ID列表")
    conflict_resolutions: Dict[str, str] = Field(default_factory=dict, description="冲突解决方案")
    import_settings: Dict[str, Any] = Field(default_factory=dict, description="导入设置")


class ImportResult(BaseModel):
    """导入结果模式"""
    success: bool = Field(..., description="是否成功")
    project_id: str = Field(..., description="项目ID")
    imported_items: Dict[str, int] = Field(default_factory=dict, description="导入项统计")
    skipped_items: Dict[str, int] = Field(default_factory=dict, description="跳过项统计")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")
    execution_time: float = Field(..., description="执行时间（秒）")


class ImportValidationResult(BaseModel):
    """导入验证结果模式"""
    is_valid: bool = Field(..., description="是否有效")
    file_format: str = Field(..., description="文件格式")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")
    data_integrity: bool = Field(..., description="数据完整性")
    validation_errors: List[str] = Field(default_factory=list, description="验证错误")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    estimated_items: Dict[str, int] = Field(default_factory=dict, description="预估项目数量")


class ConflictResolution(BaseModel):
    """冲突解决方案模式"""
    difference_id: str = Field(..., description="差异ID")
    resolution: str = Field(..., description="解决方案（keep_current/use_new/merge/skip）")
    custom_value: Optional[Any] = Field(default=None, description="自定义值")
    reason: Optional[str] = Field(default=None, description="解决原因")


class ImportProgress(BaseModel):
    """导入进度模式"""
    current_step: str = Field(..., description="当前步骤")
    total_steps: int = Field(..., description="总步骤数")
    current_step_progress: float = Field(default=0.0, description="当前步骤进度")
    overall_progress: float = Field(default=0.0, description="总体进度")
    estimated_remaining_time: Optional[int] = Field(default=None, description="预估剩余时间（秒）")
    processed_items: Dict[str, int] = Field(default_factory=dict, description="已处理项目")