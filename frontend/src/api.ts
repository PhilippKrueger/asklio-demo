// API client for backend communication

import axios from 'axios';
import type {
  Request,
  CreateRequestData,
  PDFUploadResponse,
  CommodityGroup,
  CommodityClassification,
} from './types';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Requests
export const getRequests = async (status?: string): Promise<Request[]> => {
  const params = status ? { status } : {};
  const response = await api.get<Request[]>('/requests', { params });
  return response.data;
};

export const getRequest = async (id: number): Promise<Request> => {
  const response = await api.get<Request>(`/requests/${id}`);
  return response.data;
};

export const createRequest = async (data: CreateRequestData): Promise<Request> => {
  const response = await api.post<Request>('/requests', data);
  return response.data;
};

export const updateRequestStatus = async (
  id: number,
  status: 'Open' | 'In Progress' | 'Closed'
): Promise<Request> => {
  const response = await api.patch<Request>(`/requests/${id}/status`, { status });
  return response.data;
};

export const deleteRequest = async (id: number): Promise<void> => {
  await api.delete(`/requests/${id}`);
};

// PDF Upload
export const uploadPDF = async (file: File): Promise<PDFUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<PDFUploadResponse>('/requests/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

// Commodity Groups
export const getCommodityGroups = async (): Promise<CommodityGroup[]> => {
  const response = await api.get<CommodityGroup[]>('/commodity-groups');
  return response.data;
};

export const searchCommodityGroups = async (query: string): Promise<CommodityGroup[]> => {
  const response = await api.get<CommodityGroup[]>('/commodity-groups/search', {
    params: { q: query },
  });
  return response.data;
};

export const classifyText = async (text: string): Promise<CommodityClassification> => {
  const response = await api.post<CommodityClassification>('/commodity-groups/classify', {
    text,
  });
  return response.data;
};
