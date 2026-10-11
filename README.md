# MedDocAss

## Run

You need Docker and an Anthropic API key.

```sh
cp .env.example .env        # then set ANTHROPIC_API_KEY
docker compose up --build
```

The API runs on http://localhost:8000
On first start it downloads the embedding model, which takes a minute.


## curl

```sh
# upload a document
curl -s -F "file=@data/samples/UMNwriteup.pdf" localhost:8000/documents

# list documents
curl -s localhost:8000/documents

# search chunks
curl -s localhost:8000/search -H 'Content-Type: application/json' \
  -d '{"query": "What does the patient complain about?", "top_k": 3}'

# ask a question
curl -s localhost:8000/ask -H 'Content-Type: application/json' \
  -d '{"question": "What does the patient complain about?"}'
```

## Architecture

```
upload:  POST /documents -> Indexer -> Datastore -> Qdrant
ask:     POST /ask -> Retriever -> Qdrant -> Generator -> LLM -> answer + references
```

- **Indexer** extracts text per page with pypdf and spiits it into
  overlapping chunks.
- **Datastore** : embeds chunks with fastembed and
  stores them in Qdrant. Uploading the same file again replaces it.
- **Retriever** : embeds the question and returns the top-k most similar chunks.
- **Generator** : sends the chunks as numbered sources to Claude and returns the
  answer with references to the sources it cited. If nothing relevant is found, it doesn't call
  the LLM.

Everything else in `src/meddocass/`:

- `main.py`: FastAPI app and request logging
- `api/`: routes and request/response models
- `config.py`: settings, read from environment variables or `.env`
- `dependencies.py`: creates the components above once and shares them
- `observability.py`: logging with a request id on every line
