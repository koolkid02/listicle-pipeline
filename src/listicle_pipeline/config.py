import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

MODEL_NAME = os.environ.get("LISTICLE_MODEL", "gpt-4o-mini")

TEMPERATURE_LEXICAL = 0.7
TEMPERATURE_SEMANTIC = 0.0
TEMPERATURE_INTENT = 0.7
TEMPERATURE_GUARDRAIL = 0.0
TEMPERATURE_SUMMARISER = 0.5

MAX_GUARDRAIL_ATTEMPTS = 3
CONFIDENCE_THRESHOLD = 0.7
RECURSION_LIMIT = 60

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"


def get_llm(temperature: float) -> ChatOpenAI:
    return ChatOpenAI(model=MODEL_NAME, temperature=temperature)


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.txt").read_text()
