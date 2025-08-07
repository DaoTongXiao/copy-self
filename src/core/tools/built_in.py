# -*- coding: utf-8 -*-
import time
import math
from langchain_core.tools import tool
from utils.logger import logger
from .registry import register

@register
@tool
def search_internet(query: str) -> str:
    """Search the internet for information."""
    logger.info(f"--- Calling tool: search_internet(query='{query}') ---")
    # Simulate a search result
    if "sinner" in query.lower() and "hometown" in query.lower():
        return "Search results for \"hometown of 2024 Australian Open men's champion Sinner\": Jannik Sinner's hometown is Sesto, in the South Tyrol region of Italy."
    return f"Search results for \"{query}\": This year's Australian Open men's champion is Sinner."

@register
@tool
def current_date() -> str:
    """Get the current date."""
    logger.info(f"--- Calling tool: current_date ---")
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

@register
@tool
def factorial(n: int) -> int:
    """Compute n! (factorial). n must be a non-negative integer."""
    logger.info(f"--- Calling tool: factorial(n={n}) ---")
    if n < 0:
        raise ValueError("n must be non-negative")
    # Use math.factorial for correctness and performance
    return math.factorial(n)

@register
@tool
def fibonacci(n: int) -> int:
    """Compute the nth Fibonacci number (F0=0, F1=1). n must be a non-negative integer."""
    logger.info(f"--- Calling tool: fibonacci(n={n}) ---")
    if n < 0:
        raise ValueError("n must be non-negative")
    # Fast doubling algorithm for large n
    def _fib(k: int) -> tuple[int, int]:
        if k == 0:
            return (0, 1)
        a, b = _fib(k // 2)
        c = a * (2 * b - a)
        d = a * a + b * b
        if k % 2 == 0:
            return (c, d)
        else:
            return (d, c + d)
    return _fib(n)[0]

@register
@tool
def sum_numbers(numbers: list[float]) -> float:
    """Sum a list of numbers. Example: sum_numbers(numbers=[1,2,3.5])"""
    logger.info(f"--- Calling tool: sum_numbers(numbers={numbers}) ---")
    return float(math.fsum(numbers))

@register
@tool
def power(base: float, exponent: float) -> float:
    """Compute base ** exponent (supports floats)."""
    logger.info(f"--- Calling tool: power(base={base}, exponent={exponent}) ---")
    return float(math.pow(base, exponent))

@register
@tool
def sqrt(x: float) -> float:
    """Compute the square root of x (x must be non-negative)."""
    logger.info(f"--- Calling tool: sqrt(x={x}) ---")
    if x < 0:
        raise ValueError("x must be non-negative")
    return float(math.sqrt(x))
