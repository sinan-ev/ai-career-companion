# AI Career Companion Dashboard (React + Vite)

The frontend is a robust, dynamic React application optimized for a premium user experience and seamless integration with the AI Data Intelligence pipeline.

## 🎨 Design & Features

- **Dark Mode Aesthetics**: Sleek, glass-morphism components with vibrant color palettes and micro-animations to ensure a premium feel.
- **Interactive Visualizations**: Leverages **Recharts** and **Plotly** to render dynamic, interactive, AI-planned business charts.
- **AI Chatbot**: A responsive chat interface connected to the backend RAG store, providing persona-based, jargon-free business intelligence about the uploaded datasets.
- **Optimized Performance**: State management is handled carefully to prevent unnecessary re-renders (especially UI lag associated with complex data/charts), and the UI seamlessly handles parallel backend processes.

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation
```bash
cd frontend
npm install
```

### Running Locally
```bash
npm run dev
```

### Build for Production
```bash
npm run build
```

## 📂 Key Components
- **`UploadZone`**: The landing area for drag-and-drop file processing, highlighting Module 3 capabilities.
- **`PipelineView`**: A visual tracer showing how the AI preprocessed the data step-by-step.
- **`AnalystView`**: The core dashboard for Module 3 containing charts, automated insights, and the AI chatbot.

## 🛠 Technologies
- React 18, Vite
- TailwindCSS / Vanilla CSS (with modern variables)
- Recharts, Plotly.js
- Lucide React (Icons)
