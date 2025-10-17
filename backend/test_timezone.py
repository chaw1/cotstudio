from app.core.timezone_utils import now, format_datetime
from app.core.database import SessionLocal
from app.models.file import File
import datetime

print("=" * 60)
print("时区测试")
print("=" * 60)

print(f"\n当前北京时间 (UTC+8): {now()}")
print(f"当前UTC时间: {datetime.datetime.now(datetime.timezone.utc)}")

db = SessionLocal()
file = db.query(File).order_by(File.created_at.desc()).first()

if file:
    print(f"\n最新文件: {file.filename}")
    print(f"数据库时间 (raw): {file.created_at}")
    print(f"数据库时间 (有时区信息): {file.created_at.tzinfo is not None}")
    print(f"格式化后: {format_datetime(file.created_at)}")
    
    # 检查时区
    if file.created_at.tzinfo:
        print(f"时区: {file.created_at.tzinfo}")
else:
    print("\n没有找到文件记录")

db.close()

print("\n=" * 60)
print("✅ 时区测试完成!")
print("=" * 60)
