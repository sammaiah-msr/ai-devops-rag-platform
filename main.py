import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import chromadb
from openai import OpenAI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time

app = FastAPI(
    title="Local AI DevOps Assistant",
    description="FastAPI service using Ollama, local LLM, and RAG",
    version="2.0"
)

REQUEST_COUNT = Counter(
    "ai_platform_requests_total",
    "Total number of API requests",
    ["endpoint", "method", "status"]
)

REQUEST_LATENCY = Histogram(
    "ai_platform_request_latency_seconds",
    "Request latency in seconds",
    ["endpoint"]
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
# AI provider configuration
# -----------------------------

AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_LLM_MODEL = os.getenv(
    "OPENAI_LLM_MODEL",
    "gpt-5.6-luna"
)
OPENAI_EMBED_MODEL = os.getenv(
    "OPENAI_EMBED_MODEL",
    "text-embedding-3-small"
)

ACTIVE_LLM_MODEL = (
    OPENAI_LLM_MODEL
    if AI_PROVIDER == "openai"
    else LLM_MODEL
)

ACTIVE_EMBED_MODEL = (
    OPENAI_EMBED_MODEL
    if AI_PROVIDER == "openai"
    else EMBED_MODEL
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

# -----------------------------
# Chroma configuration
# -----------------------------

CHROMA_DB_PATH = "./vector_db"
COLLECTION_NAME = (
    "devops_knowledge_openai"
    if AI_PROVIDER == "openai"
    else "devops_knowledge"
)

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
    Create an embedding using Ollama locally
    or OpenAI when AI_PROVIDER=openai.
    """

    if AI_PROVIDER == "openai":
        try:
            response = openai_client.embeddings.create(
                model=ACTIVE_EMBED_MODEL,
                input=text
            )

            return response.data[0].embedding

        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Unable to create OpenAI embedding: {exc}"
            )

    # Default: Ollama
    try:
        response = requests.post(
            OLLAMA_EMBED_URL,
            json={
                "model": ACTIVE_EMBED_MODEL,
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
            detail=f"Unable to create Ollama embedding: {exc}"
        )

def generate_llm_response(prompt: str):
    """
    Generate a response using OpenAI when AI_PROVIDER=openai,
    otherwise use local Ollama.
    """

    if AI_PROVIDER == "openai":
        try:
            response = openai_client.responses.create(
                model=ACTIVE_LLM_MODEL,
                input=prompt
            )

            return response.output_text

        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Unable to communicate with OpenAI: {exc}"
            )

    # Default: Ollama
    try:
        response = requests.post(
            OLLAMA_GENERATE_URL,
            json={
                "model": ACTIVE_LLM_MODEL,
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
        "provider": AI_PROVIDER,
        "llm_model": ACTIVE_LLM_MODEL,
        "embedding_model": ACTIVE_EMBED_MODEL,
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
    start_time = time.time()
    try:
        prompt = f"""
You are an experienced Kubernetes, OpenShift, DevOps,
and AI Infrastructure engineer.

Answer the following question clearly and technically.

User Question:

{request.prompt}
"""

        answer = generate_llm_response(prompt)

        REQUEST_COUNT.labels(
            endpoint="/ask",
            method="POST",
            status="200"
        ).inc()

        return {
            "mode": "direct-llm",
            "provider": AI_PROVIDER,
            "model": ACTIVE_LLM_MODEL,
            "question": request.prompt,
            "answer": answer
        }
    except HTTPException as exc:
        # Preserve actual HTTP status such as 503
        REQUEST_COUNT.labels(
            endpoint="/ask",
            method="POST",
            status=str(exc.status_code)
        ).inc()
        raise

    except Exception:
        REQUEST_COUNT.labels(
            endpoint="/ask",
            method="POST",
            status="500"
        ).inc()
        raise

    finally:
        REQUEST_LATENCY.labels(
            endpoint="/ask"
        ).observe(
            time.time() - start_time
        )

@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.post("/rag")
def rag_question(request: PromptRequest):
    """
    RAG endpoint:
    Question -> embedding -> Chroma -> retrieved context
    -> Ollama -> grounded answer.
    """
    start_time = time.time()

    try:
        if knowledge_collection is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "RAG knowledge collection is not available. "
                    "Run ingest.py first."
                )
            )

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

        REQUEST_COUNT.labels(
            endpoint="/rag",
            method="POST",
            status="200"
        ).inc()

        return {
            "mode": "rag",
            "provider": AI_PROVIDER,
            "model": ACTIVE_LLM_MODEL,
            "embedding_model": ACTIVE_EMBED_MODEL,
            "question": request.prompt,
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": len(documents)
        }

    except HTTPException as exc:
        REQUEST_COUNT.labels(
            endpoint="/rag",
            method="POST",
            status=str(exc.status_code)
        ).inc()
        raise

    except Exception as exc:
        REQUEST_COUNT.labels(
            endpoint="/rag",
            method="POST",
            status="500"
        ).inc()
        raise 
    finally:
        REQUEST_LATENCY.labels(
            endpoint="/rag"
        ).observe(
            time.time() - start_time
        )