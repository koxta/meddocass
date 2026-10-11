upload: curl -s -F "file=@data/samples/UMNwriteup.pdf" localhost:8000/documents
doc list: curl localhost:8000/documents
search doc: curl -s localhost:8000/search -H 'Content-Type: application/json' \
  -d '{"query": "What is the patients complaint?", "top_k": 3}'