from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = ['utils','lxml._elementpath'], excludes = [])

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('tag_it.py', base=base)
]

setup(name='TagIt',
      version = '1.0',
      description = 'Tags a movie script',
      options = dict(build_exe = buildOptions),
      executables = executables)
