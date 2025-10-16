import { Request, RequestCreate, RequestUpdate, ExtractedData, CommodityGroup } from '@/types/request';

const API_BASE_URL = 'http://localhost:8000/api';

export const api = {
  async getRequests(): Promise<Request[]> {
    const response = await fetch(`${API_BASE_URL}/requests`);
    if (!response.ok) throw new Error('Failed to fetch requests');
    return response.json();
  },

  async createRequest(data: RequestCreate, pdfFile?: File): Promise<Request> {
    if (pdfFile) {
      const formData = new FormData();
      formData.append('request_data', JSON.stringify(data));
      formData.append('file', pdfFile);
      
      const response = await fetch(`${API_BASE_URL}/requests/with-pdf`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Failed to create request');
      return response.json();
    } else {
      const response = await fetch(`${API_BASE_URL}/requests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to create request');
      return response.json();
    }
  },

  async updateRequest(id: number, data: RequestUpdate): Promise<Request> {
    const response = await fetch(`${API_BASE_URL}/requests/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update request');
    return response.json();
  },

  async extractPDF(file: File): Promise<{ extracted_data: ExtractedData }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/requests/extract`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('Failed to extract PDF data');
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

  async getCommodityGroups(): Promise<CommodityGroup[]> {
    const response = await fetch(`${API_BASE_URL}/commodity-groups`);
    if (!response.ok) throw new Error('Failed to fetch commodity groups');
    return response.json();
  },

  async deleteRequest(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/requests/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete request');
  },

  async downloadPDF(requestId: number): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/requests/${requestId}/download-pdf`);
    if (!response.ok) throw new Error('Failed to download PDF');
    return response.blob();
  },
};
