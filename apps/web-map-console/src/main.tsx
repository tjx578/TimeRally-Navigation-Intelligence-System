import React from "react";
import ReactDOM from "react-dom/client";
import "maplibre-gl/dist/maplibre-gl.css";
import "./styles/app.css";
import { App } from "./App";
import { flushOfflineQueue } from "./lib/offline/offlineQueue";
import { registerServiceWorker } from "./lib/offline/registerServiceWorker";

registerServiceWorker();
void flushOfflineQueue(import.meta.env.VITE_API_BASE_URL ?? "");
window.addEventListener("online", () => {
  void flushOfflineQueue(import.meta.env.VITE_API_BASE_URL ?? "");
});

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
