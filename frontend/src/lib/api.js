import axios from "axios";

const host = typeof window !== "undefined" && window.location.hostname ? window.location.hostname : "127.0.0.1";
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || `http://${host}:8000`;
export const API = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API,
  withCredentials: true,
});

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("agri_token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401 && !window.location.pathname.startsWith("/login")) {
      localStorage.removeItem("agri_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;

export const fmtCurrency = (n, symbol = "₹") =>
  `${symbol}${(Number(n) || 0).toLocaleString("en-IN", { maximumFractionDigits: 2, minimumFractionDigits: 2 })}`;

export const fmtDate = (iso) => {
  if (!iso) return "-";
  try {
    const d = new Date(iso);
    if (isNaN(d)) return iso;
    return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  } catch {
    return iso;
  }
};

export const todayISO = () => new Date().toISOString().slice(0, 10);
