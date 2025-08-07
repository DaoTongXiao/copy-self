# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_openai import ChatOpenAI

# Load .env file
load_dotenv()

# Get configuration from environment variables
api_key = os.getenv("API_KEY", "")
base_url = os.getenv("API_URL", "")
model = os.getenv("API_MODEL", "")

# Initialize LLM
llm = ChatOpenAI(
    model=model,
    api_key=SecretStr(api_key) if api_key else None,
    base_url=base_url if base_url else None,
    temperature=0
)