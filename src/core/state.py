# -*- coding: utf-8 -*-
import operator
from typing import TypedDict, List, Annotated

class AgentState(TypedDict):
    question: str
    plan: List[str]
    observations: Annotated[list, operator.add]
    final_answer: str
    recursion_limit: int