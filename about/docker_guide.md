# Docker & Containerization Stack Guide

This guide provides a comprehensive overview of the newly added Docker configuration files, how they fit into the project architecture, and how to use them for both local development and production.

---

## 🏗️ Containerization Architecture

Below is a conceptual layout of the multi-container setup configured for this project:

```mermaid
graph TD
    User([User Browser]) -->|Port 80 / 5173| Frontend[Frontend Container\nReact + Vite / Nginx]
    Frontend -->|Proxy /api/* to Port 8000| Backend[Backend Container\nFastAPI + Uvicorn]
    Backend -->|Log runs/artifacts| MLflow[MLflow Server Container\nTracking UI]
    
    subgraph Storage Volumes
        artifacts[(backend_artifacts)] <---> Backend
        exports[(backend_exports)] <---> Backend
        mlflow_data[(mlflow_data)] <---> MLflow
    end
```

---

## 📁 Created Configurations

The following files have been created in the workspace:

| File Path | Purpose | Key Optimization / Features |
| :--- | :--- | :--- |
| **`Backend/Dockerfile`** | Containerizes Python FastAPI service | Multi-stage slim build, ML dependencies (`xgboost`/`lightgbm`/etc.), standard-library-based health check, non-root security user (`appuser`). |
| **`frontend/Dockerfile`** | Containerizes React/Vite web application | Multi-stage build (Node builder + Nginx runtime for production hosting). |
| **`frontend/nginx.conf`** | Configures Nginx for Frontend serving | Implements **SPA routing** (redirects unmatched URLs to `index.html`), proxies `/api/` and `/downloads/` to the backend. |
| **`docker-compose.yml`** | Configures local development | Hot-reloading via volume bind mounts (protecting container `node_modules` from local overrides), spins up MLflow dashboard. |
| **`docker-compose.prod.yml`** | Configures production deployment | Relies on immutable tagged registry images, automatic restarts, and isolated secure networks. |
| **`.dockerignore`** | Optimizes container builds | Prevents bloating containers with local virtual environments (`.venv`), node modules, logs, or sensitive `.env` credentials. |

---

## 🚀 Running the App Locally (Development)

To spin up the entire application stack locally with hot-reloading and tracking enabled:

### 1. Build and Run
Execute the following command from the root project directory:
```bash
docker compose up --build
```

### 2. Standard Service Endpoints
Once the containers are up, access the applications at:
* **Frontend Application**: `http://localhost:5173`
* **FastAPI Docs (Swagger)**: `http://localhost:8000/docs`
* **Health Check Status**: `http://localhost:8000/health`
* **MLflow Tracking Dashboard**: `http://localhost:5000`

### 3. Running Tests Inside the Container
To run unit tests or lint checks in the containerized development environment:
```bash
docker exec -it ai_career_backend pytest -v
```

---

## 🔒 Production Deployment Overview

In a production environment (such as GCP, AWS, or a custom VPS), images are built by a CI/CD pipeline (e.g. GitHub Actions) and pushed to a registry:

1. **Building Images**:
   ```bash
   docker build -t your-username/ai-career-companion/backend:latest ./Backend
   docker build -t your-username/ai-career-companion/frontend:latest ./frontend
   ```

2. **Deploying on Server**:
   Place `docker-compose.prod.yml` on your server and start:
   ```bash
   docker compose -f docker-compose.prod.yml pull
   docker compose -f docker-compose.prod.yml up -d
   ```

> [!TIP]
> **Why Multi-Stage Builds?**
> Standard Python and Node environments can result in images larger than 2GB. By compiling dependencies or building static bundles in the first stage and copying only the outputs to a minimal second stage, image sizes are reduced by up to **80%**, making deployments faster and reducing the attack surface.
