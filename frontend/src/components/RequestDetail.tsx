// Request detail view with confidence visualization

import { useState } from 'react';
import type { Request } from '../types';

interface RequestDetailProps {
  request: Request;
  onClose: () => void;
  commodityGroups: Map<number, string>;
}

export default function RequestDetail({ request, onClose, commodityGroups }: RequestDetailProps) {
  const [showConfidence, setShowConfidence] = useState(false);

  const getConfidenceBarWidth = (confidence: number | null) => {
    if (confidence === null) return 0;
    return Math.round(confidence * 100);
  };

  const getConfidenceColor = (confidence: number | null) => {
    if (confidence === null) return 'bg-gray-400';
    const percent = confidence * 100;
    if (percent >= 90) return 'bg-green-700';
    if (percent >= 80) return 'bg-green-600';
    if (percent >= 70) return 'bg-green-500';
    if (percent >= 60) return 'bg-lime-600';
    if (percent >= 50) return 'bg-yellow-400';
    if (percent >= 40) return 'bg-yellow-500';
    if (percent >= 30) return 'bg-yellow-600';
    return 'bg-gray-500';
  };

  return (
    <div className="fixed inset-0 bg-white z-50 overflow-auto">
      {/* Header */}
      <div className="border-b-3 border-black p-6 flex justify-between items-center bg-black text-white sticky top-0">
        <div>
          <div className="text-sm opacity-60 mb-1">REQUEST #{request.id}</div>
          <h1 className="text-3xl font-bold">{request.title}</h1>
        </div>
        <button
          onClick={onClose}
          className="text-4xl hover:opacity-60 transition-opacity duration-100"
        >
          ×
        </button>
      </div>

      <div className="max-w-6xl mx-auto p-6 space-y-6">
        {/* Vendor Info */}
        <div className="border-3 border-black p-6">
          <h2 className="text-xl font-bold mb-4">VENDOR INFORMATION</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm opacity-60">VENDOR NAME</div>
              <div className="text-xl font-bold">{request.vendor_name}</div>
            </div>
            <div>
              <div className="text-sm opacity-60">VAT ID</div>
              <div className="text-xl font-mono">
                {request.vat_id || <span className="opacity-30">N/A</span>}
              </div>
            </div>
            <div>
              <div className="text-sm opacity-60">DEPARTMENT</div>
              <div className="text-xl">
                {request.department || <span className="opacity-30">N/A</span>}
              </div>
            </div>
            <div>
              <div className="text-sm opacity-60">REQUESTOR</div>
              <div className="text-xl">{request.requestor_name}</div>
            </div>
          </div>
        </div>

        {/* Commodity Group with Confidence */}
        {request.commodity_group_id && (
          <div
            className="border-3 border-black p-6 cursor-pointer"
            onClick={() => setShowConfidence(!showConfidence)}
          >
            <h2 className="text-xl font-bold mb-4">
              COMMODITY GROUP
              <span className="text-sm ml-2 opacity-60">
                (CLICK TO SHOW CONFIDENCE)
              </span>
            </h2>
            <div className="text-2xl font-bold mb-2">
              {commodityGroups.get(request.commodity_group_id) || 'Unknown'}
            </div>
            <div className="text-sm opacity-60">ID: {request.commodity_group_id}</div>

            {showConfidence && request.commodity_group_confidence !== null && (
              <div className="mt-4 pt-4 border-t-2 border-black">
                <div className="text-sm mb-2">
                  CONFIDENCE: {(request.commodity_group_confidence * 100).toFixed(0)}%
                </div>
                <div className="h-8 border-2 border-black flex">
                  <div
                    className={`${getConfidenceColor(
                      request.commodity_group_confidence
                    )} transition-all duration-100`}
                    style={{
                      width: `${getConfidenceBarWidth(request.commodity_group_confidence)}%`,
                    }}
                  />
                  <div className="flex-1 bg-gray-200" />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Order Lines */}
        <div className="border-3 border-black">
          <div className="p-6 border-b-3 border-black bg-black text-white">
            <h2 className="text-xl font-bold">ORDER LINES</h2>
          </div>
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b-3 border-black">
                <th className="p-3 text-left border-r-3 border-black">#</th>
                <th className="p-3 text-left border-r-3 border-black">DESCRIPTION</th>
                <th className="p-3 text-right border-r-3 border-black">UNIT PRICE</th>
                <th className="p-3 text-right border-r-3 border-black">AMOUNT</th>
                <th className="p-3 text-left border-r-3 border-black">UNIT</th>
                <th className="p-3 text-right">TOTAL</th>
              </tr>
            </thead>
            <tbody>
              {request.order_lines.map((line, idx) => (
                <tr key={line.id || idx} className="border-b-3 border-black last:border-b-0">
                  <td className="p-3 font-mono border-r-3 border-black">{idx + 1}</td>
                  <td className="p-3 border-r-3 border-black">{line.position_description}</td>
                  <td className="p-3 text-right font-mono border-r-3 border-black">
                    €{line.unit_price.toFixed(2)}
                  </td>
                  <td className="p-3 text-right font-mono border-r-3 border-black">
                    {line.amount}
                  </td>
                  <td className="p-3 border-r-3 border-black">{line.unit}</td>
                  <td className="p-3 text-right font-mono font-bold">
                    €{line.total_price.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t-4 border-black bg-black text-white">
                <td colSpan={5} className="p-3 text-right font-bold">
                  TOTAL COST
                </td>
                <td className="p-3 text-right font-mono text-2xl font-bold">
                  €{request.total_cost.toFixed(2)}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        {/* Metadata */}
        <div className="border-3 border-black p-6">
          <h2 className="text-xl font-bold mb-4">METADATA</h2>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <div className="opacity-60">STATUS</div>
              <div className="font-bold">{request.status}</div>
            </div>
            <div>
              <div className="opacity-60">CREATED</div>
              <div className="font-mono">{new Date(request.created_at).toLocaleString()}</div>
            </div>
            <div>
              <div className="opacity-60">UPDATED</div>
              <div className="font-mono">{new Date(request.updated_at).toLocaleString()}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
