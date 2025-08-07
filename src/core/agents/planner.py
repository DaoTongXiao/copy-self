# -*- coding: utf-8 -*-
import re
import json
from ..prompts.prompts import planner_system_prompt_template
from ..tools import get_tools
from utils.logger import logger
from ..state import AgentState

class Planner:
    def __init__(self, llm):
        self.llm = llm
        self.tools = get_tools()

    def get_tool_list_str(self):
        return "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])

    def __call__(self, state: AgentState):
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