import { useState } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { PDFDropZone } from './PDFDropZone';
import { RequestForm } from './RequestForm';
import { ExtractedData } from '@/types/request';

interface CreateRequestDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const CreateRequestDialog = ({ isOpen, onClose, onSuccess }: CreateRequestDialogProps) => {
  const [extractedData, setExtractedData] = useState<ExtractedData | undefined>();
  const [pdfFile, setPdfFile] = useState<File | undefined>();
  const [showForm, setShowForm] = useState(false);

  if (!isOpen) return null;

  const handleExtract = (data: ExtractedData, file: File) => {
    setExtractedData(data);
    setPdfFile(file);
    setShowForm(true);
  };

  const handleSuccess = () => {
    onSuccess();
    onClose();
    resetDialog();
  };

  const resetDialog = () => {
    setExtractedData(undefined);
    setPdfFile(undefined);
    setShowForm(false);
  };

  const handleClose = () => {
    onClose();
    resetDialog();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-background border-ultra shadow-brutal-lg max-w-4xl w-full max-h-[90vh] overflow-auto">
        <div className="border-b-4 border-black p-4 flex justify-between items-center sticky top-0 bg-background">
          <h2 className="font-bold text-2xl">CREATE NEW REQUEST</h2>
          <Button onClick={handleClose} variant="ghost" size="sm">
            <X className="w-6 h-6" />
          </Button>
        </div>

        <div className="p-6 space-y-6">
          {!showForm && (
            <>
              <div>
                <h3 className="font-bold text-lg mb-2">UPLOAD VENDOR OFFER (PDF)</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Automatically extract request details from PDF
                </p>
                <PDFDropZone onExtract={handleExtract} />
              </div>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t-2 border-black"></div>
                </div>
                <div className="relative flex justify-center">
                  <span className="bg-background px-4 font-bold">OR</span>
                </div>
              </div>

              <Button
                onClick={() => setShowForm(true)}
                variant="outline"
                className="w-full border-heavy h-12 font-bold"
              >
                ENTER MANUALLY
              </Button>
            </>
          )}

          {showForm && <RequestForm extractedData={extractedData} pdfFile={pdfFile} onSuccess={handleSuccess} />}
        </div>
      </div>
    </div>
  );
};
