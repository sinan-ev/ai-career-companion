/**
 * Dynamic API Configuration
 * --------------------------
 * - In local development: defaults to 'http://localhost:8000' (or your local backend container).
 * - In production: Vite reads the 'VITE_API_BASE_URL' environment variable injected at container build time.
 */

export const BACKEND_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const API_URL = `${BACKEND_URL}/api`;

console.log(`[API Config] Connecting to Backend at: ${BACKEND_URL}`);
