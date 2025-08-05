# Example usage - you need to provide an llm instance
# Function to test various queries
from utils.logger import logger

def test_various_queries(llm):
    """Test various queries covering date, math, tool-chaining and clarification."""
    queries = [
        # 1) 基础日期能力：期待调用 current_date
        # "今年是多少年？",

        # 2) 简单算术：期待直接回答或用 sum_numbers 进行求和
        # "请计算 1.5 + 2.25 + 3.75 的和",

        # 3) 中等复杂计算：期待使用 factorial
        # "请计算 20 的阶乘",

        # 4) 大型计算：期待使用 fibonacci 并验证长计算能力
        # "请给出第 2000 个斐波那契数的值",

        # 5) 幂与开方：期待使用 power 和 sqrt 组合
        # "先计算 1.0001 的 100000 次幂，然后对结果开平方，分别给出两个数值",

        # 6) 参数澄清：触发 <clarification>，例如缺少参数的场景
        "请帮我计算阶乘",

        # 7) 工具链路：先用搜索工具获取今年澳网男单冠军和家乡，再组织答案
        # "今年澳网男单冠军是谁？他的家乡在哪里？需要先检索再回答",
    ]

    for i, query in enumerate(queries, 1):
        # logger.info(f"\n{'='*60}")
        # logger.info(f"Test {i}: {query}")
        # logger.info('='*60)
        run_react_agent(llm, query)

if __name__ == "__main__":
    from core.provider import llm  # Import your llm instance
    from core.agent import run_react_agent
    test_various_queries(llm)
