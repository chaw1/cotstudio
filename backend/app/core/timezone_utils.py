"""
时区处理工具模块
统一处理所有时区相关的操作,确保系统使用北京时间(UTC+8)
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def now() -> datetime:
    """
    获取当前北京时间
    
    Returns:
        datetime: 带时区信息的当前北京时间
    """
    return datetime.now(BEIJING_TZ)

def utcnow() -> datetime:
    """
    获取当前UTC时间(保留此函数用于向后兼容,但建议使用now())
    
    Returns:
        datetime: 带时区信息的当前UTC时间
    """
    return datetime.now(timezone.utc)

def to_beijing_time(dt: Optional[datetime]) -> Optional[datetime]:
    """
    将任意时区的datetime转换为北京时间
    
    Args:
        dt: 要转换的datetime对象
        
    Returns:
        datetime: 北京时间,如果输入为None则返回None
    """
    if dt is None:
        return None
    
    # 如果是naive datetime(无时区信息),假设为UTC时间
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # 转换为北京时间
    return dt.astimezone(BEIJING_TZ)

def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    将任意时区的datetime转换为UTC时间
    
    Args:
        dt: 要转换的datetime对象
        
    Returns:
        datetime: UTC时间,如果输入为None则返回None
    """
    if dt is None:
        return None
    
    # 如果是naive datetime,假设为北京时间
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=BEIJING_TZ)
    
    # 转换为UTC
    return dt.astimezone(timezone.utc)

def format_datetime(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化datetime为字符串(自动转换为北京时间)
    
    Args:
        dt: 要格式化的datetime对象
        fmt: 格式字符串
        
    Returns:
        str: 格式化后的字符串,如果输入为None则返回空字符串
    """
    if dt is None:
        return ""
    
    beijing_dt = to_beijing_time(dt)
    return beijing_dt.strftime(fmt)

def parse_datetime(dt_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    解析字符串为datetime(假设为北京时间)
    
    Args:
        dt_str: 时间字符串
        fmt: 格式字符串
        
    Returns:
        datetime: 带北京时区信息的datetime对象
    """
    dt = datetime.strptime(dt_str, fmt)
    return dt.replace(tzinfo=BEIJING_TZ)

def get_beijing_timezone():
    """
    获取北京时区对象
    
    Returns:
        timezone: 北京时区(UTC+8)
    """
    return BEIJING_TZ
