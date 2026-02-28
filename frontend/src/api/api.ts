import axios, { AxiosResponse } from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export interface BackendResponse<T = any> {
  success: boolean;
  data: T;
  error?: string;
  timestamp: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  role: 'user';
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    email: string;
    role: string;
  };
}

export interface Document {
  id: number;
  filename: string;
  upload_date: string;
}

export interface RegulatoryChangeCreate {
  change_type: string;
  description: string;
  effective_date: string;
}

export interface RegulatoryImpactAnalysisRequest {
  scenario: string;
  timeframe: string;
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config: any) => {
  const token = localStorage.getItem('token');
  if (token && !config.skipAuth) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const apiCall = async <T>(
  method: 'GET' | 'POST' | 'PUT' | 'DELETE',
  endpoint: string,
  data?: any,
  skipAuth: boolean = false
): Promise<BackendResponse<T>> => {
  try {
    const config: any = { skipAuth };
    let response: AxiosResponse<BackendResponse<T>>;

    switch (method) {
      case 'GET':
        response = await api.get<BackendResponse<T>>(endpoint, config);
        break;
      case 'POST':
        response = await api.post<BackendResponse<T>>(endpoint, data, config);
        break;
      case 'PUT':
        response = await api.put<BackendResponse<T>>(endpoint, data, config);
        break;
      case 'DELETE':
        response = await api.delete<BackendResponse<T>>(endpoint, config);
        break;
      default:
        throw new Error(`Unsupported method: ${method}`);
    }

    return response.data;
  } catch (error: any) {
    console.error(`API Error [${method}] ${endpoint}:`, error);
    throw error;
  }
};

export const authAPI = {
  register: (data: RegisterRequest) => 
    apiCall<AuthResponse>('POST', '/auth/register', data, true),
  
  login: (data: LoginRequest) => 
    apiCall<AuthResponse>('POST', '/auth/login', data, true),
  
  validate: () => 
    apiCall<any>('GET', '/auth/validate'),
};

export const documentsAPI = {
  getDocuments: () => 
    apiCall<Document[]>('GET', '/documents'),
  
  upload: (formData: FormData) => {
    const token = localStorage.getItem('token');
    return axios.post(`${API_BASE_URL}/documents/upload`, formData, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  },
};

export const analysisAPI = {
  assessRisk: (documentId: number) => 
    apiCall<any>('POST', `/risk/assess/${documentId}`),
  
  simulateRegulatory: (documentId: number, data: RegulatoryChangeCreate) => 
    apiCall<any>('POST', `/regulatory/simulate/${documentId}`, data),
  
  analyzeReputation: (documentId: number) => 
    apiCall<any>('POST', `/reputation/analyze/${documentId}`),
  
  analyzeImpact: (documentId: number, data: RegulatoryImpactAnalysisRequest) => 
    apiCall<any>('POST', `/impact/analyze/${documentId}`, data),
};
