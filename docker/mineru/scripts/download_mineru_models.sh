#!/bin/bash
# MinerU 模型下载脚本

set -e

echo "=========================================="
echo "MinerU 2.5 模型下载脚本"
echo "=========================================="

# 检查是否已存在模型
MODEL_DIR="/app/models"
if [ -d "$MODEL_DIR" ] && [ "$(ls -A $MODEL_DIR)" ]; then
    echo "✓ 模型目录已存在且非空，跳过下载"
    echo "模型位置: $MODEL_DIR"
    ls -lh "$MODEL_DIR"
    exit 0
fi

echo "→ 开始下载MinerU模型文件..."
echo "  这可能需要10-20分钟，请耐心等待..."

# 下载所有必要的模型
mineru-models-download --model_type all --save_path "$MODEL_DIR"

if [ $? -eq 0 ]; then
    echo "✓ 模型下载完成！"
    echo "模型大小:"
    du -sh "$MODEL_DIR"
    echo "模型列表:"
    find "$MODEL_DIR" -type f -name "*.bin" -o -name "*.pth" -o -name "*.onnx" | head -20
else
    echo "✗ 模型下载失败"
    exit 1
fi

echo "=========================================="
echo "模型下载完成，MinerU已就绪"
echo "=========================================="
