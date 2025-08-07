# -*- coding: utf-8 -*-
import re
import json
from ..tools import get_tool_map
from utils.logger import logger
from ..state import AgentState


class Executor:
    def __init__(self):
        self.tool_map = get_tool_map()

    def __call__(self, state: AgentState):
        """Executes the tools in the plan."""
        logger.info("\n=== Executing Plan ===")
        plan = state.get("plan", [])
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
                    try:
                        tool_input = json.loads(f"{{{args_str}}}")
                    except json.JSONDecodeError:
                        param_matches = re.findall(r'(\w+)=["\'](.*?)["\']', args_str)
                        if param_matches:
                            tool_input = dict(param_matches)
                        else:
                            first_arg_name = list(tool_to_call.args.keys())[0]
                            tool_input = {first_arg_name: args_str.strip("\"'")}

                result = tool_to_call.invoke(tool_input)
                observation = str(result)
                logger.info(f"Observation: {observation}")
            except Exception as e:
                observation = f"Error executing tool '{tool_name}': {e}"
                logger.error(observation)

            observations.append(observation)
            logger.info("--------------------")

        return {"observations": observations}
