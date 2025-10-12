import { Request, RequestCreate, ExtractedData } from '@/types/request';

const API_BASE_URL = 'http://localhost:8000/api';

export const api = {
  async getRequests(): Promise<Request[]> {
    const response = await fetch(`${API_BASE_URL}/requests`);
    if (!response.ok) throw new Error('Failed to fetch requests');
    return response.json();
  },

  async createRequest(data: RequestCreate): Promise<Request> {
    const response = await fetch(`${API_BASE_URL}/requests`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create request');
    return response.json();
  },

  async uploadPDF(file: File): Promise<{ extracted_data: ExtractedData }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/requests/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('Failed to upload PDF');
    return response.json();
  },

  async updateStatus(id: number, status: string): Promise<Request> {
    const response = await fetch(`${API_BASE_URL}/requests/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    if (!response.ok) throw new Error('Failed to update status');
    return response.json();
  },
};
