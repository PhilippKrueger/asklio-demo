// Main dashboard with brutal grid layout

import { useEffect, useState } from 'react';
import PDFUpload from './components/PDFUpload';
import RequestsKanban from './components/RequestsKanban';
import RequestDetail from './components/RequestDetail';
import { getRequests, createRequest, getCommodityGroups } from './api';
import type { Request, ExtractedData, CreateRequestData, CommodityGroup } from './types';

export default function App() {
  const [requests, setRequests] = useState<Request[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<Request | null>(null);
  const [extractedData, setExtractedData] = useState<ExtractedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [creatingRequest, setCreatingRequest] = useState(false);
  const [commodityGroups, setCommodityGroups] = useState<Map<number, string>>(new Map());

  const loadRequests = async () => {
    try {
      setLoading(true);
      const data = await getRequests();
      setRequests(data);
    } catch (error) {
      console.error('Failed to load requests:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRequests();
    loadCommodityGroups();
  }, []);

  const loadCommodityGroups = async () => {
    try {
      const groups = await getCommodityGroups();
      const groupMap = new Map<number, string>();
      groups.forEach((group) => {
        groupMap.set(group.id, group.name);
      });
      setCommodityGroups(groupMap);
    } catch (error) {
      console.error('Failed to load commodity groups:', error);
    }
  };

  const handleDataExtracted = (data: ExtractedData) => {
    setExtractedData(data);
  };

  const handleCreateRequest = async () => {
    if (!extractedData) return;

    const requestData: CreateRequestData = {
      requestor_name: 'Auto-Extracted',
      title: `Request from ${extractedData.vendor_name}`,
      vendor_name: extractedData.vendor_name,
      vat_id: extractedData.vat_id || undefined,
      department: extractedData.department || undefined,
      total_cost: extractedData.total_cost,
      order_lines: extractedData.order_lines,
    };

    try {
      setCreatingRequest(true);
      await createRequest(requestData);
      await loadRequests();
      setExtractedData(null);
    } catch (error) {
      console.error('Failed to create request:', error);
    } finally {
      setCreatingRequest(false);
    }
  };

  const handleCancelExtracted = () => {
    setExtractedData(null);
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b-4 border-black p-6 bg-black text-white">
        <h1 className="text-4xl font-bold">PROCUREMENT REQUEST SYSTEM</h1>
        <div className="text-sm opacity-60 mt-1">AUTOMATED EXTRACTION & CLASSIFICATION</div>
      </header>

      <div className="p-6">
        {/* Centered Upload Area */}
        <div className="flex justify-center mb-6">
          <div className="w-[600px] h-[600px]">
            <PDFUpload onDataExtracted={handleDataExtracted} />
          </div>
        </div>

        {/* Extracted Data Preview */}
        {extractedData && (
          <div className="border-4 border-black p-6 mb-6 bg-yellow-50">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-2xl font-bold">EXTRACTED DATA</h2>
                <div className="text-sm opacity-60">
                  CONFIDENCE: {(extractedData.confidence * 100).toFixed(0)}%
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleCreateRequest}
                  disabled={creatingRequest}
                  className="border-3 border-black px-6 py-2 bg-black text-white hover:bg-white hover:text-black transition-colors duration-100 disabled:opacity-50"
                >
                  {creatingRequest ? 'CREATING...' : 'CREATE REQUEST'}
                </button>
                <button
                  onClick={handleCancelExtracted}
                  className="border-3 border-black px-6 py-2 hover:bg-black hover:text-white transition-colors duration-100"
                >
                  CANCEL
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="opacity-60">VENDOR</div>
                <div className="font-bold">{extractedData.vendor_name}</div>
              </div>
              <div>
                <div className="opacity-60">VAT ID</div>
                <div className="font-mono">{extractedData.vat_id || 'N/A'}</div>
              </div>
              <div>
                <div className="opacity-60">DEPARTMENT</div>
                <div>{extractedData.department || 'N/A'}</div>
              </div>
              <div>
                <div className="opacity-60">TOTAL COST</div>
                <div className="font-mono font-bold text-xl">
                  €{extractedData.total_cost.toFixed(2)}
                </div>
              </div>
              <div className="col-span-2">
                <div className="opacity-60 mb-2">ORDER LINES ({extractedData.order_lines.length})</div>
                <div className="space-y-1">
                  {extractedData.order_lines.map((line, idx) => (
                    <div key={idx} className="text-xs">
                      {line.position_description} - €{line.total_price.toFixed(2)}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Requests Table */}
        <div>
          <h2 className="text-2xl font-bold mb-3">
            REQUESTS ({loading ? '...' : requests.length})
          </h2>

          {loading ? (
            <div className="border-3 border-black p-12 text-center text-2xl">
              LOADING...
            </div>
          ) : (
            <RequestsKanban
              requests={requests}
              onRequestClick={setSelectedRequest}
              onRequestsChange={loadRequests}
              commodityGroups={commodityGroups}
            />
          )}
        </div>
      </div>

      {/* Request Detail Modal */}
      {selectedRequest && (
        <RequestDetail
          request={selectedRequest}
          onClose={() => setSelectedRequest(null)}
          commodityGroups={commodityGroups}
        />
      )}
    </div>
  );
}
