"""FastAPI service. Run with: uvicorn app.main:app --reload"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .agent import extractive_answer, get_llm, llm_answer
from .index import ChunkIndex
from .ingest import load_chunks


class Question(BaseModel):
    question: str = Field(min_length=3)
    top_k: int = Field(default=3, ge=1, le=10)


class Source(BaseModel):
    source: str
    title: str
    score: float


class Answer(BaseModel):
    answer: str
    mode: str
    sources: list[Source]


@asynccontextmanager
async def lifespan(app: FastAPI):
    data_dir = os.getenv("DATA_DIR", "data/sample_configs")
    app.state.index = ChunkIndex(load_chunks(data_dir))
    app.state.llm = get_llm()
    yield


app = FastAPI(title="network-rag-agent", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "chunks": len(app.state.index.chunks)}


@app.post("/query", response_model=Answer)
def query(body: Question):
    hits = app.state.index.search(body.question, body.top_k)
    llm = app.state.llm
    if llm is not None:
        text, mode = llm_answer(body.question, hits, llm), "llm"
    else:
        text, mode = extractive_answer(body.question, hits), "extractive"
    return Answer(
        answer=text,
        mode=mode,
        sources=[Source(source=h.source, title=h.title, score=round(h.score, 3)) for h in hits],
    )
