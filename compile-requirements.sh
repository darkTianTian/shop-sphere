#!/bin/bash

# 安装pip-tools
pip install pip-tools

# 生成完整的依赖文件
pip-compile --upgrade --output-file requirements.txt requirements-base.txt

# 生成开发环境依赖（可选）
# pip-compile --upgrade --output-file requirements-dev.txt requirements-dev.in

echo "依赖文件已更新！"
echo "使用 'pip-sync requirements.txt' 来安装依赖" 