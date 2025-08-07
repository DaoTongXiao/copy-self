# -*- coding: utf-8 -*-
# Example usage - you need to provide an llm instance
# Function to test various queries
from utils.logger import logger

def test_various_queries(llm):
    """Test various queries."""
    queries = [
      "查询北京的天气？"
    ]

    for i, query in enumerate(queries, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Test {i}: {query}")
        logger.info('='*60)
        run_plan_execute_agent(llm, query)

if __name__ == "__main__":
    from core.llm_provider import llm  # Import your llm instance
    from core.runner import run_plan_execute_agent
    test_various_queries(llm)