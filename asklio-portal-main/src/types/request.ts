export interface OrderLine {
  position_description: string;
  unit_price: number;
  amount: number;
  unit: string;
  total_price: number;
}

export interface CommodityGroup {
  id: number;
  category: string;
  name: string;
}

export interface Request {
  id: number;
  requestor_name: string;
  title: string;
  vendor_name: string;
  vat_id: string;
  commodity_group_id: number | null;
  commodity_group?: string;
  total_cost: number;
  department: string;
  status: 'open' | 'in_progress' | 'closed';
  order_lines: OrderLine[];
  created_at: string;
  updated_at: string;
  currency?: string;
}

export interface RequestCreate {
  requestor_name: string;
  title: string;
  vendor_name: string;
  vat_id: string;
  commodity_group_id?: number;
  total_cost: number;
  department: string;
  order_lines: OrderLine[];
}

export interface RequestUpdate {
  requestor_name?: string;
  title?: string;
  vendor_name?: string;
  vat_id?: string;
  department?: string;
  total_cost?: number;
  commodity_group_id?: number;
}

export interface ExtractedData {
  vendor_name?: string;
  vat_id?: string;
  requestor_name?: string;
  requestor_department?: string;
  title?: string;
  order_lines?: OrderLine[];
  total_cost?: number;
  currency?: string;
  confidence?: number;
  commodity_group?: number;
}
