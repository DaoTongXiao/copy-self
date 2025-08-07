# -*- coding: utf-8 -*-
import pkgutil
import importlib
from .registry import get_tools, get_tool_map, register_tool

# 自动发现并导入此包中的所有模块以注册工具。
# 这可以确保在此目录下的任何.py文件中定义的、
# 并且使用了@register_tool装饰器的工具都会被自动注册。
for _, name, _ in pkgutil.iter_modules(__path__):
    if name != 'registry': # 避免重复导入注册表本身
        importlib.import_module(f".{name}", __package__)

__all__ = ['get_tools', 'get_tool_map', 'register_tool']