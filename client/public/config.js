// Runtime configuration — overwritten by docker-entrypoint.sh in production.
// For local development, these defaults point to the FastAPI dev server.
// DO NOT commit production values here.
window.__BACKEND_URL__ = "http://localhost:7860";
window.__WS_URL__ = "ws://localhost:7860";
window.LIGHTRAG_URL = "";
window.LIGHTRAG_API_KEY = "";
window.__VERSION__ = "dev";
