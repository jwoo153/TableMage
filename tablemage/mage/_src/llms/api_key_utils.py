from dotenv import load_dotenv
import pathlib
import os
from typing import Literal


def key_exists(llm_type: Literal["openai", "groq", "togetherai"]) -> bool:
    """Reads the .env file and returns whether the API key for the specified LLM type exists.

    Parameters
    ----------
    llm_type : Literal["openai"]
        The type of LLM for which to find the API key.
    """
    load_dotenv(
        dotenv_path=pathlib.Path(__file__).parent.parent.parent.parent.parent / ".env"
    )

    if llm_type == "openai":
        api_key = (
            str(os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
        )
        if api_key == "..." or api_key is None:
            return False
    elif llm_type == "groq":
        api_key = str(os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None
        if api_key == "..." or api_key is None:
            return False
    elif llm_type == "togetherai":
        api_key = (
            str(os.getenv("TOGETHERAI_API_KEY"))
            if os.getenv("TOGETHERAI_API_KEY")
            else None
        )
        if api_key == "..." or api_key is None:
            return False
    else:
        raise ValueError("Invalid LLM type specified.")
    return True


def find_key(llm_type: Literal["openai", "groq", "togetherai"]) -> str:
    """Reads the .env file and returns the API key for the specified LLM type.
    If the API key is not found, raises a ValueError.

    Parameters
    ----------
    llm_type : Literal["openai", "groq", "togetherai"]
        The type of LLM for which to find the API key.
    """
    load_dotenv(
        dotenv_path=pathlib.Path(__file__).parent.parent.parent.parent.parent / ".env"
    )

    if llm_type == "openai":
        api_key = (
            str(os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
        )
        if api_key == "..." or api_key is None:
            raise ValueError("OpenAI API key not found in .env file.")
    elif llm_type == "groq":
        api_key = str(os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None
        if api_key == "..." or api_key is None:
            raise ValueError("GROQ API key not found in .env file.")
    elif llm_type == "togetherai":
        api_key = (
            str(os.getenv("TOGETHERAI_API_KEY"))
            if os.getenv("TOGETHERAI_API_KEY")
            else None
        )
        if api_key == "..." or api_key is None:
            raise ValueError("TogetherAI API key not found in .env file.")
    else:
        raise ValueError("Invalid LLM type specified.")

    return api_key
