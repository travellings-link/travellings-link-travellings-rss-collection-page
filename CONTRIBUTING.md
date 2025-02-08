# 贡献指南

## 部署开发环境

### 在本地部署 Python3.12 环境

[Download Python](https://www.python.org/downloads/)

### 下载项目源码，并进入到项目根目录

```shell
git clone https://github.com/travellings-link/travellings-rss-collection-page && cd travellings-rss-collection-page/
```

### 创建虚拟环境

```shell
python -m venv .venv
```

### 进入虚拟环境

在 Windows 环境下

```powershell
./.venv/Scripts/activate
```

在 Bash

```shell
source ./.venv/bin/activate
```

附：退出虚拟环境的指令

```shell
deactivate
```

### 安装项目所需库

```shell
pip install -r requirements.txt
```

```shell
pip install -r requirements-dev.txt
```

创建 pre-commit 钩子，以便在每次提交前自动格式化代码

```shell
pre-commit install
```

### 启动项目

开发环境

```shell
python src/main.py
```

生产环境（gunicorn 仅支持 Linux）

```shell
gunicorn src/main:app
```

<!-- 附：导出当前虚拟环境中的库

```shell
pip freeze > requirements.txt
``` -->
