# AI DevOps RAG Platform

A local-first AI platform for Kubernetes and DevOps troubleshooting. The project combines a local LLM, retrieval-augmented generation (RAG), vector search, FastAPI, Docker, Kubernetes, and Helm to answer operational questions using curated runbooks instead of relying only on the model's pretrained knowledge.

## Overview

This project demonstrates how to:

- run a local LLM with Ollama on an NVIDIA GPU
- generate embeddings with a local embedding model
- store operational knowledge in ChromaDB
- retrieve relevant troubleshooting context through semantic search
- expose the workflow through a FastAPI service
- package and deploy the app in Kubernetes with Helm

The current knowledge base focuses on:

- CrashLoopBackOff
- ImagePullBackOff
- OOMKilled / Exit Code 137

## Architecture

```text
User
  |
  v
FastAPI API
  |-- /health
  |-- /ask
  |-- /rag
  |
  +------------------------+
  |                        |
  v                        v
Ollama API             ChromaDB
  | (LLM)               | (vector store)
  |                      |
  +--------> Llama 3.2 3B
  +--------> nomic-embed-text
              |
              v
      Retrieved runbook context
              |
              v
         Local AI response
```

## Tech Stack

| Area | Technology |
| --- | --- |
| Operating Environment | Windows 11 + WSL2 / Ubuntu 24.04 |
| Language | Python 3.12 |
| AI Framework | PyTorch |
| Model Server | Ollama |
| LLM | Llama 3.2 3B |
| Embedding Model | nomic-embed-text |
| API Framework | FastAPI |
| Vector Database | ChromaDB |
| Containerization | Docker |
| Orchestration | Kubernetes |
| Package Management | Helm |
| GPU | NVIDIA RTX 5070 Laptop GPU |

## Project Flow

```text
Local Python app
  |
  v
Ollama local LLM
  |
  v
FastAPI service
  |
  v
RAG + ChromaDB retrieval
  |
  v
Docker container
  |
  v
Kubernetes deployment
  |
  v
Helm-managed application
```

## Repository Structure

```text
local-llm-api/
├── README.md
├── main.py
├── ingest.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── vector_db/
├── knowledge/
│   ├── crashloopbackoff.md
│   ├── imagepullbackoff.md
│   └── oomkilled.md
├── k8s/
│   └── local-llm-api/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── _helpers.tpl
│           ├── configmap.yaml
│           ├── deployment.yaml
│           └── service.yaml
└── docs/
    └── AI_DevOps_RAG_Kubernetes_Helm_Interview_Guide_v1.0_2026-08-29.docx
```

## Prerequisites

- WSL2 or Ubuntu-based Linux environment
- NVIDIA GPU and NVIDIA drivers
- Docker
- Kubernetes cluster or local Kubernetes environment
- Helm
- Python 3.12+
- Ollama

## GPU Validation

Verify the GPU is visible from WSL:

```bash
nvidia-smi
```

The project was validated with an NVIDIA RTX 5070 Laptop GPU and approximately 12 GB VRAM.

### PyTorch CUDA validation

A compatible CUDA-enabled PyTorch build should be installed for GPU execution. Example validation:

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0)); print(torch.cuda.get_device_properties(0).total_memory)"
```

Important note: GPU visibility alone does not guarantee that the installed PyTorch build supports the GPU architecture. A CUDA mismatch can prevent GPU execution even when `nvidia-smi` shows the device.

## Ollama Setup

Install dependencies required for Ollama:

```bash
sudo apt update
sudo apt install -y zstd
```

Install Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Pull and run the model:

```bash
ollama pull llama3.2:3b
ollama run llama3.2:3b
```

Verify the model is running on the GPU:

```bash
ollama ps
nvidia-smi
```

## Embedding Model

The RAG pipeline uses `nomic-embed-text` to convert user questions and knowledge chunks into embeddings before similarity search in ChromaDB.

## Python Environment Setup

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Ingest Knowledge

The RAG knowledge collection is created from the markdown files in the `knowledge/` directory.

```bash
python ingest.py
```

This loads the knowledge base into ChromaDB so `/rag` can retrieve context for troubleshooting questions.

## Run the API

Start the FastAPI service:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger UI is available at:

```text
http://localhost:8000/docs
```

## API Endpoints

### GET /

Returns service status and model metadata.

### GET /health

Health check endpoint.

### POST /ask

Directly queries the local LLM without using retrieved context.

### POST /rag

Queries the embedding model, retrieves the most relevant knowledge chunks from ChromaDB, and sends that context to the LLM for a grounded answer.

## Example Requests

### Direct LLM ask

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Why is my Kubernetes pod in CrashLoopBackOff?"}'
```

### RAG-based ask

```bash
curl -X POST "http://localhost:8000/rag" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"My pod keeps restarting with CrashLoopBackOff. What should I check first?"}'
```

## Deployment Notes

The project includes a Helm chart under `k8s/local-llm-api/` for deploying the service in Kubernetes. The app is designed to run alongside local model services and persistent storage for the vector database. The deployment setup should be adjusted to match the target cluster and resource constraints.

## Troubleshooting

If the API cannot connect to Ollama, check:

```bash
curl http://localhost:11434/api/tags
```

If RAG answers are empty or missing:

```bash
python ingest.py
```

If Chroma cannot find the collection, confirm the vector database was initialized and the app is using the expected path.

## License

This project is intended for educational and demonstration purposes as an AI/DevOps engineering sample.

API Endpoints
Health
GET /health

Used by Kubernetes readiness and liveness probes.

Direct LLM Question
POST /ask

Sends a question directly to the local LLM.

RAG Question
POST /rag

Retrieves relevant knowledge before generating the response.

6. Why RAG?

During initial testing, the base LLM sometimes generated inaccurate Kubernetes troubleshooting recommendations.

RAG was introduced to ground answers in controlled DevOps runbooks.

Question
   |
   v
Embedding
   |
   v
Vector Search
   |
   v
Relevant Runbook Chunks
   |
   v
Grounded Prompt
   |
   v
Local LLM
   |
   v
Answer

This approach is useful for:

Internal operational documentation
Kubernetes runbooks
OpenShift procedures
Incident troubleshooting
Architecture standards
Application support documentation
Enterprise knowledge assistants
7. Knowledge Base

The current knowledge base contains:

knowledge/crashloopbackoff.md
knowledge/imagepullbackoff.md
knowledge/oomkilled.md

Run ingestion:

python ingest.py

The ingestion pipeline:

Reads Markdown documents.
Splits documents into chunks.
Generates embeddings using nomic-embed-text.
Stores vectors and metadata in ChromaDB.
Makes the content available to /rag.
8. RAG Troubleshooting Use Cases
CrashLoopBackOff

Example question:

Why is my Kubernetes pod in CrashLoopBackOff?

The RAG pipeline retrieves the CrashLoopBackOff runbook before generating the answer.

ImagePullBackOff

Example:

My Kubernetes application cannot pull an image from a private registry.
What should I check?

Typical areas include:

Registry authentication
Image/tag availability
imagePullSecrets
Registry connectivity
TLS/certificate problems
OOMKilled

Example:

My container terminated with exit code 137.
What should I check?

The assistant retrieves the OOMKilled runbook and provides memory-focused troubleshooting guidance.

9. Docker

Build the image:

docker build -t ai-devops-rag:v1 .

Run:

docker run --rm \
  --name ai-devops-rag \
  -p 8001:8000 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  ai-devops-rag:v1

Swagger:

http://localhost:8001/docs
Docker Networking

Inside a container:

localhost

refers to the container itself.

Therefore the container uses:

http://host.docker.internal:11434

to communicate with Ollama running on the host.

The application externalizes this setting:

OLLAMA_BASE_URL

This allows the same image to run in multiple environments.

10. Kubernetes

The application was deployed to Docker Desktop Kubernetes.

Validated Kubernetes version:

v1.36.1

Check the cluster:

kubectl get nodes
kubectl get pods -A
Kubernetes Components

The application uses:

Deployment
Pods
ClusterIP Service
ConfigMap
Readiness probe
Liveness probe
CPU requests/limits
Memory requests/limits
Multiple replicas
EndpointSlice
Rolling restart
11. ConfigMap

Runtime Ollama configuration is externalized using a ConfigMap.

Example:

data:
  OLLAMA_BASE_URL: "http://host.docker.internal:11434"

This separates application configuration from the container image.

12. Resource Management

Example:

resources:
  requests:
    cpu: "250m"
    memory: "256Mi"
  limits:
    cpu: "1"
    memory: "1Gi"

Requests help Kubernetes schedule the pod.

Limits restrict maximum resource consumption.

13. Readiness and Liveness

Readiness:

readinessProbe:
  httpGet:
    path: /health
    port: 8000

A failed readiness probe prevents the pod from receiving Service traffic.

Liveness:

livenessProbe:
  httpGet:
    path: /health
    port: 8000

A persistent liveness failure causes Kubernetes to restart the container.

14. Scaling

The application was scaled to multiple replicas:

kubectl scale deployment ai-devops-rag --replicas=2

EndpointSlice can be inspected using:

kubectl get endpointslice
15. Rolling Restart
kubectl rollout restart deployment/ai-devops-rag

Kubernetes gradually replaces the pods while maintaining the desired application availability.

16. Helm

Helm was introduced after validating the raw Kubernetes deployment.

Helm version used:

v3.21.4

Chart structure:

k8s/local-llm-api/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── _helpers.tpl
    ├── configmap.yaml
    ├── deployment.yaml
    └── service.yaml
17. Helm Validation

Lint:

helm lint ./local-llm-api

Render manifests locally:

helm template ai-devops-rag ./local-llm-api
18. Helm Install
helm install ai-devops-rag ./local-llm-api

Check:

helm list
19. Helm Upgrade

The application was initially deployed with:

replicaCount: 2

It was then changed to:

replicaCount: 3

Validate:

helm lint ./local-llm-api
helm template ai-devops-rag ./local-llm-api | grep replicas

Upgrade:

helm upgrade ai-devops-rag ./local-llm-api
20. Helm Revision History
helm history ai-devops-rag

Validated history:

REVISION   STATUS       DESCRIPTION
1          superseded   Install complete
2          deployed     Upgrade complete
21. Helm Rollback

Example:

helm rollback ai-devops-rag 1

A rollback does not simply reactivate revision 1.

Helm applies the old configuration and creates a new release revision.

Conceptually:

Revision 1
   |
   v
Helm Upgrade
   |
   v
Revision 2
   |
   v
Helm Rollback
   |
   v
Revision 3
22. Key Troubleshooting Lessons
Problem	Resolution
PyTorch GPU kernel incompatibility	Install CUDA/PyTorch build supporting the GPU architecture
Ollama installation missing zstd	Install zstd
uvicorn not found	Activate the correct Python virtual environment
Docker unavailable from WSL	Verify Docker Desktop WSL integration
Container cannot reach Ollama	Use host.docker.internal
Kubernetes Endpoints deprecation	Use EndpointSlice
Duplicate pods after Helm install	Remove old raw-YAML deployment after validating Helm
Helm repository TLS issue	Use trusted official installation method instead of disabling certificate verification
23. Security

The repository intentionally excludes:

.venv/
vector_db/
.env
*.key
*.pem
*.p12
*.jks

Never commit:

Passwords
API tokens
Cloud credentials
Registry credentials
Private keys
Certificates containing private keys
kubeconfig credentials
Corporate secrets

Use Kubernetes Secrets or an enterprise secrets-management platform for sensitive configuration.

24. Production Improvements

The current project is designed as a local hands-on platform engineering lab.

A production architecture should add:

Shared/persistent vector database
Persistent storage
Enterprise model serving
Authentication and authorization
TLS
Secrets management
Network policies
Prometheus metrics
Grafana dashboards
Centralized logging
Distributed tracing
HPA/KEDA
Private container registry
Image vulnerability scanning
Image signing
CI/CD or GitOps
Automated document ingestion
RAG evaluation
Model monitoring
25. Interview Summary

A concise way to explain this project:

I built an AI-powered DevOps troubleshooting platform using a local GPU and LLM. I configured PyTorch and Ollama, exposed the model through FastAPI, and added RAG using nomic embeddings and ChromaDB because relying only on the base model could produce inaccurate Kubernetes troubleshooting guidance.

I created operational knowledge for CrashLoopBackOff, ImagePullBackOff, and OOMKilled scenarios, containerized the application with Docker, and externalized model connectivity through environment configuration.

I then deployed the application to Kubernetes with a ClusterIP Service, ConfigMap, readiness and liveness probes, CPU and memory requests and limits, multiple replicas, EndpointSlice validation, and rolling restarts.

Finally, I converted the raw Kubernetes manifests into a reusable Helm chart, validated it with helm lint and helm template, installed the release, upgraded it from two to three replicas, and validated Helm revision history.

26. Skills Demonstrated

This project demonstrates hands-on experience with:

AI Infrastructure
AI Platform Engineering
Python
PyTorch
CUDA/GPU workloads
Local LLM deployment
Ollama
FastAPI
REST APIs
Retrieval-Augmented Generation
Embeddings
Vector databases
ChromaDB
Docker
Kubernetes
Helm
Configuration management
Health probes
Resource management
Scaling
Rolling deployments
Troubleshooting
Platform engineering
27. Roadmap

Next phases:

Current Platform
      |
      v
Helm Packaging
      |
      v
OpenShift Deployment
      |
      v
OpenShift Route
      |
      v
CI/CD Pipeline
      |
      v
Image Scanning
      |
      v
Prometheus / Grafana
      |
      v
Persistent Vector Database
      |
      v
Automated Knowledge Ingestion
      |
      v
Agentic Incident Assistant
Documentation

Detailed step-by-step implementation and interview notes are available under:

docs/

Document version:

v1.0
August 29, 2026

Project Version: v1.0
Last Updated: August 29, 2026
EOF