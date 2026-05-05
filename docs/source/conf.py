import os
import sys

project = 'cseslib4py'
copyright = '2025, MacrosMeng'
author = 'MacrosMeng'

sys.path.insert(0, os.path.abspath('../../'))

extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]

# 排除 Pydantic BaseModel 的 model_config 属性
autodoc_default_options = {
    'exclude-members': 'model_config',
}

templates_path = ['_templates']
exclude_patterns = []

language = 'zh-cn'

html_theme = 'furo'
html_static_path = ['_static']
