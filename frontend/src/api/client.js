import axios from 'axios';

const getApiBaseUrl = () => {
  let url = (import.meta.env.VITE_API_URL || '').trim();
  if (url) {
    // Remove trailing slash and remove duplicate /api if included
    url = url.replace(/\/+$/, '');
    if (url.endsWith('/api')) {
      url = url.slice(0, -4);
    }
    return url;
  }
  if (typeof window !== 'undefined' && window.location && window.location.hostname) {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://127.0.0.1:8000';
    }
    return `http://${window.location.hostname}:8000`;
  }
  return 'http://127.0.0.1:8000';
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export { API_BASE_URL };

// Attach JWT token automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('sales_auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle global 401 unauthenticated
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token and let state handle redirect if needed
      if (!window.location.pathname.includes('/login')) {
        localStorage.removeItem('sales_auth_token');
        localStorage.removeItem('sales_auth_user');
      }
    }
    return Promise.reject(error);
  }
);

export default api;
