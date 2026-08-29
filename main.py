import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import chromadb

app = FastAPI(
    title="Local AI DevOps Assistant",
    description="FastAPI service using Ollama, local LLM, and RAG",
    version="2.0"
)

# -----------------------------
# Ollama configuration
# -----------------------------

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_EMBED_URL = f"{OLLAMA_BASE_URL}/api/embed"

LLM_MODEL = "llama3.2:3b"
EMBED_MODEL = "nomic-embed-text"

# -----------------------------
# Chroma configuration
# -----------------------------

CHROMA_DB_PATH = "./vector_db"
COLLECTION_NAME = "devops_knowledge"

chroma_client = chromadb.PersistentClient(
    path=CHROMA_DB_PATH
)

try:
    knowledge_collection = chroma_client.get_collection(
        name=COLLECTION_NAME
    )
except Exception as exc:
    knowledge_collection = None
    print(
        f"Warning: Chroma collection '{COLLECTION_NAME}' "
        f"is not available yet: {exc}"
    )


# -----------------------------
# Request model
# -----------------------------

class PromptRequest(BaseModel):
    prompt: str


# -----------------------------
# Helper functions
# -----------------------------

def create_embedding(text: str):
    """
    Convert text into an embedding vector using Ollama.
    """

    try:
        response = requests.post(
            OLLAMA_EMBED_URL,
            json={
                "model": EMBED_MODEL,
                "input": text
            },
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        return data["embeddings"][0]

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to create embedding: {exc}"
        )


def generate_llm_response(prompt: str):
    """
    Send a prompt to the local Ollama LLM.
    """

    try:
        response = requests.post(
            OLLAMA_GENERATE_URL,
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )

        response.raise_for_status()

        result = response.json()

        return result["response"]

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Unable to communicate with Ollama: {exc}"
        )


# -----------------------------
# API endpoints
# -----------------------------

@app.get("/")
def root():
    return {
        "status": "running",
        "service": "Local AI DevOps Assistant",
        "llm_model": LLM_MODEL,
        "embedding_model": EMBED_MODEL,
        "rag_enabled": knowledge_collection is not None
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/ask")
def ask_llm(request: PromptRequest):
    """
    Direct LLM call without RAG.
    """

    prompt = f"""
You are an experienced Kubernetes, OpenShift, DevOps,
and AI Infrastructure engineer.

Answer the following question clearly and technically.

User Question:

{request.prompt}
"""

    answer = generate_llm_response(prompt)

    return {
        "mode": "direct-llm",
        "model": LLM_MODEL,
        "question": request.prompt,
        "answer": answer
    }


@app.post("/rag")
def rag_question(request: PromptRequest):
    """
    RAG endpoint:
    Question -> embedding -> Chroma -> retrieved context
    -> Ollama -> grounded answer.
    """

    if knowledge_collection is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "RAG knowledge collection is not available. "
                "Run ingest.py first."
            )
        )

    try:
        # Create embedding for the user's question
        question_embedding = create_embedding(
            request.prompt
        )

        # Retrieve relevant chunks
        results = knowledge_collection.query(
            query_embeddings=[question_embedding],
            n_results=4
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            raise HTTPException(
                status_code=404,
                detail="No relevant knowledge was found."
            )

        context = "\n\n---\n\n".join(documents)

        rag_prompt = f"""
You are an AI DevOps troubleshooting assistant specializing in:

- Kubernetes
- OpenShift
- Docker
- Jenkins
- Ansible
- Terraform
- AWS
- AI Infrastructure

Use the retrieved technical context below as your primary source.

Do not invent Kubernetes settings, commands, or behavior.

If the context is insufficient to confidently answer,
state that additional information is required.

Retrieved Context:

{context}

User Question:

{request.prompt}

Respond using this structure:

1. Problem Summary
2. Likely Causes
3. Troubleshooting Steps
4. Commands to Run
5. Recommended Remediation
"""

        answer = generate_llm_response(
            rag_prompt
        )

        sources = sorted(
            {
                item.get("source", "unknown")
                for item in metadatas
                if item
            }
        )

        return {
            "mode": "rag",
            "model": LLM_MODEL,
            "embedding_model": EMBED_MODEL,
            "question": request.prompt,
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": len(documents)
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"RAG processing failed: {exc}"
        )