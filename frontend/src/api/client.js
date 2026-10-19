import axios from 'axios';

const AUTH_TOKEN_KEY = 'token';

export const setAuthToken = (token) => {
  if (token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    return;
  }
  localStorage.removeItem(AUTH_TOKEN_KEY);
};

export const getAuthToken = () => localStorage.getItem(AUTH_TOKEN_KEY) || '';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = getAuthToken();
  const headers = config.headers || {};

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  } else {
    delete headers.Authorization;
  }

  config.headers = headers;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error?.response?.data?.message || error?.message || '请求失败';
    return Promise.reject(new Error(message));
  },
);

export const request = async ({ method = 'get', url, data, params, headers }) => {
  const response = await apiClient.request({
    method,
    url,
    data,
    params,
    headers,
  });

  return response.data;
};

export default apiClient;
