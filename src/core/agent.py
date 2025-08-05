import re
import operator
import time
import ast
from typing import TypedDict, List, Annotated, Sequence, cast
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from core.prompt import react_system_prompt_template
from utils.logger import logger
from core.tools import TOOLS

# Define the state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    recursion_limit: int

# Tools moved to core.tools (see TOOLS)

# Create the ReAct Agent
class ReActAgent:
    def __init__(self, llm, tools, system_message_template):
        self.llm = llm
        self.tools = tools
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.system_message_template = system_message_template

    def _get_system_message(self):
        tool_list = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])
        return self.system_message_template.format(tool_list=tool_list)

    def _parse_action(self, text: str):
        """Parse the action from the model output."""
        thought_match = re.search(r"<thought>(.*?)</thought>", text, re.DOTALL)
        action_match = re.search(r"<action>(.*?)</action>", text, re.DOTALL)
        final_answer_match = re.search(r"<final_answer>(.*?)</final_answer>", text, re.DOTALL)
        clarification_match = re.search(r"<clarification>(.*?)</clarification>", text, re.DOTALL)

        thought = thought_match.group(1).strip() if thought_match else ""

        if clarification_match:
            return {
                "thought": thought,
                "clarification": clarification_match.group(1).strip(),
                "type": "clarification"
            }

        if action_match:
            action_str = action_match.group(1).strip()
            # Parse tool call: tool_name(param1="value1", param2="value2")
            match = re.match(r"(\w+)\((.*)\)", action_str)
            if not match:
                return {
                    "thought": thought,
                    "error": f"Could not parse action format: {action_str}. Correct format is: tool_name(param1=\"value1\")",
                    "type": "error"
                }

            tool_name, args_str = match.groups()

            if tool_name not in self.tool_map:
                return {
                    "thought": thought,
                    "error": f"Tool '{tool_name}' does not exist. Available tools: {list(self.tool_map.keys())}",
                    "type": "error"
                }

            try:
                # Parse arguments (support numbers, booleans, null, lists, dicts, strings)
                if args_str.strip():
                    # First, try to interpret as Python literals safely
                    # Normalize common JSON literals to Python equivalents
                    normalized = re.sub(r'\btrue\b', 'True', args_str, flags=re.IGNORECASE)
                    normalized = re.sub(r'\bfalse\b', 'False', normalized, flags=re.IGNORECASE)
                    normalized = re.sub(r'\bnull\b', 'None', normalized, flags=re.IGNORECASE)
                    try:
                        # Wrap into dict(...) form so "a=1, b=[...]" becomes a dict
                        tool_input_candidate = ast.literal_eval(f"dict({normalized})")
                        if not isinstance(tool_input_candidate, dict):
                            raise ValueError("Parsed args are not a dict")
                        tool_input = tool_input_candidate
                    except Exception:
                        # Fallback to legacy regex: only captures string arguments
                        param_matches = re.findall(r'(\w+)=(["\\\'])(.*?)\2', args_str)
                        if param_matches:
                            tool_input = {param: value for param, _, value in param_matches}
                        else:
                            # No parseable arguments found; treat as empty
                            tool_input = {}
                else:
                    tool_input = {}

                return {
                    "thought": thought,
                    "tool": tool_name,
                    "tool_input": tool_input,
                    "type": "action"
                }
            except Exception as e:
                return {
                    "thought": thought,
                    "error": f"Argument parsing error: {e}. Argument string: {args_str}",
                    "type": "error"
                }

        if final_answer_match:
            return {
                "thought": thought,
                "final_answer": final_answer_match.group(1).strip(),
                "type": "final_answer"
            }

        return {
            "thought": thought,
            "error": "No valid <action> or <final_answer> tag found",
            "type": "error"
        }

    def should_continue(self, state: AgentState):
        """Determine whether to continue execution."""
        if not state['messages']:
            return "continue"

        last_message = state['messages'][-1]

        # If it's an AIMessage, check if it contains a final_answer or clarification
        if isinstance(last_message, AIMessage):
            content = last_message.content
            if "<final_answer>" in content or "<clarification>" in content:
                return "end"
            elif "<action>" in content:
                return "continue"

        return "continue"

    def call_model(self, state: AgentState):
        """Call the model to generate a response."""
        # Ensure messages is a list for safe mutation locally
        messages = list(state['messages'])

        # If the first message is not a system message, add a system message
        if not messages or not isinstance(messages[0], SystemMessage):
            system_message = SystemMessage(content=self._get_system_message())
            messages.insert(0, system_message)

        try:
            response = self.llm.invoke(messages)
            logger.info(f"\n=== Model Output ===")
            logger.info(response.content)
            logger.info("====================")

            return {"messages": [response]}
        except Exception as e:
            error_msg = f"Error calling model: {e}"
            logger.error(f"Error: {error_msg}")
            return {"messages": [AIMessage(content=f"<final_answer>Sorry, an error occurred while processing the request: {error_msg}</final_answer>")]}

    def call_tool(self, state: AgentState):
        """Call a tool."""
        if not state['messages']:
            return {"messages": []}

        last_message = state['messages'][-1]

        if not isinstance(last_message, AIMessage):
            return {"messages": []}

        action = self._parse_action(cast(str, last_message.content))

        logger.info(f"\n=== Parsing Result ===")
        logger.info(f"Type: {action.get('type', 'unknown')}")
        logger.info(f"Thought: {action.get('thought', 'N/A')}")
        logger.info("====================")

        if action.get("type") == "error":
            error_message = HumanMessage(
                content=f"Parsing error: {action['error']}. Please check your format and try again."
            )
            return {"messages": [error_message]}

        if action.get("type") in ["final_answer", "clarification"]:
            return {"messages": []}

        if action.get("type") != "action":
            return {"messages": []}

        tool_name = action["tool"]
        tool_input = action["tool_input"]

        tool = self.tool_map.get(tool_name)
        if not tool:
            observation = f"Error: Tool '{tool_name}' not found"
        else:
            try:
                logger.info(f"\n=== Executing Tool ===")
                logger.info(f"Tool: {tool_name}")
                logger.info(f"Arguments: {tool_input}")

                observation = tool.invoke(tool_input)
                logger.info(f"Result: {observation}")
                logger.info("====================")
            except Exception as e:
                observation = f"Error executing tool '{tool_name}': {e}"
                logger.error(f"Tool execution error: {observation}")

        # Create a message containing the observation
        observation_message = HumanMessage(
            content=f"<observation>{observation}</observation>"
        )

        return {"messages": [observation_message]}

def create_graph(llm):
    """Create the workflow graph."""
    tools = TOOLS
    agent = ReActAgent(llm, tools, react_system_prompt_template)

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent.call_model)
    workflow.add_node("action", agent.call_tool)

    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent",
        agent.should_continue,
        {
            "continue": "action",
            "end": END,
        },
    )
    workflow.add_edge("action", "agent")

    return workflow.compile()

def run_react_agent(llm, query: str = "Where is the hometown of this year's Australian Open men's champion?"):
    """Run the ReAct Agent."""
    app = create_graph(llm)

    initial_state: AgentState = {
        "messages": [HumanMessage(content=f"<question>{query}</question>")],
        "recursion_limit": 10,
    }

    logger.info(f"=== Starting ReAct Agent ===")
    logger.info(f"Query: {query}")
    logger.info("=" * 50)

    step_count = 0
    agent_turns = 0  # Count the number of agent node executions

    try:
        for output in app.stream(initial_state, {"recursion_limit": 10}):
            step_count += 1
            node = list(output.keys())[0]
            state = list(output.values())[0]

            if node == 'agent':
                agent_turns += 1

            logger.info(f"\n--- Step {step_count}: Node '{node}' ---")

            if not state.get('messages'):
                logger.info("(No message output)")
                continue

            last_message = state['messages'][-1]

            if isinstance(last_message, ToolMessage):
                logger.info(f"Tool Message: {last_message.content}")
            elif isinstance(last_message, HumanMessage):
                content = cast(str, last_message.content)
                if content.startswith("<observation>"):
                    logger.info(f"Observation: {content}")
                else:
                    logger.info(f"Human Message: {content}")
            elif isinstance(last_message, AIMessage):
                # Only display key information to simplify output
                content = cast(str, last_message.content)
                if "<final_answer>" in content:
                    final_answer_match = re.search(r"<final_answer>(.*?)</final_answer>", content, re.DOTALL)
                    if final_answer_match:
                        logger.info(f"🎯 Final Answer: {final_answer_match.group(1).strip()}")
                elif "<action>" in content:
                    action_match = re.search(r"<action>(.*?)</action>", content, re.DOTALL)
                    if action_match:
                        logger.info(f"🔧 Executing Action: {action_match.group(1).strip()}")
                else:
                    logger.info(f"AI Message: {content}")
            else:
                logger.info(f"Other message type: {type(last_message)} - {last_message.content}")

    except Exception as e:
        logger.error(f"\nAn error occurred during execution: {e}")
        import traceback
        traceback.print_exc()

    logger.info(f"\n=== ReAct Agent Finished ===")
    logger.info(f"Total steps: {step_count} | Agent turns: {agent_turns}")

    # Evaluate efficiency
    if agent_turns <= 2:
        logger.info("✅ Execution efficiency: Excellent (completed within 2 turns)")
    elif agent_turns <= 3:
        logger.info("⚠️ Execution efficiency: Good (completed within 3 turns)")
    else:
        logger.info("❌ Execution efficiency: Needs optimization (more than 3 turns)")
