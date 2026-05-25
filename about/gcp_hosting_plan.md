# GCP Hosting Plan — AI Career Companion
### Complete Deployment Guide for Production

---

## 1. Architecture Decision: Monolith vs Microservices

> [!IMPORTANT]
> Your backend is **one FastAPI app** where all 4 modules share the same process, memory, and Python imports. Splitting into 4 separate Docker containers right now would require rewriting how modules call each other (currently direct Python function calls). Here's the honest recommendation:

| Approach | What It Means | Right For You? |
|----------|--------------|----------------|
| **Monolith in 1 Container** | 1 Docker image, all 4 modules together | ✅ **Start here** — zero code rewrite |
| **Microservices (4 containers)** | Each module is a separate service with REST API between them | ⚠️ Needs a full inter-service API rewrite |
| **Hybrid (2 containers)** | Backend (all modules) + Frontend | ✅ Best balance for your project now |

### Recommended Architecture: **Hybrid (2 Services)**

```
┌─────────────────────────────────────────────────────────────────┐
│                        GCP CLOUD                                │
│                                                                 │
│  ┌──────────────┐      ┌──────────────────────────────────┐     │
│  │   Cloud Run  │      │          Cloud Run               │     │
│  │  (Frontend)  │─────▶│         (Backend API)            │    │
│  │  React+Nginx │      │  FastAPI + Module1,2,3,4         │    │
│  │  Port 80     │      │  Port 8000                       │    │
│  └──────────────┘      └──────────────┬─────────────────┘     │
│                                        │                        │
│                         ┌──────────────▼──────────────────┐    │
│                         │       Cloud Storage (GCS)        │    │
│                         │  bucket: ai-career-artifacts     │    │
│                         │  ├── artifacts/                  │    │
│                         │  ├── exports/                    │    │
│                         │  └── logs/                       │    │
│                         └─────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────┐   ┌─────────────┐   ┌──────────────────────┐ │
│  │   Secret    │   │  Artifact   │   │   Cloud Build        │ │
│  │   Manager   │   │  Registry   │   │   (CI/CD)            │ │
│  │ GROQ_API_KEY│   │ Docker imgs │   │   Auto deploy        │ │
│  └─────────────┘   └─────────────┘   └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. GCP Services You Will Use

| GCP Service | Purpose | Cost |
|-------------|---------|------|
| **Cloud Run** | Run your Docker containers (serverless, auto-scales) | Free tier: 2M requests/month |
| **Cloud Storage (GCS)** | Store artifacts (.pkl), exports (.csv), logs | $0.02/GB/month |
| **Artifact Registry** | Store your Docker images | 0.5 GB free |
| **Secret Manager** | Store GROQ_API_KEY securely | First 6 secrets free |
| **GitHub Actions** | CI/CD — auto-build + deploy on git push | **100% Free** (public repos) |
| **Load Balancer** (optional) | Custom domain + SSL | ~$18/month |

> [!TIP]
> **Estimated monthly cost**: $0–$10/month for a student project with moderate traffic using the free tiers.

---

## 3. Full File Structure to Create

```
ai-career-companion/
├── Backend/
│   ├── Dockerfile                    ← NEW
│   └── ...existing files...
├── frontend/
│   ├── Dockerfile                    ← NEW
│   ├── nginx.conf                    ← NEW
│   └── ...existing files...
├── utils/
│   └── gcs_storage.py                ← NEW (replaces local file storage)
├── docker-compose.yml                ← NEW (local dev)
├── cloudbuild.yaml                   ← NEW (GCP CI/CD)
├── .dockerignore                     ← NEW
└── .env.example                      ← NEW
```

---

## 4. Step-by-Step Implementation

---

### STEP 1 — Fix Artifact & Export Storage (Critical First)

**The Problem**: Your code saves files to local disk:
```python
# artifact_manager.py
DEFAULT_ARTIFACTS_DIR = "artifacts"       # local disk → dies on Cloud Run

# main.py
EXPORTS_DIR = Path("exports")             # local disk → dies on Cloud Run
app.mount("/downloads", StaticFiles(...)) # can't serve from GCS directly
```

**The Fix**: Create `Backend/utils/gcs_storage.py`

```python
"""
utils/gcs_storage.py
====================
Unified storage layer.
- STORAGE_BACKEND=local  → local disk (dev, default)
- STORAGE_BACKEND=gcs    → Google Cloud Storage (production)
"""
import os
import io
import json
import joblib
from typing import Any
from dotenv import load_dotenv

load_dotenv()

STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
GCS_BUCKET = os.getenv("GCS_BUCKET_NAME", "ai-career-artifacts")


def _get_gcs_client():
    """Lazy-import GCS client to avoid errors in local mode."""
    from google.cloud import storage
    return storage.Client()


def save_pickle(obj: Any, path: str) -> str:
    """Save a Python object (.pkl) to local disk or GCS."""
    if STORAGE_BACKEND == "gcs":
        buffer = io.BytesIO()
        joblib.dump(obj, buffer)
        buffer.seek(0)
        bucket = _get_gcs_client().bucket(GCS_BUCKET)
        bucket.blob(path).upload_from_file(buffer, content_type="application/octet-stream")
    else:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        joblib.dump(obj, path)
    return path


def load_pickle(path: str) -> Any:
    """Load a .pkl file from local disk or GCS."""
    if STORAGE_BACKEND == "gcs":
        buffer = io.BytesIO()
        bucket = _get_gcs_client().bucket(GCS_BUCKET)
        bucket.blob(path).download_to_file(buffer)
        buffer.seek(0)
        return joblib.load(buffer)
    return joblib.load(path)


def save_json(data: dict, path: str) -> str:
    """Save a dict as JSON to local disk or GCS."""
    content = json.dumps(data, indent=2, default=str).encode("utf-8")
    if STORAGE_BACKEND == "gcs":
        bucket = _get_gcs_client().bucket(GCS_BUCKET)
        bucket.blob(path).upload_from_string(content, content_type="application/json")
    else:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.decode())
    return path


def load_json(path: str) -> dict:
    """Load a JSON file from local disk or GCS."""
    if STORAGE_BACKEND == "gcs":
        bucket = _get_gcs_client().bucket(GCS_BUCKET)
        return json.loads(bucket.blob(path).download_as_text())
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_csv(df, path: str) -> str:
    """Save a pandas DataFrame as CSV to local disk or GCS."""
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    if STORAGE_BACKEND == "gcs":
        bucket = _get_gcs_client().bucket(GCS_BUCKET)
        bucket.blob(path).upload_from_string(csv_bytes, content_type="text/csv")
    else:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(csv_bytes)
    return path


def generate_signed_url(path: str, expires_minutes: int = 60) -> str:
    """
    Generate a temporary download URL for a GCS file.
    Returns local path string in local mode.
    """
    if STORAGE_BACKEND == "gcs":
        import datetime
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(path)
        return blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=expires_minutes),
            method="GET",
        )
    return f"/downloads/{os.path.basename(path)}"
```

**Update `artifact_manager.py`** — Replace `joblib.dump` calls:

```python
# ADD at top of artifact_manager.py
from utils.gcs_storage import save_pickle, save_json, load_pickle, load_json

# REPLACE in save_artifacts():
# OLD:  joblib.dump(encoder_map, paths["encoders"])
# NEW:
save_pickle(encoder_map, paths["encoders"])
save_pickle(scaler_map, paths["scalers"])
save_json({"feature_columns": feature_cols}, paths["features"])
save_json(metadata, paths["metadata"])

# REPLACE in load_artifacts():
# OLD:  result["encoder_map"] = joblib.load(encoders_path)
# NEW:
result["encoder_map"] = load_pickle(encoders_path)
result["scaler_map"] = load_pickle(scalers_path)
result["feature_columns"] = load_json(features_path)["feature_columns"]
result["metadata"] = load_json(metadata_path)
```

**Update `main.py`** — Fix exports download:

```python
# REPLACE the /downloads static mount with a proper endpoint:
# REMOVE: app.mount("/downloads", StaticFiles(directory=str(EXPORTS_DIR)), name="downloads")

from utils.gcs_storage import generate_signed_url, STORAGE_BACKEND
from fastapi.responses import FileResponse, RedirectResponse

@app.get("/downloads/{filename}")
async def download_file(filename: str):
    """Serve exported files from GCS (prod) or local disk (dev)."""
    path = f"exports/{filename}"
    if STORAGE_BACKEND == "gcs":
        url = generate_signed_url(path, expires_minutes=60)
        return RedirectResponse(url)
    local_path = EXPORTS_DIR / filename
    if not local_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(local_path))
```

**Update `dataset_builder.py`** — Fix CSV exports:

```python
from utils.gcs_storage import save_csv

# REPLACE: df.to_csv("exports/file.csv", index=False)
# WITH:
save_csv(df, f"exports/{filename}.csv")
```

---

### STEP 2 — Backend Dockerfile

Create `Backend/Dockerfile`:

```dockerfile
# ── Stage 1: Dependencies ──────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# System libs needed by LightGBM, CatBoost, Prophet
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/deps -r requirements.txt

# Also install GCS client
RUN pip install --no-cache-dir --prefix=/deps google-cloud-storage==2.16.0

# ── Stage 2: Runtime ──────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime system libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages
COPY --from=builder /deps /usr/local

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Run uses PORT env variable
ENV PORT=8000
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 2
```

---

### STEP 3 — Frontend Dockerfile + Nginx

Create `frontend/Dockerfile`:

```dockerfile
# ── Stage 1: Build React App ──────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --frozen-lockfile

COPY . .

# Pass backend URL at build time
ARG VITE_API_BASE_URL=https://backend-XXXX-uc.a.run.app
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# ── Stage 2: Nginx ─────────────────────────────────────────────────
FROM nginx:1.25-alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

Create `frontend/nginx.conf`:

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # React SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Gzip compression
    gzip on;
    gzip_types text/plain application/javascript text/css application/json;
    gzip_min_length 1000;

    # Cache static assets
    location ~* \.(js|css|png|jpg|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Update `frontend/src` API base URL** — ensure all axios calls use env variable:

```javascript
// frontend/src/api/client.js  (create if doesn't exist)
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 120000,  // 2 min for heavy ML operations
});

export default api;
```

---

### STEP 4 — Docker Compose (Local Dev)

Create `docker-compose.yml` at project root:

```yaml
version: "3.9"

services:
  backend:
    build:
      context: ./Backend
      dockerfile: Dockerfile
    container_name: ai_career_backend
    ports:
      - "8000:8000"
    environment:
      - STORAGE_BACKEND=local
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - ./Backend:/app
      - artifacts_vol:/app/artifacts
      - exports_vol:/app/exports
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: builder
    container_name: ai_career_frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    volumes:
      - ./frontend/src:/app/src
    command: npm run dev -- --host 0.0.0.0

volumes:
  artifacts_vol:
  exports_vol:
```

---

### STEP 5 — GCP Setup Commands

Run these once to set up your GCP project:

```bash
# 1. Install & authenticate GCP CLI
# Download: https://cloud.google.com/sdk/docs/install

# 2. Create project
gcloud projects create ai-career-companion --name="AI Career Companion"
gcloud config set project ai-career-companion

# 3. Enable required APIs
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    storage.googleapis.com \
    secretmanager.googleapis.com

# 4. Create Docker image registry
gcloud artifacts repositories create ai-career-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="AI Career Companion Docker images"

# 5. Create GCS bucket for artifacts + exports
gsutil mb -l us-central1 gs://ai-career-artifacts
gsutil mb -l us-central1 gs://ai-career-exports

# (Or use one bucket with prefixes — recommended)
gsutil mb -l us-central1 gs://ai-career-companion-storage

# 6. Store GROQ_API_KEY in Secret Manager
echo -n "your_actual_groq_api_key" | \
    gcloud secrets create GROQ_API_KEY --data-file=-

# 7. Allow Cloud Run to access Secret Manager
gcloud secrets add-iam-policy-binding GROQ_API_KEY \
    --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

---

### STEP 6 — CI/CD with GitHub Actions (✅ Recommended over Cloud Build)

> [!TIP]
> GitHub Actions is **100% free** for public repos and integrates directly with your existing GitHub repo. No extra GCP setup needed. Cloud Build costs money after 120 min/day.

**Comparison:**

| | GitHub Actions | GCP Cloud Build |
|--|--|--|
| Cost | Free (public repo) | 120 min/day free, then paid |
| Setup | GitHub Secrets | GCP IAM + triggers |
| Familiarity | Easier | GCP-specific |
| Integration | GitHub native | Needs repo connection |
| **Verdict** | ✅ **Use this** | Skip |

Create this file structure:
```
.github/
└── workflows/
    ├── ci.yml      ← runs on every PR (lint + test)
    └── deploy.yml  ← runs on push to main (build + deploy to GCP)
```

#### `.github/workflows/ci.yml` — Lint & Test on Every PR

```yaml
name: CI — Lint & Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-lint:
    name: Backend Lint (Ruff)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install ruff
      - run: ruff check Backend/ --output-format=github

  backend-test:
    name: Backend Tests (pytest)
    runs-on: ubuntu-latest
    needs: backend-lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r Backend/requirements.txt pytest pytest-asyncio httpx
      - name: Run tests
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          STORAGE_BACKEND: local
        run: pytest Backend/tests/ -v --tb=short

  frontend-lint:
    name: Frontend Lint (ESLint)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: cd frontend && npm ci && npm run lint

  frontend-build:
    name: Frontend Build Check
    runs-on: ubuntu-latest
    needs: frontend-lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: cd frontend && npm ci && npm run build
```

#### `.github/workflows/deploy.yml` — Build & Deploy to GCP on Push to Main

```yaml
name: Deploy to GCP Cloud Run

on:
  push:
    branches: [main]

env:
  GCP_PROJECT_ID: ai-career-companion
  GCP_REGION: us-central1
  ARTIFACT_REGISTRY: us-central1-docker.pkg.dev
  REPO_NAME: ai-career-repo
  BACKEND_SERVICE: ai-career-backend
  FRONTEND_SERVICE: ai-career-frontend
  GCS_BUCKET: ai-career-companion-storage

jobs:
  deploy-backend:
    name: Build & Deploy Backend
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      # Authenticate to GCP using Service Account key stored in GitHub Secrets
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      # Configure Docker to use GCP Artifact Registry
      - name: Setup Docker for GCP
        run: gcloud auth configure-docker ${{ env.ARTIFACT_REGISTRY }} --quiet

      # Build the Backend Docker image
      - name: Build Backend Image
        run: |
          docker build ./Backend \
            -t ${{ env.ARTIFACT_REGISTRY }}/${{ env.GCP_PROJECT_ID }}/${{ env.REPO_NAME }}/backend:${{ github.sha }} \
            -t ${{ env.ARTIFACT_REGISTRY }}/${{ env.GCP_PROJECT_ID }}/${{ env.REPO_NAME }}/backend:latest

      # Push to GCP Artifact Registry
      - name: Push Backend Image
        run: |
          docker push --all-tags \
            ${{ env.ARTIFACT_REGISTRY }}/${{ env.GCP_PROJECT_ID }}/${{ env.REPO_NAME }}/backend

      # Deploy to Cloud Run
      - name: Deploy Backend to Cloud Run
        run: |
          gcloud run deploy ${{ env.BACKEND_SERVICE }} \
            --image=${{ env.ARTIFACT_REGISTRY }}/${{ env.GCP_PROJECT_ID }}/${{ env.REPO_NAME }}/backend:${{ github.sha }} \
            --region=${{ env.GCP_REGION }} \
            --platform=managed \
            --allow-unauthenticated \
            --memory=2Gi \
            --cpu=2 \
            --timeout=300 \
            --concurrency=10 \
            --min-instances=0 \
            --max-instances=3 \
            --set-env-vars="STORAGE_BACKEND=gcs,GCS_BUCKET_NAME=${{ env.GCS_BUCKET }}" \
            --set-secrets="GROQ_API_KEY=GROQ_API_KEY:latest"

      # Get the backend URL for frontend build
      - name: Get Backend URL
        id: get-backend-url
        run: |
          URL=$(gcloud run services describe ${{ env.BACKEND_SERVICE }} \
            --region=${{ env.GCP_REGION }} \
            --format='value(status.url)')
          echo "url=$URL" >> $GITHUB_OUTPUT

  deploy-frontend:
    name: Build & Deploy Frontend
    runs-on: ubuntu-latest
    needs: deploy-backend   # Wait for backend to get its URL

    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Setup Docker for GCP
        run: gcloud auth configure-docker ${{ env.ARTIFACT_REGISTRY }} --quiet

      # Get the live backend URL
      - name: Get Backend URL
        id: backend-url
        run: |
          URL=$(gcloud run services describe ${{ env.BACKEND_SERVICE }} \
            --region=${{ env.GCP_REGION }} \
            --format='value(status.url)')
          echo "url=$URL" >> $GITHUB_OUTPUT

      - name: Build Frontend Image
        run: |
          docker build ./frontend \
            --build-arg VITE_API_BASE_URL=${{ steps.backend-url.outputs.url }} \
            -t ${{ env.ARTIFACT_REGISTRY }}/${{ env.GCP_PROJECT_ID }}/${{ env.REPO_NAME }}/frontend:${{ github.sha }} \
            -t ${{ env.ARTIFACT_REGISTRY }}/${{ env.GCP_PROJECT_ID }}/${{ env.REPO_NAME }}/frontend:latest

      - name: Push Frontend Image
        run: |
          docker push --all-tags \
            ${{ env.ARTIFACT_REGISTRY }}/${{ env.GCP_PROJECT_ID }}/${{ env.REPO_NAME }}/frontend

      - name: Deploy Frontend to Cloud Run
        run: |
          gcloud run deploy ${{ env.FRONTEND_SERVICE }} \
            --image=${{ env.ARTIFACT_REGISTRY }}/${{ env.GCP_PROJECT_ID }}/${{ env.REPO_NAME }}/frontend:${{ github.sha }} \
            --region=${{ env.GCP_REGION }} \
            --platform=managed \
            --allow-unauthenticated \
            --memory=256Mi \
            --cpu=1
```

#### GitHub Secrets Required

Go to: **GitHub Repo → Settings → Secrets and variables → Actions → New secret**

| Secret Name | How to Get It |
|-------------|---------------|
| `GCP_SA_KEY` | GCP Service Account JSON key (see below) |
| `GROQ_API_KEY` | Your Groq API key |

**Create the GCP Service Account key:**
```bash
# Create a service account for GitHub Actions
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions Deployer"

# Grant required permissions
gcloud projects add-iam-policy-binding ai-career-companion \
    --member="serviceAccount:github-actions@ai-career-companion.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding ai-career-companion \
    --member="serviceAccount:github-actions@ai-career-companion.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding ai-career-companion \
    --member="serviceAccount:github-actions@ai-career-companion.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding ai-career-companion \
    --member="serviceAccount:github-actions@ai-career-companion.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# Download the key as JSON → paste into GitHub Secret GCP_SA_KEY
gcloud iam service-accounts keys create gcp-key.json \
    --iam-account=github-actions@ai-career-companion.iam.gserviceaccount.com

# Copy the contents of gcp-key.json into GitHub Secret
cat gcp-key.json
# (then delete the local file!)
del gcp-key.json
```

---

### STEP 7 — How the Full Flow Works After Setup

```
You push code to GitHub (main branch)
           │
           ▼
  GitHub Actions triggers
           │
    ┌──────┴──────┐
    │             │
 ci.yml       deploy.yml
(on PR)      (on main push)
    │             │
  Lint         Build Backend Docker image
  Test         Push to GCP Artifact Registry
               Deploy to Cloud Run
               Build Frontend (with live backend URL)
               Deploy Frontend to Cloud Run
           │
           ▼
  Your app is live! 🎉
```

---

### STEP 8 — Manual First Deploy

```bash
# Authenticate Docker to GCP
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build and push backend manually (first time)
docker build ./Backend \
    -t us-central1-docker.pkg.dev/ai-career-companion/ai-career-repo/backend:v1

docker push us-central1-docker.pkg.dev/ai-career-companion/ai-career-repo/backend:v1

# Deploy backend to Cloud Run
gcloud run deploy ai-career-backend \
    --image=us-central1-docker.pkg.dev/ai-career-companion/ai-career-repo/backend:v1 \
    --region=us-central1 \
    --platform=managed \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --set-env-vars="STORAGE_BACKEND=gcs,GCS_BUCKET_NAME=ai-career-companion-storage" \
    --set-secrets="GROQ_API_KEY=GROQ_API_KEY:latest"

# Get backend URL (you'll need this for frontend)
gcloud run services describe ai-career-backend \
    --region=us-central1 \
    --format='value(status.url)'

# Build and push frontend (use the backend URL you just got)
docker build ./frontend \
    --build-arg VITE_API_BASE_URL=https://ai-career-backend-XXXX-uc.a.run.app \
    -t us-central1-docker.pkg.dev/ai-career-companion/ai-career-repo/frontend:v1

docker push us-central1-docker.pkg.dev/ai-career-companion/ai-career-repo/frontend:v1

# Deploy frontend
gcloud run deploy ai-career-frontend \
    --image=us-central1-docker.pkg.dev/ai-career-companion/ai-career-repo/frontend:v1 \
    --region=us-central1 \
    --platform=managed \
    --allow-unauthenticated \
    --memory=256Mi
```

---

## 5. Solving the Artifact & Exports Problem — Complete Picture

```
USER uploads CSV
      │
      ▼
Cloud Run (Backend)
      │
      ├── Runs Module 1, 2, 3, 4 (in memory — no disk needed)
      │
      ├── Saves encoders.pkl  ──────▶  GCS: artifacts/run_001/encoders.pkl
      ├── Saves scalers.pkl   ──────▶  GCS: artifacts/run_001/scalers.pkl
      ├── Saves metadata.json ──────▶  GCS: artifacts/run_001/metadata.json
      │
      ├── Saves ML-ready CSV  ──────▶  GCS: exports/hr_ml_20260516.csv
      └── Saves analytics CSV ──────▶  GCS: exports/hr_analytics_20260516.csv
                                                │
USER clicks Download                            │
      │                                         │
      ▼                                         │
Backend generates signed URL ◀──────────────────┘
(valid for 60 minutes)
      │
      ▼
Browser downloads directly from GCS (no backend involved)
```

**This solves**:
- ✅ Files survive container restarts
- ✅ Files available across all instances
- ✅ Downloads don't use Cloud Run memory/bandwidth
- ✅ Automatic 7-day expiry via GCS lifecycle rules

**Set GCS lifecycle to auto-delete old exports:**

```bash
cat > lifecycle.json << 'EOF'
{
  "lifecycle": {
    "rule": [{
      "action": {"type": "Delete"},
      "condition": {"age": 7}
    }]
  }
}
EOF

# Apply only to exports prefix
gsutil lifecycle set lifecycle.json gs://ai-career-companion-storage
```

---

## 6. Environment Variables Summary

| Variable | Local Dev | GCP Production |
|----------|-----------|---------------|
| `GROQ_API_KEY` | `.env` file | Secret Manager |
| `STORAGE_BACKEND` | `local` | `gcs` |
| `GCS_BUCKET_NAME` | _(not needed)_ | `ai-career-companion-storage` |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Cloud Run backend URL |

---

## 7. Add to `requirements.txt`

```
google-cloud-storage==2.16.0
```

---

## 8. `.dockerignore`

Create at project root and in `Backend/`:

```
**/__pycache__
**/*.pyc
**/*.pyo
**/.env
**/.env.*
**/node_modules
**/dist
**/.ruff_cache
**/logs
**/artifacts
**/exports
**/.git
**/*.docx
**/*.pdf
**/tests
```

---

## 9. Phased Execution Timeline

| Day | Task |
|-----|------|
| **Day 1** | Create `gcs_storage.py`, update `artifact_manager.py`, `dataset_builder.py`, `main.py` |
| **Day 2** | Create `Backend/Dockerfile`, test locally with `docker build` |
| **Day 3** | Create `frontend/Dockerfile` + `nginx.conf`, test locally |
| **Day 4** | Create `docker-compose.yml`, run full stack locally with Docker |
| **Day 5** | GCP setup: create project, enable APIs, create bucket, add secrets |
| **Day 6** | Manual first deploy (backend → Cloud Run), get URL, deploy frontend |
| **Day 7** | Connect GitHub → Cloud Build, test automated CI/CD pipeline |
| **Day 8** | Test full flow: upload CSV → process → download from GCS |

---

## 10. Cloud Run Sizing Guide

| Service | Memory | CPU | Why |
|---------|--------|-----|-----|
| Backend | **2 GB** | **2** | CatBoost + LightGBM + Prophet are memory hungry |
| Frontend | 256 MB | 1 | Just Nginx serving static files |

> [!WARNING]
> If backend crashes with OOM errors, increase to `--memory=4Gi`. Heavy models like CatBoost can use 1–2 GB during training on large datasets.

> [!NOTE]
> Cloud Run scales to **zero instances** when idle — you pay nothing when no one is using the app. First request after idle takes ~3–5 seconds (cold start). Set `--min-instances=1` if you need instant response.
