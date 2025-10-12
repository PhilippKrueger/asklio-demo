// Giant brutalist PDF upload drag-and-drop zone

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadPDF } from '../api';
import type { ExtractedData } from '../types';

interface PDFUploadProps {
  onDataExtracted: (data: ExtractedData) => void;
}

export default function PDFUpload({ onDataExtracted }: PDFUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const response = await uploadPDF(file);
      onDataExtracted(response.extracted_data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  }, [onDataExtracted]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div
      {...getRootProps()}
      className={`
        border-4 border-black border-dashed
        w-full h-full
        flex flex-col items-center justify-center
        cursor-pointer
        transition-colors duration-100
        ${isDragActive ? 'bg-black text-white' : 'bg-white text-black'}
        ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <input {...getInputProps()} />

      <div className="text-center">
        {uploading ? (
          <>
            <div className="text-4xl mb-4">PROCESSING...</div>
            <div className="text-sm">EXTRACTING DATA FROM PDF</div>
          </>
        ) : isDragActive ? (
          <>
            <div className="text-6xl mb-4">↓</div>
            <div className="text-4xl font-bold">DROP HERE</div>
          </>
        ) : (
          <>
            <div className="text-6xl mb-4">[ PDF ]</div>
            <div className="text-4xl font-bold mb-2">DROP PDF HERE</div>
            <div className="text-sm">OR CLICK TO SELECT FILE</div>
            <div className="text-xs mt-4 opacity-60">MAX 10MB</div>
          </>
        )}
      </div>

      {error && (
        <div className="mt-4 border-2 border-black bg-white text-black px-4 py-2 text-sm">
          ERROR: {error}
        </div>
      )}
    </div>
  );
}
