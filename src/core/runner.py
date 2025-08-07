# -*- coding: utf-8 -*-
from .graph import create_graph
from .state import AgentState
from utils.logger import logger

def run_plan_execute_agent(llm, query: str = "Where is the hometown of this year's Australian Open men's champion?"):
    """Run the Plan-and-Execute Agent."""
    app = create_graph(llm)

    initial_state: AgentState = {
        "question": query,
        "observations": [],
        "plan": [],
        "final_answer": "",
        "recursion_limit": 10
    }

    logger.info(f"=== Starting Plan-and-Execute Agent ===")
    logger.info(f"Query: {query}")
    logger.info("=" * 50)

    try:
        final_state = app.invoke(initial_state, {"recursion_limit": 10})
        
        logger.info("\n=== Plan-and-Execute Agent Finished ===")
        # The final answer is already logged in the generate_final_answer node
        
    except Exception as e:
        logger.error(f"\nAn error occurred during execution: {e}")
        import traceback
        traceback.print_exc()