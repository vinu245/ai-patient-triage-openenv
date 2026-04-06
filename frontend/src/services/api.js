import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
});

export async function fetchState() {
  const { data } = await api.get("/state");
  return data;
}

export async function fetchMetrics() {
  const { data } = await api.get("/metrics");
  return data;
}

export async function sendStep(action = null) {
  const { data } = await api.post("/step", { action });
  return data;
}

export async function resetEnv() {
  const { data } = await api.post("/reset");
  return data;
}
