// Brutal table with TanStack Table - raw HTML aesthetic

import { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table';
import type { Request } from '../types';
import { updateRequestStatus } from '../api';

interface RequestsTableProps {
  requests: Request[];
  onRequestClick: (request: Request) => void;
  onRequestsChange: () => void;
}

export default function RequestsTable({
  requests,
  onRequestClick,
  onRequestsChange,
}: RequestsTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const handleStatusChange = async (requestId: number, newStatus: string) => {
    try {
      await updateRequestStatus(requestId, newStatus as any);
      onRequestsChange();
    } catch (error) {
      console.error('Failed to update status:', error);
    }
  };

  const columns = useMemo<ColumnDef<Request>[]>(
    () => [
      {
        accessorKey: 'id',
        header: 'ID',
        cell: (info) => <span className="font-mono">{info.getValue() as number}</span>,
      },
      {
        accessorKey: 'title',
        header: 'TITLE',
        cell: (info) => <span className="font-bold">{info.getValue() as string}</span>,
      },
      {
        accessorKey: 'vendor_name',
        header: 'VENDOR',
      },
      {
        accessorKey: 'total_cost',
        header: 'COST',
        cell: (info) => (
          <span className="font-mono">€{(info.getValue() as number).toFixed(2)}</span>
        ),
      },
      {
        accessorKey: 'status',
        header: 'STATUS',
        cell: (info) => {
          const row = info.row.original;
          return (
            <select
              value={row.status}
              onChange={(e) => handleStatusChange(row.id, e.target.value)}
              className="border-2 border-black px-2 py-1 bg-white cursor-pointer hover:bg-black hover:text-white transition-colors duration-100"
              onClick={(e) => e.stopPropagation()}
            >
              <option value="Open">OPEN</option>
              <option value="In Progress">IN PROGRESS</option>
              <option value="Closed">CLOSED</option>
            </select>
          );
        },
      },
      {
        accessorKey: 'commodity_group_confidence',
        header: 'CONF',
        cell: (info) => {
          const confidence = info.getValue() as number | null;
          if (confidence === null) return <span className="opacity-30">-</span>;
          return (
            <span className="font-mono" title={`Confidence: ${confidence.toFixed(2)}`}>
              {(confidence * 100).toFixed(0)}%
            </span>
          );
        },
      },
      {
        accessorKey: 'created_at',
        header: 'CREATED',
        cell: (info) => {
          const date = new Date(info.getValue() as string);
          return (
            <span className="font-mono text-sm">
              {date.toLocaleDateString('en-GB')}
            </span>
          );
        },
      },
    ],
    []
  );

  const table = useReactTable({
    data: requests,
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="border-3 border-black overflow-auto">
      <table className="w-full border-collapse">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id} className="border-b-3 border-black">
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="border-r-3 border-black last:border-r-0 p-3 text-left bg-black text-white cursor-pointer select-none"
                  onClick={header.column.getToggleSortingHandler()}
                >
                  <div className="flex items-center gap-2">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {header.column.getIsSorted() && (
                      <span>
                        {header.column.getIsSorted() === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              onClick={() => onRequestClick(row.original)}
              className="border-b-3 border-black last:border-b-0 cursor-pointer hover:bg-black hover:text-white transition-colors duration-100"
            >
              {row.getVisibleCells().map((cell) => (
                <td
                  key={cell.id}
                  className="border-r-3 border-black last:border-r-0 p-3"
                >
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {requests.length === 0 && (
        <div className="p-8 text-center text-2xl opacity-30">
          NO REQUESTS
        </div>
      )}
    </div>
  );
}
