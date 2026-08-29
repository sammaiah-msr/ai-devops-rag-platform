from pathlib import Path
import requests
import chromadb

OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
EMBED_MODEL = "nomic-embed-text"

KNOWLEDGE_DIR = Path("knowledge")
DB_DIR = "./vector_db"

client = chromadb.PersistentClient(path=DB_DIR)

collection = client.get_or_create_collection(
    name="devops_knowledge"
)


def embed(text: str):
    response = requests.post(
        OLLAMA_EMBED_URL,
        json={
            "model": EMBED_MODEL,
            "input": text
        },
        timeout=120
    )

    response.raise_for_status()

    return response.json()["embeddings"][0]


def chunk_text(text, chunk_size=800):
    paragraphs = text.split("\n\n")

    chunks = []
    current = ""

    for paragraph in paragraphs:

        if len(current) + len(paragraph) > chunk_size:

            if current.strip():
                chunks.append(current.strip())

            current = paragraph

        else:
            current += "\n\n" + paragraph

    if current.strip():
        chunks.append(current.strip())

    return chunks


documents = []
embeddings = []
ids = []
metadata = []

index = 0

for file in KNOWLEDGE_DIR.glob("*.md"):

    print(f"Processing: {file}")

    content = file.read_text(encoding="utf-8")

    chunks = chunk_text(content)

    for chunk in chunks:

        vector = embed(chunk)

        documents.append(chunk)
        embeddings.append(vector)

        ids.append(f"doc-{index}")

        metadata.append({
            "source": file.name
        })

        index += 1


collection.upsert(
    ids=ids,
    documents=documents,
    embeddings=embeddings,
    metadatas=metadata
)

print()
print("RAG ingestion complete")
print("Chunks stored:", len(documents))