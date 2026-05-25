# ── Stage 1: Build React/Vite SPA ──────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency definition
COPY package*.json ./

# Install dependencies (frozen lockfile for reproducible builds in CI)
RUN npm ci

# Copy source code and build
COPY . .
RUN npm run build

# ── Stage 2: Serve static files with Nginx ────────────────────────
FROM nginx:stable-alpine AS runtime

# Copy built React assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
