import { useState, useEffect } from 'react';
import { Plus, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { KanbanBoard } from '@/components/KanbanBoard';
import { CreateRequestDialog } from '@/components/CreateRequestDialog';
import { Request } from '@/types/request';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

const Index = () => {
  const [requests, setRequests] = useState<Request[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const { toast } = useToast();

  const fetchRequests = async () => {
    setIsLoading(true);
    try {
      const data = await api.getRequests();
      setRequests(data);
    } catch (error) {
      toast({
        title: 'Failed to load requests',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  const handleSuccess = () => {
    fetchRequests();
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b-4 border-black bg-background sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="font-bold text-3xl">PROCUREMENT</h1>
              <p className="mono text-sm">REQUEST MANAGEMENT SYSTEM</p>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={fetchRequests}
                variant="outline"
                className="border-heavy"
                disabled={isLoading}
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                REFRESH
              </Button>
              <Button
                onClick={() => setIsDialogOpen(true)}
                className="border-ultra bg-accent text-accent-foreground hover:bg-accent/80 shadow-brutal font-bold"
              >
                <Plus className="w-4 h-4 mr-2" />
                NEW REQUEST
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block border-4 border-black border-t-accent w-12 h-12 rounded-full animate-spin"></div>
            <p className="mt-4 font-bold">LOADING...</p>
          </div>
        ) : (
          <KanbanBoard requests={requests} onUpdate={handleSuccess} />
        )}
      </main>

      <CreateRequestDialog
        isOpen={isDialogOpen}
        onClose={() => setIsDialogOpen(false)}
        onSuccess={handleSuccess}
      />
    </div>
  );
};

export default Index;
