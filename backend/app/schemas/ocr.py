"""
OCR相关的Pydantic模式
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from app.models.file import OCRStatus
from app.models.slice import SliceType


class OCREngineEnum(str, Enum):
    """OCR引擎枚举"""
    PADDLEOCR = "paddleocr"
    FALLBACK = "fallback"


class OCRStatusEnum(str, Enum):
    """OCR状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SliceTypeEnum(str, Enum):
    """切片类型枚举"""
    PARAGRAPH = "paragraph"
    IMAGE = "image"
    TABLE = "table"
    HEADER = "header"
    FOOTER = "footer"


class OCREngineInfo(BaseModel):
    """OCR引擎信息"""
    name: str
    available: bool
    description: str


class OCRRequest(BaseModel):
    """OCR处理请求"""
    file_id: str = Field(..., description="文件ID")
    engine: OCREngineEnum = Field(default=OCREngineEnum.PADDLEOCR, description="OCR引擎")
    user_id: Optional[str] = Field(None, description="用户ID")


class OCRResponse(BaseModel):
    """OCR处理响应"""
    task_id: str = Field(..., description="任务ID")
    file_id: str = Field(..., description="文件ID")
    engine: str = Field(..., description="使用的OCR引擎")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="状态消息")


class SliceBase(BaseModel):
    """切片基础模式"""
    content: str = Field(..., description="切片内容")
    slice_type: SliceTypeEnum = Field(..., description="切片类型")
    page_number: int = Field(default=1, description="页码")
    sequence_number: int = Field(..., description="序列号")
    start_offset: Optional[int] = Field(None, description="起始偏移量")
    end_offset: Optional[int] = Field(None, description="结束偏移量")


class SliceCreate(SliceBase):
    """创建切片模式"""
    file_id: str = Field(..., description="文件ID")


class SliceUpdate(BaseModel):
    """更新切片模式"""
    content: Optional[str] = Field(None, description="切片内容")
    slice_type: Optional[SliceTypeEnum] = Field(None, description="切片类型")


class SliceResponse(SliceBase):
    """切片响应模式"""
    id: str = Field(..., description="切片ID")
    file_id: str = Field(..., description="文件ID")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class FileSlicesResponse(BaseModel):
    """文件切片列表响应"""
    file_id: str = Field(..., description="文件ID")
    total_slices: int = Field(..., description="总切片数")
    slices: List[SliceResponse] = Field(..., description="切片列表")


class SliceContext(BaseModel):
    """切片上下文"""
    current_slice: SliceResponse = Field(..., description="当前切片")
    context_slices: List[SliceResponse] = Field(..., description="上下文切片")
    current_index: int = Field(..., description="当前索引")
    total_slices: int = Field(..., description="总切片数")
    file_id: str = Field(..., description="文件ID")


class OCRStatusInfo(BaseModel):
    """OCR状态信息"""
    file_id: str = Field(..., description="文件ID")
    filename: str = Field(..., description="文件名")
    ocr_status: OCRStatusEnum = Field(..., description="OCR状态")
    ocr_engine: Optional[str] = Field(None, description="OCR引擎")
    has_ocr_result: bool = Field(..., description="是否有OCR结果")
    text_length: int = Field(..., description="文本长度")
    slice_stats: Dict[str, Any] = Field(..., description="切片统计")


class SliceStats(BaseModel):
    """切片统计"""
    total_slices: int = Field(default=0, description="总切片数")
    paragraph_count: int = Field(default=0, description="段落数")
    header_count: int = Field(default=0, description="标题数")
    table_count: int = Field(default=0, description="表格数")
    image_count: int = Field(default=0, description="图片数")
    max_page: int = Field(default=0, description="最大页数")


class OCRTaskResult(BaseModel):
    """OCR任务结果"""
    file_id: str = Field(..., description="文件ID")
    engine: str = Field(..., description="OCR引擎")
    status: str = Field(..., description="处理状态")
    text_content: str = Field(..., description="提取的文本内容")
    total_pages: int = Field(..., description="总页数")
    slices_count: int = Field(..., description="切片数量")
    slices: List[Dict[str, Any]] = Field(..., description="切片摘要")


class ReprocessRequest(BaseModel):
    """重新处理请求"""
    engine: OCREngineEnum = Field(default=OCREngineEnum.PADDLEOCR, description="OCR引擎")
    user_id: Optional[str] = Field(None, description="用户ID")


class SliceSearchRequest(BaseModel):
    """切片搜索请求"""
    query: str = Field(..., min_length=1, description="搜索查询")
    project_id: str = Field(..., description="项目ID")
    limit: int = Field(default=50, ge=1, le=100, description="结果限制")


class SliceSearchResponse(BaseModel):
    """切片搜索响应"""
    query: str = Field(..., description="搜索查询")
    total_results: int = Field(..., description="总结果数")
    slices: List[SliceResponse] = Field(..., description="匹配的切片")