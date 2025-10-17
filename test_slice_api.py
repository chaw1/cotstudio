import requests

file_id = "cf5d8952-7b50-4011-9e43-8e9c1f422f48"
url = f"http://localhost:8000/api/v1/ocr/slices/{file_id}"
params = {"page": 1, "size": 10}

r = requests.get(url, params=params)
data = r.json()

print(f"成功: {data['success']}")
print(f"总数: {data['data']['total']}")
print(f"返回切片数: {len(data['data']['slices'])}")
print("\n前3个切片:")
for i, s in enumerate(data['data']['slices'][:3], 1):
    print(f"{i}. 类型={s['slice_type']}, 页={s['page_number']}, 序号={s['sequence_number']}")
    print(f"   内容: {s['content'][:80]}...")
    print()

# 检查图片切片
image_slices = [s for s in data['data']['slices'] if s['slice_type'] == 'image']
if image_slices:
    print(f"找到 {len(image_slices)} 个图片切片")
    print(f"第一个图片: {image_slices[0]['content'][:100]}...")
