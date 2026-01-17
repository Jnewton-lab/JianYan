# PyInstaller hook for funasr
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# 收集 funasr 的所有内容
datas, binaries, hiddenimports = collect_all('funasr')

# 额外收集可能遗漏的子模块
hiddenimports += collect_submodules('funasr.models')
hiddenimports += collect_submodules('funasr.auto')
hiddenimports += collect_submodules('funasr.bin')
hiddenimports += collect_submodules('funasr.frontends')
hiddenimports += collect_submodules('funasr.utils')
hiddenimports += ['funasr.register']

# 添加 funasr 运行时需要的数据文件
datas += collect_data_files('funasr', include_py_files=True)
