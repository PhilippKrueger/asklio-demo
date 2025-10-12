// TypeScript types for the Procurement Request System

export interface CommodityGroup {
  id: number;
  category: string;
  name: string;
}

export interface OrderLine {
  id?: number;
  request_id?: number;
  position_description: string;
  unit_price: number;
  amount: number;
  unit: string;
  total_price: number;
}

export interface Request {
  id: number;
  requestor_name: string;
  title: string;
  vendor_name: string;
  vat_id: string | null;
  department: string | null;
  total_cost: number;
  commodity_group_id: number | null;
  commodity_group_confidence: number | null;
  status: 'Open' | 'In Progress' | 'Closed';
  pdf_path: string | null;
  pdf_filename: string | null;
  created_at: string;
  updated_at: string;
  order_lines: OrderLine[];
}

export interface CreateRequestData {
  requestor_name: string;
  title: string;
  vendor_name: string;
  vat_id?: string;
  department?: string;
  total_cost: number;
  commodity_group_id?: number;
  order_lines: Omit<OrderLine, 'id' | 'request_id'>[];
}

export interface ExtractedData {
  vendor_name: string;
  vat_id: string | null;
  department: string | null;
  order_lines: Omit<OrderLine, 'id' | 'request_id'>[];
  total_cost: number;
  confidence: number;
}

export interface PDFUploadResponse {
  extracted_data: ExtractedData;
  message: string;
}

export interface CommodityClassification {
  commodity_group_id: number;
  commodity_group_name: string;
  confidence: number;
  reasoning: string | null;
}
