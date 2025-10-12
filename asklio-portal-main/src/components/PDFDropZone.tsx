import { useCallback, useState } from 'react';
import { Upload, FileText, X } from 'lucide-react';
import { ExtractedData } from '@/types/request';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface PDFDropZoneProps {
  onExtract: (data: ExtractedData) => void;
}

export const PDFDropZone = ({ onExtract }: PDFDropZoneProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const { toast } = useToast();

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const processFile = async (file: File) => {
    if (!file.name.endsWith('.pdf')) {
      toast({
        title: 'Invalid file',
        description: 'Only PDF files are allowed',
        variant: 'destructive',
      });
      return;
    }

    setIsProcessing(true);
    setFileName(file.name);

    try {
      const result = await api.uploadPDF(file);
      onExtract(result.extracted_data);
      toast({
        title: 'PDF processed',
        description: 'Data extracted successfully',
      });
    } catch (error) {
      toast({
        title: 'Processing failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        processFile(files[0]);
      }
    },
    []
  );

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      processFile(files[0]);
    }
  };

  const clearFile = () => {
    setFileName(null);
  };

  return (
    <div
      className={`relative border-heavy p-8 transition-colors ${
        isDragging ? 'bg-accent' : 'bg-card'
      } ${isProcessing ? 'opacity-50 pointer-events-none' : ''}`}
      onDragEnter={handleDragIn}
      onDragLeave={handleDragOut}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <input
        type="file"
        accept=".pdf"
        onChange={handleFileInput}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        disabled={isProcessing}
      />

      <div className="flex flex-col items-center justify-center gap-4 pointer-events-none">
        {fileName ? (
          <>
            <FileText className="w-12 h-12" />
            <div className="flex items-center gap-2">
              <span className="mono text-sm font-bold">{fileName}</span>
              {!isProcessing && (
                <button
                  onClick={clearFile}
                  className="pointer-events-auto hover:bg-muted p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            {isProcessing && <span className="text-sm font-bold">PROCESSING...</span>}
          </>
        ) : (
          <>
            <Upload className="w-12 h-12" />
            <div className="text-center">
              <p className="font-bold text-lg">DROP PDF HERE</p>
              <p className="text-sm mono mt-1">OR CLICK TO BROWSE</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
