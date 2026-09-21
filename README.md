# network-rag-agent

A RAG-powered AI agent for querying and troubleshooting network configuration documents using LangChain, FAISS and FastAPI.

Ask a question in plain English, such as "My OSPF neighbor is stuck in EXSTART, what should I check?", and the service finds the most relevant passages in your configuration files and runbooks and returns them with their sources.

> The sample data in this repo is **synthetic**. The devices, addresses and runbook are made-up examples that use documentation IP ranges. No real network or employer data is included.

## How it works

1. **Ingest** (`app/ingest.py`): reads `.cfg`, `.txt` and `.md` files and splits them into chunks. Config files split into blocks such as interfaces, OSPF and BGP. Runbooks split into one chunk per `##` section.
2. **Index** (`app/index.py`): turns each chunk into a TF-IDF vector and stores the vectors in a FAISS index. Search uses cosine similarity.
3. **Retrieve**: a question is vectorised the same way and the closest chunks are returned. Questions with no matching terms return nothing instead of a random guess.
4. **Answer** (`app/agent.py`):
   - *Extractive mode (default, no API key):* returns the best passage and its source.
   - *LLM mode:* if `OPENAI_API_KEY` is set, a LangChain chain asks the model to answer using only the retrieved passages and to name its sources.
5. **Serve** (`app/main.py`): a FastAPI service with `GET /health` and `POST /query`.

## Getting started

Requires Python 3.10 or newer.

```bash
git clone https://github.com/keerthanaboorgula3-tech/network-rag-agent.git
cd network-rag-agent
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs to try the API in your browser, or use curl:

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "My OSPF neighbor is stuck in EXSTART, what should I check?", "top_k": 2}'
```

Example response (shortened):

```json
{
  "answer": "Most relevant passage (troubleshooting-runbook.md, OSPF neighbor stuck in EXSTART or EXCHANGE): ... This usually means an MTU mismatch between the two ends of the link ...",
  "mode": "extractive",
  "sources": [
    {"source": "troubleshooting-runbook.md", "title": "OSPF neighbor stuck in EXSTART or EXCHANGE", "score": 0.268}
  ]
}
```

### Optional: LLM answers

```bash
pip install langchain-openai
cp .env.example .env     # then add your OPENAI_API_KEY
export $(grep -v '^#' .env | xargs)
uvicorn app.main:app --reload
```

### Use your own documents

Put your `.cfg`, `.txt` or `.md` files in a folder and set `DATA_DIR` to that folder. Only index documents you are allowed to share with the model provider.

## Tests

```bash
pytest
```

The tests cover chunking, retrieval quality on the sample data, the no-match case, the LangChain answer chain (with a fake model, so no key is needed), and the API.

## Limitations

- Retrieval uses TF-IDF keyword matching, not neural embeddings, so it can miss questions that use different words from the documents. Swapping in an embedding model is the natural next step.
- The LLM mode is tested only with a fake model. It has not been tested against a live provider in this repo.
- The index is built in memory at startup and is not persisted.
- Sample data is small and synthetic, so results on real configurations will differ.

## License

MIT. See [LICENSE](LICENSE).
