// Brutal Kanban board with drag-and-drop

import { useState, useRef } from 'react';
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCenter,
  useDroppable,
  useDraggable,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core';
import type { Request } from '../types';
import { updateRequestStatus } from '../api';

interface RequestsKanbanProps {
  requests: Request[];
  onRequestClick: (request: Request) => void;
  onRequestsChange: () => void;
  commodityGroups: Map<number, string>;
}

type Status = 'Open' | 'In Progress' | 'Closed';

const COLUMNS: { id: Status; title: string }[] = [
  { id: 'Open', title: 'OPEN' },
  { id: 'In Progress', title: 'IN PROGRESS' },
  { id: 'Closed', title: 'CLOSED' },
];

function RequestCard({
  request,
  onClick,
  isDraggingAny,
  commodityGroupName,
}: {
  request: Request;
  onClick: () => void;
  isDraggingAny: boolean;
  commodityGroupName?: string;
}) {
  const {
    attributes,
    listeners,
    setNodeRef: setDraggableRef,
    transform,
    isDragging,
  } = useDraggable({ id: request.id });

  const { setNodeRef: setDroppableRef } = useDroppable({ id: request.id });

  const setNodeRef = (node: HTMLElement | null) => {
    setDraggableRef(node);
    setDroppableRef(node);
  };

  const style = transform ? {
    transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
  } : undefined;

  const handleClick = (e: React.MouseEvent) => {
    // Prevent click if we're dragging or just finished dragging
    if (isDragging || isDraggingAny) {
      e.stopPropagation();
      e.preventDefault();
      return;
    }
    onClick();
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={handleClick}
      className={`border-3 border-black bg-white p-3 mb-3 cursor-pointer hover:bg-black hover:text-white transition-colors duration-100 select-none ${
        isDragging ? 'opacity-50' : ''
      }`}
    >
      <div className="flex items-start justify-between mb-2">
        <span className="font-mono text-sm opacity-60">#{request.id}</span>
        {request.commodity_group_confidence !== null && (
          <span className="font-mono text-xs border-2 border-current px-2 py-0.5">
            {(request.commodity_group_confidence * 100).toFixed(0)}%
          </span>
        )}
      </div>

      <div className="font-bold text-lg mb-2 leading-tight">{request.title}</div>

      <div className="text-sm space-y-1">
        <div className="opacity-70">{request.vendor_name}</div>
        {commodityGroupName && (
          <div className="text-xs border-2 border-black px-2 py-1 inline-block">
            {commodityGroupName}
          </div>
        )}
        <div className="font-mono font-bold">€{request.total_cost.toFixed(2)}</div>
        <div className="font-mono text-xs opacity-50">
          {new Date(request.created_at).toLocaleDateString('en-GB')}
        </div>
      </div>
    </div>
  );
}

function KanbanColumn({
  status,
  title,
  requests,
  onRequestClick,
  isDraggingAny,
  commodityGroups,
}: {
  status: Status;
  title: string;
  requests: Request[];
  onRequestClick: (request: Request) => void;
  isDraggingAny: boolean;
  commodityGroups: Map<number, string>;
}) {
  const { setNodeRef, isOver } = useDroppable({
    id: status,
  });

  return (
    <div className="border-3 border-black flex flex-col">
      <div className="bg-black text-white p-4 border-b-3 border-black">
        <div className="text-xl font-bold">{title}</div>
        <div className="text-sm opacity-60">{requests.length} ITEMS</div>
      </div>

      <div
        ref={setNodeRef}
        className={`p-4 flex-1 overflow-y-auto min-h-[400px] transition-colors duration-200 ${
          isOver ? 'bg-yellow-50' : ''
        }`}
      >
        {requests.length === 0 ? (
          <div className="text-center text-xl opacity-30 mt-12">
            NO ITEMS
          </div>
        ) : (
          requests.map((request) => (
            <RequestCard
              key={request.id}
              request={request}
              onClick={() => onRequestClick(request)}
              isDraggingAny={isDraggingAny}
              commodityGroupName={
                request.commodity_group_id
                  ? commodityGroups.get(request.commodity_group_id)
                  : undefined
              }
            />
          ))
        )}
      </div>
    </div>
  );
}

export default function RequestsKanban({
  requests,
  onRequestClick,
  onRequestsChange,
  commodityGroups,
}: RequestsKanbanProps) {
  const [activeRequest, setActiveRequest] = useState<Request | null>(null);
  const [isDraggingAny, setIsDraggingAny] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

  const handleDragStart = (event: DragStartEvent) => {
    const request = requests.find((r) => r.id === event.active.id);
    setActiveRequest(request || null);
    setIsDraggingAny(true);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveRequest(null);

    // Reset dragging state after a short delay to prevent click events
    setTimeout(() => setIsDraggingAny(false), 100);

    if (!over) return;

    const requestId = active.id as number;

    // Check if over.id is a status (column) or a request ID
    const validStatuses: Status[] = ['Open', 'In Progress', 'Closed'];
    let newStatus: Status | undefined;

    if (validStatuses.includes(over.id as Status)) {
      // Dropped directly on a column
      newStatus = over.id as Status;
    } else {
      // Dropped on a card - find which column that card is in
      const targetRequest = requests.find((r) => r.id === over.id);
      if (targetRequest) {
        newStatus = targetRequest.status;
      }
    }

    if (!newStatus) return;

    const request = requests.find((r) => r.id === requestId);
    if (!request || request.status === newStatus) return;

    try {
      await updateRequestStatus(requestId, newStatus);
      onRequestsChange();
    } catch (error) {
      console.error('Failed to update status:', error);
    }
  };

  const getRequestsByStatus = (status: Status) => {
    return requests.filter((r) => r.status === status);
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="grid grid-cols-3 gap-6">
        {COLUMNS.map((column) => (
          <KanbanColumn
            key={column.id}
            status={column.id}
            title={column.title}
            requests={getRequestsByStatus(column.id)}
            onRequestClick={onRequestClick}
            isDraggingAny={isDraggingAny}
            commodityGroups={commodityGroups}
          />
        ))}
      </div>

      <DragOverlay>
        {activeRequest ? (
          <div className="border-3 border-black bg-white p-3 shadow-lg rotate-3 scale-105">
            <div className="flex items-start justify-between mb-2">
              <span className="font-mono text-sm opacity-60">#{activeRequest.id}</span>
              {activeRequest.commodity_group_confidence !== null && (
                <span className="font-mono text-xs border-2 border-current px-2 py-0.5">
                  {(activeRequest.commodity_group_confidence * 100).toFixed(0)}%
                </span>
              )}
            </div>
            <div className="font-bold text-lg mb-2 leading-tight">{activeRequest.title}</div>
            <div className="text-sm space-y-1">
              <div className="opacity-70">{activeRequest.vendor_name}</div>
              {activeRequest.commodity_group_id && commodityGroups.get(activeRequest.commodity_group_id) && (
                <div className="text-xs border-2 border-black px-2 py-1 inline-block">
                  {commodityGroups.get(activeRequest.commodity_group_id)}
                </div>
              )}
              <div className="font-mono font-bold">€{activeRequest.total_cost.toFixed(2)}</div>
            </div>
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
