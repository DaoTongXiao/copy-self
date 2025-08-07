# -*- coding: utf-8 -*-
import time
from langchain_core.tools import tool
from utils.logger import logger
from .registry import register_tool

@register_tool
@tool
def search_internet(query: str) -> str:
    """Search the internet for information."""
    logger.info(f"--- Calling tool: search_internet(query='{query}') ---")
    # Simulate a search result
    if "sinner" in query.lower() and "hometown" in query.lower():
        return "Search results for \"hometown of 2024 Australian Open men's champion Sinner\": Jannik Sinner's hometown is Sesto, in the South Tyrol region of Italy."
    return f"Search results for \"{query}\": This year's Australian Open men's champion is Sinner."

@register_tool
@tool
def current_date() -> str:
    """Get the current date."""
    logger.info(f"--- Calling tool: current_date ---")
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())