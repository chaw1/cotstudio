from app.core.database import SessionLocal
from app.models.file import File
from app.models.slice import Slice

db = SessionLocal()

# 查找最近处理的文件
file = db.query(File).filter(File.ocr_status.in_(['processing', 'completed', 'failed'])).order_by(File.updated_at.desc()).first()

if file:
    print(f"文件: {file.filename}")
    print(f"OCR状态: {file.ocr_status}")
    print(f"OCR引擎: {file.ocr_engine}")
    print(f"创建时间: {file.created_at}")
    print(f"更新时间: {file.updated_at}")
    
    # 查看OCR结果
    if file.ocr_result:
        print(f"\nOCR结果长度: {len(file.ocr_result)} 字符")
        print(f"OCR结果预览: {file.ocr_result[:200]}...")
    else:
        print("\n⚠️ OCR结果为空!")
    
    # 查看切片
    slices = db.query(Slice).filter(Slice.file_id == file.id).all()
    print(f"\n切片总数: {len(slices)}")
    
    if slices:
        # 按类型统计
        from collections import Counter
        type_counts = Counter(s.slice_type for s in slices)
        print("\n切片类型分布:")
        for slice_type, count in type_counts.items():
            print(f"  {slice_type}: {count}")
        
        print("\n前5个切片:")
        for i, s in enumerate(slices[:5], 1):
            print(f"  {i}. {s.slice_type} (页{s.page_number}, 序号{s.sequence_number}): {len(s.content)} 字符")
            if s.content:
                print(f"     内容预览: {s.content[:100]}...")
    else:
        print("⚠️ 没有找到任何切片数据!")

else:
    print("没有找到最近处理的文件")

db.close()
