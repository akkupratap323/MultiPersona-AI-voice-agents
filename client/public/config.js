// Runtime configuration — overwritten by docker-entrypoint.sh in production.
// For local development, these defaults point to the FastAPI dev server.
// DO NOT commit production values here.
window.__BACKEND_URL__ = "";
window.__WS_URL__ = "";
window.LIGHTRAG_URL = "";
window.LIGHTRAG_API_KEY = "";
window.__VERSION__ = "dev";
