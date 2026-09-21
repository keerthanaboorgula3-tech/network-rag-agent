"""Answer questions from retrieved passages.

Default mode is extractive: return the most relevant passages with their
sources, no API key needed. If a LangChain chat model is supplied, the
model writes an answer using only those passages.
"""
from __future__ import annotations

import os

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .index import Hit

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a network operations assistant. Answer the question using "
            "ONLY the passages provided. If they do not contain the answer, say "
            "you could not find it in the documents. Mention the source file "
            "names you used.",
        ),
        ("human", "Question: {question}\n\nPassages:\n{context}"),
    ]
)


def format_context(hits: list[Hit]) -> str:
    return "\n\n".join(f"[{h.source}] {h.title}\n{h.text}" for h in hits)


def extractive_answer(question: str, hits: list[Hit]) -> str:
    if not hits:
        return "I could not find anything relevant in the documents."
    best = hits[0]
    return f"Most relevant passage ({best.source}, {best.title}):\n\n{best.text}"


def llm_answer(question: str, hits: list[Hit], llm) -> str:
    """Generate an answer with any LangChain chat model."""
    if not hits:
        return "I could not find anything relevant in the documents."
    chain = PROMPT | llm | StrOutputParser()
    return chain.invoke({"question": question, "context": format_context(hits)})


def get_llm():
    """Return a chat model if OPENAI_API_KEY is set and langchain-openai is
    installed, otherwise None (extractive mode)."""
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        return None
    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
