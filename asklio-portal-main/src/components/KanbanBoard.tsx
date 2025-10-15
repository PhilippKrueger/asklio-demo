import { useState } from 'react';
import { Request } from '@/types/request';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { getCurrencySymbol } from '@/lib/currency';
import { RequestDetailsDialog } from './RequestDetailsDialog';

interface KanbanBoardProps {
  requests: Request[];
  onUpdate: () => void;
}

const statusLabels = {
  open: 'OPEN',
  in_progress: 'IN PROGRESS',
  closed: 'CLOSED',
};

const statusColors = {
  open: 'bg-status-open',
  in_progress: 'bg-status-progress',
  closed: 'bg-status-closed',
};

export const KanbanBoard = ({ requests, onUpdate }: KanbanBoardProps) => {
  const { toast } = useToast();
  const [draggedRequestId, setDraggedRequestId] = useState<number | null>(null);
  const [dragOverStatus, setDragOverStatus] = useState<string | null>(null);
  const [selectedRequest, setSelectedRequest] = useState<Request | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  // Normalize status to lowercase with underscores for comparison
  const normalizeStatus = (status: string) => {
    return status.toLowerCase().replace(/ /g, '_');
  };

  const requestsByStatus = {
    open: requests.filter((r) => normalizeStatus(r.status) === 'open'),
    in_progress: requests.filter((r) => normalizeStatus(r.status) === 'in_progress'),
    closed: requests.filter((r) => normalizeStatus(r.status) === 'closed'),
  };

  // Convert frontend status format to backend format
  const toBackendStatus = (status: string) => {
    const statusMap: Record<string, string> = {
      'open': 'Open',
      'in_progress': 'In Progress',
      'closed': 'Closed',
    };
    return statusMap[status] || status;
  };

  const handleStatusChange = async (id: number, newStatus: string) => {
    try {
      await api.updateStatus(id, toBackendStatus(newStatus));
      toast({
        title: 'Status updated',
        description: 'Request status changed successfully',
      });
      onUpdate();
    } catch (error) {
      toast({
        title: 'Update failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  };

  // Drag and drop handlers
  const handleDragStart = (e: React.DragEvent, requestId: number) => {
    // Only allow drag if it's not a quick click
    setDraggedRequestId(requestId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleClick = (e: React.MouseEvent, request: Request) => {
    e.preventDefault();
    e.stopPropagation();
    handleRequestClick(request);
  };


  const handleDragEnd = () => {
    setDraggedRequestId(null);
    setDragOverStatus(null);
  };

  const handleRequestClick = (request: Request) => {
    setSelectedRequest(request);
    setIsDetailsOpen(true);
  };

  const handleCloseDetails = () => {
    setIsDetailsOpen(false);
    setSelectedRequest(null);
    onUpdate();
  };

  const handleDragOver = (e: React.DragEvent, status: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverStatus(status);
  };

  const handleDragLeave = () => {
    setDragOverStatus(null);
  };

  const handleDrop = async (e: React.DragEvent, newStatus: string) => {
    e.preventDefault();
    setDragOverStatus(null);

    if (draggedRequestId === null) return;

    const request = requests.find((r) => r.id === draggedRequestId);
    if (!request) return;

    const currentStatus = normalizeStatus(request.status);
    if (currentStatus === newStatus) return;

    await handleStatusChange(draggedRequestId, newStatus);
    setDraggedRequestId(null);
  };

  return (
    <div className="grid grid-cols-3 gap-4">
      {(['open', 'in_progress', 'closed'] as const).map((status) => (
        <div key={status} className="border-heavy">
          <div className={`${statusColors[status]} p-3 border-b-2 border-black`}>
            <h2 className="font-bold text-lg text-black">{statusLabels[status]}</h2>
            <span className="mono text-sm text-black">
              {requestsByStatus[status].length} REQUESTS
            </span>
          </div>

          <div
            className={`p-3 space-y-3 min-h-[400px] transition-colors ${
              dragOverStatus === status ? 'bg-accent/20' : ''
            }`}
            onDragOver={(e) => handleDragOver(e, status)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, status)}
          >
            {requestsByStatus[status].map((request) => (
              <div
                key={request.id}
                draggable
                onDragStart={(e) => handleDragStart(e, request.id)}
                onDragEnd={handleDragEnd}
                onClick={(e) => handleClick(e, request)}
                className={`border-heavy bg-card p-3 shadow-brutal hover:shadow-brutal-lg transition-all cursor-pointer ${
                  draggedRequestId === request.id ? 'opacity-50' : ''
                }`}
                title="Click to view details, drag to move"
              >
                <div className="mb-2">
                  <div className="flex justify-between items-start mb-1">
                    <h3 className="font-bold text-sm">{request.title}</h3>
                    <span className="mono text-xs">#{request.id}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{request.vendor_name}</p>
                  {request.commodity_group && (
                    <div className="mt-1">
                      <span className="inline-block bg-secondary text-xs px-2 py-1 border border-black font-mono">
                        {request.commodity_group}
                      </span>
                    </div>
                  )}
                </div>

                <div className="space-y-1 text-xs mono">
                  <div className="flex justify-between">
                    <span>Requestor:</span>
                    <span className="font-bold">{request.requestor_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Department:</span>
                    <span className="font-bold">{request.department || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Items:</span>
                    <span className="font-bold">{request.order_lines?.length || 0}</span>
                  </div>
                  <div className="flex justify-between border-t-2 border-black pt-1 mt-1">
                    <span>Total:</span>
                    <span className="font-bold">{getCurrencySymbol(request.currency)}{request.total_cost.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      
      <RequestDetailsDialog
        request={selectedRequest}
        isOpen={isDetailsOpen}
        onClose={handleCloseDetails}
        onUpdate={onUpdate}
      />
    </div>
  );
};
