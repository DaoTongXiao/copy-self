# -*- coding: utf-8 -*-
from langgraph.graph import StateGraph, END
from .state import AgentState
from .agents import Planner, Executor, FinalAnswerGenerator

def create_graph(llm):
    """Create the workflow graph."""
    planner = Planner(llm)
    executor = Executor()
    final_answer_generator = FinalAnswerGenerator(llm)

    workflow = StateGraph(AgentState)
    
    workflow.add_node("planner", planner)
    workflow.add_node("executor", executor)
    workflow.add_node("final_answer_generator", final_answer_generator)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "final_answer_generator")
    workflow.add_edge("final_answer_generator", END)

    return workflow.compile()