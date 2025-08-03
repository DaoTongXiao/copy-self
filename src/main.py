# Example usage - you need to provide an llm instance
# Function to test various queries
from utils.logger import logger

def test_various_queries(llm):
    """Test various queries."""
    queries = [
      "今年是多少年？"
    ]

    for i, query in enumerate(queries, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Test {i}: {query}")
        logger.info('='*60)
        run_react_agent(llm, query)

if __name__ == "__main__":
    from core.provider import llm  # Import your llm instance
    from core.agent import run_react_agent
    test_various_queries(llm)