# -*- coding: utf-8 -*-
import re
import operator
import time
import json
from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from core.prompt import planner_system_prompt_template, final_answer_prompt_template
from utils.logger import logger

# --- State Definition ---
class AgentState(TypedDict):
    question: str
    plan: List[str]
    observations: Annotated[list, operator.add]
    final_answer: str
    recursion_limit: int

# --- Tools ---
@tool
def search_internet(query: str) -> str:
    """Search the internet for information."""
    logger.info(f"--- Calling tool: search_internet(query='{query}') ---")
    # Simulate a search result
    if "sinner" in query.lower() and "hometown" in query.lower():
        return "Search results for \"hometown of 2024 Australian Open men's champion Sinner\": Jannik Sinner's hometown is Sesto, in the South Tyrol region of Italy."
    return f"Search results for \"{query}\": This year's Australian Open men's champion is Sinner."

@tool
def current_date() -> str:
    """Get the current date."""
    logger.info(f"--- Calling tool: current_date ---")
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

# --- Plan-and-Execute Agent ---
class PlanExecuteAgent:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self.tool_map = {tool.name: tool for tool in self.tools}

    def get_tool_list_str(self):
        return "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])

    def planner(self, state: AgentState):
        """Generates an execution plan."""
        logger.info("\n=== Generating Plan ===")
        question = state['question']
        tool_list = self.get_tool_list_str()

        prompt = planner_system_prompt_template.format(
            tool_list=tool_list,
            question=question
        )
        
        response = self.llm.invoke(prompt)
        plan_str = response.content.strip()
        
        try:
            # The model might return a markdown code block
            cleaned_plan_str = re.sub(r"```json\n|\n```", "", plan_str)
            plan = json.loads(cleaned_plan_str)
            logger.info(f"Generated Plan: {plan}")
            logger.info("======================")
            return {"plan": plan}
        except json.JSONDecodeError:
            error_msg = f"Error: Planner did not return a valid JSON list. Output: {plan_str}"
            logger.error(error_msg)
            return {"final_answer": error_msg}

    def executor(self, state: AgentState):
        """Executes the tools in the plan."""
        logger.info("\n=== Executing Plan ===")
        plan = state.get('plan', [])
        observations = []

        for i, step in enumerate(plan):
            logger.info(f"--- Step {i+1}/{len(plan)}: {step} ---")
            
            match = re.match(r"(\w+)\((.*)\)", step)
            if not match:
                observation = f"Error: Could not parse action format: {step}"
                logger.error(observation)
                observations.append(observation)
                continue

            tool_name, args_str = match.groups()
            tool_to_call = self.tool_map.get(tool_name)

            if not tool_to_call:
                observation = f"Error: Tool '{tool_name}' not found."
                logger.error(observation)
                observations.append(observation)
                continue

            try:
                tool_input = {}
                if args_str.strip():
                    # This regex is simplified and might need to be more robust
                    param_matches = re.findall(r'(\w+)=["\'](.*?)["\']', args_str)
                    if param_matches:
                        tool_input = dict(param_matches)

                result = tool_to_call.invoke(tool_input)
                observation = str(result)
                logger.info(f"Observation: {observation}")
            except Exception as e:
                observation = f"Error executing tool '{tool_name}': {e}"
                logger.error(observation)
            
            observations.append(observation)
            logger.info("--------------------")

        return {"observations": observations}

    def generate_final_answer(self, state: AgentState):
        """Generates the final answer based on observations."""
        logger.info("\n=== Generating Final Answer ===")
        question = state['question']
        observations = state['observations']

        history = ""
        for i, obs in enumerate(observations):
            history += f"Step {i+1} Observation: {obs}\n"

        prompt = final_answer_prompt_template.format(
            history=history.strip(),
            question=question
        )

        response = self.llm.invoke(prompt)
        final_answer = response.content.strip()
        
        logger.info(f"🎯 Final Answer: {final_answer}")
        logger.info("===========================")
        return {"final_answer": final_answer}

def create_graph(llm):
    """Create the workflow graph."""
    tools = [search_internet, current_date]
    agent = PlanExecuteAgent(llm, tools)

    workflow = StateGraph(AgentState)
    
    workflow.add_node("planner", agent.planner)
    workflow.add_node("executor", agent.executor)
    workflow.add_node("final_answer_generator", agent.generate_final_answer)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "final_answer_generator")
    workflow.add_edge("final_answer_generator", END)

    return workflow.compile()

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
