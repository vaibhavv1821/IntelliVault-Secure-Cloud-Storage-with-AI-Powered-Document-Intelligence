import axios from 'axios';

// Base API instance configured for /api
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getHealth = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    return {
      success: false,
      error: {
        message: error.message || 'Unable to reach backend API',
        code: error.code || 'NETWORK_ERROR'
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
        message: error.message || 'Unable to fetch system diagnostic status',
        code: error.code || 'NETWORK_ERROR'
      }
    };
  }
};

export default apiClient;
