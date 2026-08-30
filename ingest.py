import os
import requests
import chromadb
from pathlib import Path
from openai import OpenAI

# -----------------------------
# AI provider configuration
# -----------------------------

AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()

# Ollama
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434"
)

OLLAMA_EMBED_URL = f"{OLLAMA_BASE_URL}/api/embed"

OLLAMA_EMBED_MODEL = "nomic-embed-text"

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OPENAI_EMBED_MODEL = os.getenv(
    "OPENAI_EMBED_MODEL",
    "text-embedding-3-small"
)

openai_client = None

if AI_PROVIDER == "openai":
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is required when AI_PROVIDER=openai"
        )

    openai_client = OpenAI(
        api_key=OPENAI_API_KEY
    )

ACTIVE_EMBED_MODEL = (
    OPENAI_EMBED_MODEL
    if AI_PROVIDER == "openai"
    else OLLAMA_EMBED_MODEL
)

KNOWLEDGE_DIR = Path("knowledge")
DB_DIR = "./vector_db"

COLLECTION_NAME = (
    "devops_knowledge_openai"
    if AI_PROVIDER == "openai"
    else "devops_knowledge"
)

client = chromadb.PersistentClient(path=DB_DIR)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)


def embed(text: str):
    """
    Create embeddings using OpenAI when AI_PROVIDER=openai.
    Otherwise use local Ollama.
    """

    if AI_PROVIDER == "openai":
        response = openai_client.embeddings.create(
            model=OPENAI_EMBED_MODEL,
            input=text
        )

        return response.data[0].embedding

    # Default: Ollama
    response = requests.post(
        OLLAMA_EMBED_URL,
        json={
            "model": OLLAMA_EMBED_MODEL,
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