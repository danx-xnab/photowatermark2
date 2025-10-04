import os
import sys
import subprocess
import shutil

# 获取当前脚本所在目录
base_dir = os.path.dirname(os.path.abspath(__file__))

# 确保在虚拟环境中运行
venv_python = os.path.join(base_dir, 'venv', 'Scripts', 'python.exe')
if not os.path.exists(venv_python):
    print("错误：未找到虚拟环境。请先创建虚拟环境。")
    sys.exit(1)

# 安装PyInstaller
print("安装PyInstaller...")
subprocess.run([venv_python, '-m', 'pip', 'install', 'pyinstaller'], check=True)

# 安装项目依赖
print("安装项目依赖...")
requirements_path = os.path.join(base_dir, 'requirements.txt')
subprocess.run([venv_python, '-m', 'pip', 'install', '-r', requirements_path], check=True)

# 清理之前的构建文件
build_dir = os.path.join(base_dir, 'build')
dist_dir = os.path.join(base_dir, 'dist')
spec_file = os.path.join(base_dir, 'main.spec')

for path in [build_dir, dist_dir, spec_file]:
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

# 执行打包命令
print("开始打包应用...")
main_py = os.path.join(base_dir, 'src', 'main.py')

# 打包命令参数
pyinstaller_args = [
    venv_python,
    '-m', 'PyInstaller',
    '--onefile',  # 打包成单个文件
    '--windowed',  # 不显示控制台窗口
    '--name', 'PhotoWatermark',  # 应用名称
    # 不设置图标
    '--distpath', dist_dir,
    '--workpath', build_dir,
    main_py
]

# 执行打包
subprocess.run(pyinstaller_args, check=True)

# 创建templates目录（如果不存在）
templates_dir = os.path.join(dist_dir, 'templates')
os.makedirs(templates_dir, exist_ok=True)

print(f"\n打包完成！可执行文件位于：{os.path.join(dist_dir, 'PhotoWatermark.exe')}")