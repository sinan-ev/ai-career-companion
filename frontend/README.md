# AI Data Intelligence Dashboard (React + Vite)

The frontend is a modern Single Page Application (SPA) built using React 18, Vite, and custom Vanilla CSS. It provides a visual dashboard to upload datasets, view step-by-step cleaning pipelines, inspect data charts, and chat with the AI Analyst or Future Decision Intelligence cores.

---

## 🎨 Design & Aesthetic System

The user interface follows premium visual design standards:
*   **Vibrant Dark Mode**: Built around curated, harmonious HSL/HEX color tokens (deep backgrounds, neon accent borders, active indicator glows).
*   **Glassmorphism Layouts**: Component boxes feature semi-transparent backgrounds (`rgba` backdrops), subtle border outlines, and blurred backdrops (`backdrop-filter: blur(12px)`) for depth.
*   **Micro-Animations**: Hover actions trigger smooth transition transformations (`scale`, `translate-y`), active states use glowing box shadows, and processing indicators use custom spin animations.
*   **Typography**: Relies on modern, high-legibility Google Fonts (e.g. Inter, Outfit) to deliver a polished executive interface.

---

## 📂 Key Components

1.  **`UploadZone`**: Serves as the user entry point. Handles drag-and-drop actions, validates file sizes, and streams binary file uploads to `/api/process`.
2.  **`PipelineView`**: Renders a vertical step tracer that reads Module 2's execution memory. Displays the success, duration, and details of each cleaning step (e.g. imputations, scaling, column drops).
3.  **`AnalystView`**: The primary analytical workspace. Renders automated business insights and hosts the interactive charting panel.
4.  **`ChatBot`**: A sticky conversational assistant. Grounded in the dataset's context, allowing users to query trends and request aggregations in plain business English.

---

## 🛠️ API & Routing Integration

### SPA Routing Setup
To support clean client-side routing on static hosting providers:
*   **Vercel (`vercel.json`)**: Configured with a URL rewrite rule that forwards all unmatched routes to `index.html` (preventing 404 errors on browser refreshes).
*   **Nginx (`nginx.conf`)**: In Dockerized production modes, Nginx uses `try_files $uri $uri/ /index.html` to handle client-side URLs and proxies API traffic (`/api/*`) directly to the backend container.

### API Environment Configuration
The frontend communicates with the FastAPI server using the `VITE_API_URL` variable.
*   **Local Development**: Vite sets `VITE_API_URL` to `http://localhost:8000` (handled automatically by `docker-compose.yml`).
*   **Production Deployment**: Set `VITE_API_URL` to your live Google Cloud Run service URL in Vercel's project dashboard.

---

## 🚀 Getting Started

### Prerequisites
*   Node.js 18+
*   npm or yarn

### 1. Installation
Navigate to the frontend directory and install dependencies:
```bash
cd frontend
npm install
```

### 2. Local Run (Development Server)
Start the hot-reloading development server:
```bash
npm run dev
```
Open `http://localhost:5173` in your browser.

### 3. Production Build
Compile the application into optimized static assets:
```bash
npm run build
```
The compiled files will be outputted to `/frontend/dist/`, ready to be served by Nginx or uploaded to static hosting.
