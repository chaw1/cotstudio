"""
导出相关的Pydantic模式
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class ExportFormat(str, Enum):
    """导出格式枚举"""
    JSON = "json"
    MARKDOWN = "markdown"
    LATEX = "latex"
    TXT = "txt"


class ExportStatus(str, Enum):
    """导出状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportRequest(BaseModel):
    """导出请求模式"""
    project_id: str = Field(..., description="项目ID")
    format: ExportFormat = Field(..., description="导出格式")
    include_metadata: bool = Field(default=True, description="是否包含元数据")
    include_files: bool = Field(default=True, description="是否包含原始文件")
    include_kg_data: bool = Field(default=True, description="是否包含知识图谱数据")
    cot_status_filter: Optional[List[str]] = Field(default=None, description="CoT状态过滤")


class ExportTaskResponse(BaseModel):
    """导出任务响应模式"""
    task_id: str = Field(..., description="任务ID")
    status: ExportStatus = Field(..., description="任务状态")
    progress: float = Field(default=0.0, description="进度百分比")
    message: Optional[str] = Field(default=None, description="状态消息")
    download_url: Optional[str] = Field(default=None, description="下载链接")
    created_at: datetime = Field(..., description="创建时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")


class ExportMetadata(BaseModel):
    """导出元数据模式"""
    project_name: str
    project_description: Optional[str]
    export_format: ExportFormat
    export_timestamp: datetime
    total_files: int
    total_cot_items: int
    total_candidates: int
    export_settings: Dict[str, Any]


class COTExportItem(BaseModel):
    """CoT导出项模式"""
    id: str
    question: str
    chain_of_thought: Optional[str]
    source: str
    status: str
    created_by: str
    created_at: datetime
    slice_content: str
    slice_type: str
    file_name: str
    candidates: List[Dict[str, Any]]


class ProjectExportData(BaseModel):
    """项目导出数据模式"""
    metadata: ExportMetadata
    cot_items: List[COTExportItem]
    files_info: List[Dict[str, Any]]
    kg_data: Optional[Dict[str, Any]] = None


class ExportValidationResult(BaseModel):
    """导出验证结果模式"""
    is_valid: bool
    total_items: int
    validation_errors: List[str] = []
    warnings: List[str] = []
    checksum: str