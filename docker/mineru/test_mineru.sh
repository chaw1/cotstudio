#!/bin/bash
# MinerU测试脚本 - 在容器内直接测试mineru命令

set -e

echo "================================"
echo "MinerU 直接测试"
echo "================================"

# 检查是否有测试PDF
if [ ! -f "/tmp/test.pdf" ]; then
    echo "错误: 找不到 /tmp/test.pdf"
    echo "请先上传一个PDF文件到容器的 /tmp 目录"
    exit 1
fi

echo "1. 创建输出目录"
mkdir -p /tmp/test_output
rm -rf /tmp/test_output/*

echo "2. 检查输入文件"
ls -lh /tmp/test.pdf

echo "3. 执行mineru命令"
echo "命令: mineru -p /tmp/test.pdf -o /tmp/test_output --backend pipeline --device cuda --batch-size 8"

# 记录开始时间
start_time=$(date +%s)

# 执行命令并捕获输出
set +e
mineru -p /tmp/test.pdf -o /tmp/test_output --backend pipeline --device cuda --batch-size 8 2>&1 | tee /tmp/mineru_test.log
exit_code=$?
set -e

# 记录结束时间
end_time=$(date +%s)
duration=$((end_time - start_time))

echo ""
echo "4. 命令执行结果"
echo "退出码: $exit_code"
echo "执行时间: ${duration}秒"

echo ""
echo "5. 输出目录内容"
echo "目录结构:"
find /tmp/test_output -type f -o -type d | head -50

echo ""
echo "6. 查找markdown文件"
find /tmp/test_output -name "*.md" -exec ls -lh {} \;

echo ""
echo "7. 如果有markdown文件,显示前100行"
md_file=$(find /tmp/test_output -name "*.md" | head -1)
if [ -n "$md_file" ]; then
    echo "找到文件: $md_file"
    head -100 "$md_file"
else
    echo "未找到markdown文件"
fi

echo ""
echo "================================"
echo "测试完成"
echo "================================"
