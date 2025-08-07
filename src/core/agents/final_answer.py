# -*- coding: utf-8 -*-
from ..prompts.prompts import final_answer_prompt_template
from utils.logger import logger
from ..state import AgentState

class FinalAnswerGenerator:
    def __init__(self, llm):
        self.llm = llm

    def __call__(self, state: AgentState):
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