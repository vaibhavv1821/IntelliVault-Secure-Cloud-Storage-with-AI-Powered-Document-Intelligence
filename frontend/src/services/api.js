import axios from 'axios';

// Base API instance configured for /api
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Storage token helper functions
export const getAuthToken = () => localStorage.getItem('intellivault_token');
export const setAuthToken = (token) => localStorage.setItem('intellivault_token', token);
export const clearAuthToken = () => localStorage.removeItem('intellivault_token');

// Request interceptor: attach Bearer token if present
apiClient.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

// System probes
export const getHealth = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    return {
      success: false,
      error: {
        message: error.response?.data?.error?.message || error.message || 'Unable to reach backend API',
        code: error.response?.data?.error?.code || 'NETWORK_ERROR'
      }
    };
  }
};

export const getSystemStatus = async () => {
  try {
    const response = await apiClient.get('/system/status');
    return response.data;
  } catch (error) {
    return {
      success: false,
      error: {
        message: error.response?.data?.error?.message || error.message || 'Unable to fetch system status',
        code: error.response?.data?.error?.code || 'NETWORK_ERROR'
      }
    };
  }
};

// Authentication API calls
export const registerApi = async (name, email, password) => {
  try {
    const response = await apiClient.post('/auth/register', { name, email, password });
    return response.data;
  } catch (error) {
    return {
      success: false,
      error: {
        message: error.response?.data?.error?.message || error.message || 'Registration failed',
        code: error.response?.data?.error?.code || 'REGISTRATION_ERROR'
      }
    };
  }
};

export const loginApi = async (email, password) => {
  try {
    const response = await apiClient.post('/auth/login', { email, password });
    return response.data;
  } catch (error) {
    return {
      success: false,
      error: {
        message: error.response?.data?.error?.message || error.message || 'Login failed',
        code: error.response?.data?.error?.code || 'LOGIN_ERROR'
      }
    };
  }
};

export const getMeApi = async () => {
  try {
    const response = await apiClient.get('/auth/me');
    return response.data;
  } catch (error) {
    return {
      success: false,
      error: {
        message: error.response?.data?.error?.message || error.message || 'Authentication session invalid',
        code: error.response?.data?.error?.code || 'AUTH_ERROR'
      }
    };
  }
};

// File Management API calls
export const uploadFileApi = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    return {
      success: false,
      error: {
        message: error.response?.data?.error?.message || error.message || 'File upload failed',
        code: error.response?.data?.error?.code || 'UPLOAD_ERROR',
      },
    };
  }
};

export const getFilesApi = async () => {
  try {
    const response = await apiClient.get('/files');
    return response.data;
  } catch (error) {
    return {
      success: false,
      error: {
        message: error.response?.data?.error?.message || error.message || 'Failed to fetch files',
        code: error.response?.data?.error?.code || 'FETCH_FILES_ERROR',
      },
    };
  }
};

export default apiClient;

