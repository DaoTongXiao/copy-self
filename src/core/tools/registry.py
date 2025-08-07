# -*- coding: utf-8 -*-
from langchain_core.tools import BaseTool

_tools: list[BaseTool] = []
_tool_map: dict[str, BaseTool] = {}

def register(tool_func: BaseTool) -> BaseTool:
    """
    一个用于注册工具的装饰器。
    它应该应用于已经被@tool装饰器装饰过的函数所返回的对象。
    """
    if tool_func.name not in _tool_map:
        _tools.append(tool_func)
        _tool_map[tool_func.name] = tool_func
    return tool_func

def get_tools() -> list[BaseTool]:
    """返回已注册工具的列表。"""
    return _tools

def get_tool_map() -> dict[str, BaseTool]:
    """返回已注册工具的名称到工具对象的映射。"""
    return _tool_map