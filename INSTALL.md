# 安装指南 (Installation Guide)

本指南详细说明如何在不同操作系统上安装 HAADF-STEM Deconvolution 工具。

## 目录

- [系统要求](#系统要求)
- [快速安装](#快速安装)
- [详细安装](#详细安装)
  - [Linux](#linux)
  - [macOS](#macos)
  - [Windows](#windows)
- [依赖包说明](#依赖包说明)
- [常见安装问题](#常见安装问题)
- [开发环境配置](#开发环境配置)

## 系统要求

### 软件要求

- **Python**: 3.8 或更高版本（推荐 3.9 或 3.10）
- **pip**: Python 包管理器（通常随 Python 一起安装）
- **Git**: 用于克隆仓库（可选）

### 硬件要求

- **内存**: 最小 4GB，推荐 8GB 或更多
- **存储**: 至少 1GB 可用空间
- **CPU**: 支持多核处理器（Numba 可自动使用多核加速）

### 支持的操作系统

- Linux (Ubuntu, Fedora, CentOS, 等)
- macOS (10.15 Catalina 及更高版本)
- Windows 10/11

## 快速安装

如果您已经配置好 Python 环境，可以快速安装：

```bash
# 1. 克隆仓库
git clone https://github.com/chenguisen/dec_stem_for_computer.git
cd dec_stem_for_computer

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行程序
python deconvolution_gui.py
```

## 详细安装

### Linux

#### 安装 Python

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**Fedora/CentOS:**
```bash
sudo dnf install python3 python3-pip python3-venv
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip python-virtualenv
```

#### 安装系统依赖

某些包可能需要编译，需要安装构建工具：

```bash
# Ubuntu/Debian
sudo apt install build-essential gfortran

# Fedora
sudo dnf install gcc gcc-c++ gfortran

# CentOS
sudo yum groupinstall "Development Tools"
sudo yum install gfortran
```

#### 创建虚拟环境并安装

```bash
# 克隆仓库
git clone https://github.com/chenguisen/dec_stem_for_computer.git
cd dec_stem_for_computer

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 运行程序
python deconvolution_gui.py
```

### macOS

#### 安装 Python

**推荐使用 Homebrew:**
```bash
# 安装 Homebrew（如果未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Python
brew install python@3.10
```

**或者使用官方安装包:**
从 https://www.python.org/downloads/ 下载 macOS 安装包

#### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/chenguisen/dec_stem_for_computer.git
cd dec_stem_for_computer

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 运行程序
python deconvolution_gui.py
```

#### 注意事项

- macOS 可能需要安装 Xcode 命令行工具：`xcode-select --install`
- 如果遇到编译错误，确保已安装最新的 Xcode

### Windows

#### 安装 Python

1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.9 或 3.10 的 Windows 安装包
3. 运行安装程序，**重要：勾选 "Add Python to PATH"**
4. 完成安装

#### 安装 Visual C++ 编译工具（可选）

某些 Python 包需要编译，建议安装：

```powershell
# 以管理员身份运行 PowerShell，执行：
winget install Microsoft.VisualStudio.2022.BuildTools
# 或下载安装: https://visualstudio.microsoft.com/downloads/
```

#### 使用 Git 克隆（可选）

**方法 1: 使用 Git 命令行**
```powershell
# 安装 Git: https://git-scm.com/download/win
git clone https://github.com/chenguisen/dec_stem_for_computer.git
cd dec_stem_for_computer
```

**方法 2: 直接下载**
1. 访问 https://github.com/chenguisen/dec_stem_for_computer
2. 点击 "Code" -> "Download ZIP"
3. 解压缩到本地目录

#### 创建虚拟环境并安装

```powershell
# 打开命令提示符或 PowerShell，进入项目目录
cd dec_stem_for_computer

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# PowerShell:
venv\Scripts\Activate.ps1
# 或命令提示符:
venv\Scripts\activate.bat

# 升级 pip
python -m pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 运行程序
python deconvolution_gui.py
```

#### Windows PowerShell 执行策略问题

如果遇到 "execution of scripts is disabled" 错误：

```powershell
# 以管理员身份运行 PowerShell，执行：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 依赖包说明

### 必需包

| 包名 | 用途 | 依赖 |
|------|------|------|
| PyQt6 | 图形界面框架 | 无 |
| numpy | 数值计算 | 无 |
| scipy | 科学计算 | numpy |
| matplotlib | 数据可视化 | numpy |
| mrcfile | MRC 文件读写 | numpy |

### 可选包

| 包名 | 用途 | 说明 |
|------|------|------|
| numba | 性能加速 | 使用 JIT 编译，大幅提升计算速度 |
| scikit-image | 图像处理 | 提供额外的图像处理算法 |
| tqdm | 进度显示 | 命令行工具的进度条 |

### 最小安装

如果只需要基本功能，可以只安装必需包：

```bash
pip install PyQt6 numpy scipy matplotlib mrcfile
```

## 常见安装问题

### 问题 1: pip 版本过旧

**错误信息**: `WARNING: You are using pip version X, however version Y is available.`

**解决方案**:
```bash
python -m pip install --upgrade pip
```

### 问题 2: 权限错误

**错误信息**: `Permission denied` 或 `Access denied`

**解决方案**:
- Linux/macOS: 在命令前加 `sudo`（不推荐）
- 更好的方法：使用虚拟环境（推荐）

### 问题 3: 编译错误

**错误信息**: `Microsoft Visual C++ 14.0 is required` 或类似错误

**解决方案**:
- Windows: 安装 Visual C++ Build Tools
- Linux: 安装 `build-essential` 和 `gfortran`
- macOS: 安装 Xcode 命令行工具

### 问题 4: PyQt6 安装失败

**解决方案**:
```bash
# 尝试使用预编译的 wheel 包
pip install PyQt6 --prefer-binary

# 如果仍失败，使用 conda
conda install pyqt
```

### 问题 5: numpy/scipy 版本冲突

**解决方案**:
```bash
# 清理旧版本
pip uninstall numpy scipy

# 重新安装
pip install numpy scipy
```

### 问题 6: mrcfile 导入错误

**错误信息**: `ImportError: No module named 'mrcfile'`

**解决方案**:
```bash
pip install mrcfile
```

### 问题 7: 虚拟环境激活失败

**Linux/macOS**: 确保安装了 `python3-venv`
```bash
# Ubuntu/Debian
sudo apt install python3-venv

# Fedora
sudo dnf install python3-virtualenv
```

**Windows**: 确保使用正确的激活脚本
```powershell
# PowerShell
venv\Scripts\Activate.ps1

# CMD
venv\Scripts\activate.bat
```

## 开发环境配置

### 安装开发工具

```bash
# 激活虚拟环境后，安装开发依赖
pip install pytest pylint black flake8 mypy

# 或者创建 requirements-dev.txt
cat > requirements-dev.txt << EOF
pytest>=7.0.0
pylint>=2.13.0
black>=22.0.0
flake8>=4.0.0
mypy>=0.940
EOF

pip install -r requirements-dev.txt
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest test_deconv.py

# 生成覆盖率报告
pytest --cov=stem_deconv --cov-report=html
```

### 代码格式化

```bash
# 使用 Black 格式化代码
black stem_deconv/ *.py

# 使用 Pylint 检查代码质量
pylint stem_deconv/
```

## 验证安装

安装完成后，运行以下命令验证：

```bash
# 检查 Python 版本
python --version

# 检查已安装的包
pip list

# 测试导入
python -c "import numpy, scipy, matplotlib, PyQt6; print('All imports successful!')"

# 运行 GUI
python deconvolution_gui.py
```

如果 GUI 正常启动，说明安装成功！

## 卸载

### 卸载软件包

```bash
# 卸载所有包
pip uninstall -y PyQt6 numpy scipy matplotlib mrcfile numba scikit-image tqdm

# 或者删除虚拟环境（推荐）
deactivate  # 如果虚拟环境已激活
rm -rf venv  # Linux/macOS
rmdir /s venv  # Windows
```

### 完全删除项目

```bash
cd ..
rm -rf dec_stem_for_computer  # Linux/macOS
rmdir /s dec_stem_for_computer  # Windows
```

## 下一步

安装完成后，请阅读 [README.md](README.md) 了解如何使用本工具。

如有问题，请访问 [GitHub Issues](https://github.com/chenguisen/dec_stem_for_computer/issues) 提交问题。
