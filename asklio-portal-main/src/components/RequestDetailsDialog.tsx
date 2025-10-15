import { useState } from 'react';
import { Trash2 } from 'lucide-react';
import { Request } from '@/types/request';
import { 
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { RequestForm } from './RequestForm';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import { getCurrencySymbol } from '@/lib/currency';

interface RequestDetailsDialogProps {
  request: Request | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdate?: () => void;
}

export const RequestDetailsDialog = ({ request, isOpen, onClose, onUpdate }: RequestDetailsDialogProps) => {
  const { toast } = useToast();
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  if (!request) return null;

  const handleDelete = async () => {
    if (!request) return;
    
    setIsDeleting(true);
    try {
      await api.deleteRequest(request.id);
      toast({
        title: 'Request deleted',
        description: 'Request has been permanently deleted',
      });
      onClose();
      onUpdate?.();
    } catch (error) {
      toast({
        title: 'Delete failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setIsDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const handleSuccess = () => {
    onClose();
    onUpdate?.();
  };

  return (
    <>
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto border-heavy">
          <DialogHeader>
            <DialogTitle className="font-bold text-xl">
              REQUEST #{request.id} - {request.title}
            </DialogTitle>
          </DialogHeader>
          
          <RequestForm 
            existingRequest={request}
            mode="view"
            onSuccess={handleSuccess}
            onDelete={() => setShowDeleteConfirm(true)}
          />
        </DialogContent>
      </Dialog>

      <Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <DialogContent className="border-heavy">
          <DialogHeader>
            <DialogTitle className="font-bold text-lg">
              DELETE REQUEST #{request.id}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <p>Are you sure you want to permanently delete this request?</p>
            <p className="text-sm text-muted-foreground">
              <strong>Title:</strong> {request.title}<br />
              <strong>Vendor:</strong> {request.vendor_name}<br />
              <strong>Total:</strong> {getCurrencySymbol(request.currency)}{request.total_cost.toFixed(2)}
            </p>
            <p className="text-sm font-bold text-destructive">
              This action cannot be undone.
            </p>
            
            <div className="flex gap-3 justify-end">
              <Button
                onClick={() => setShowDeleteConfirm(false)}
                variant="outline"
                className="border-heavy"
              >
                CANCEL
              </Button>
              <Button
                onClick={handleDelete}
                disabled={isDeleting}
                variant="destructive"
                className="border-heavy"
              >
                {isDeleting ? 'DELETING...' : 'DELETE PERMANENTLY'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};