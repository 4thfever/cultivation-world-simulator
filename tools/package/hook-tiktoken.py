"""
PyInstaller hook for tiktoken
确保 tiktoken 的编码数据和插件被正确打包
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 收集 tiktoken 的所有数据文件
datas = collect_data_files('tiktoken')

# 收集所有子模块，包括 tiktoken_ext
hiddenimports = collect_submodules('tiktoken')
hiddenimports += collect_submodules('tiktoken_ext')

# 确保核心编码被导入
hiddenimports += [
    'tiktoken.registry',
    'tiktoken.core',
    'tiktoken_ext.openai_public',
    'tiktoken_ext',
]

