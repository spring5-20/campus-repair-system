import { request } from './client';

export const api = {
  get: (url, config) => request({ method: 'get', url, ...config }),
  post: (url, data, config) => request({ method: 'post', url, data, ...config }),
  put: (url, data, config) => request({ method: 'put', url, data, ...config }),
  patch: (url, data, config) => request({ method: 'patch', url, data, ...config }),
  delete: (url, config) => request({ method: 'delete', url, ...config }),
};

export default api;
