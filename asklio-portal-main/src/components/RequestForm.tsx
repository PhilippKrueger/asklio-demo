import { useState, useEffect } from 'react';
import { Plus, Trash2, Trash } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RequestCreate, RequestUpdate, OrderLine, ExtractedData, Request, CommodityGroup } from '@/types/request';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/lib/api';
import { getCurrencySymbol } from '@/lib/currency';

interface RequestFormProps {
  extractedData?: ExtractedData;
  existingRequest?: Request;
  mode?: 'create' | 'view';
  onSuccess?: () => void;
  onDelete?: () => void;
}

export const RequestForm = ({ extractedData, existingRequest, mode = 'create', onSuccess, onDelete }: RequestFormProps) => {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [commodityGroups, setCommodityGroups] = useState<CommodityGroup[]>([]);
  const [isLoadingGroups, setIsLoadingGroups] = useState(true);
  const isViewMode = mode === 'view';
  const isEditingExisting = Boolean(existingRequest);

  const [formData, setFormData] = useState<RequestCreate>(() => {
    if (existingRequest) {
      return {
        requestor_name: existingRequest.requestor_name,
        title: existingRequest.title,
        vendor_name: existingRequest.vendor_name,
        vat_id: existingRequest.vat_id || '',
        department: existingRequest.department || '',
        total_cost: existingRequest.total_cost,
        order_lines: existingRequest.order_lines?.length > 0 
          ? existingRequest.order_lines 
          : [{ position_description: '', unit_price: 0, amount: 0, unit: '', total_price: 0 }],
        commodity_group_id: existingRequest.commodity_group_id,
      };
    }
    
    return {
      requestor_name: extractedData?.vendor_name || '',
      title: '',
      vendor_name: extractedData?.vendor_name || '',
      vat_id: extractedData?.vat_id || '',
      department: extractedData?.requestor_department || '',
      total_cost: extractedData?.total_cost || 0,
      order_lines: extractedData?.order_lines || [
        { position_description: '', unit_price: 0, amount: 0, unit: '', total_price: 0 },
      ],
      commodity_group_id: extractedData?.commodity_group,
    };
  });
  
  const currentCurrency = existingRequest?.currency || extractedData?.currency;

  useEffect(() => {
    const fetchCommodityGroups = async () => {
      try {
        const groups = await api.getCommodityGroups();
        setCommodityGroups(groups);
      } catch (error) {
        console.error('Failed to fetch commodity groups:', error);
        toast({
          title: 'Failed to load commodity groups',
          description: 'Using form without commodity group options',
          variant: 'destructive',
        });
      } finally {
        setIsLoadingGroups(false);
      }
    };

    fetchCommodityGroups();
  }, [toast]);

  const updateField = (field: keyof RequestCreate, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const addOrderLine = () => {
    setFormData((prev) => ({
      ...prev,
      order_lines: [
        ...prev.order_lines,
        { position_description: '', unit_price: 0, amount: 0, unit: '', total_price: 0 },
      ],
    }));
  };

  const removeOrderLine = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      order_lines: prev.order_lines.filter((_, i) => i !== index),
    }));
  };

  const updateOrderLine = (index: number, field: keyof OrderLine, value: any) => {
    setFormData((prev) => {
      const newLines = [...prev.order_lines];
      newLines[index] = { ...newLines[index], [field]: value };
      
      // Auto-calculate total price
      if (field === 'unit_price' || field === 'amount') {
        const line = newLines[index];
        line.total_price = line.unit_price * line.amount;
      }

      return { ...prev, order_lines: newLines };
    });
  };

  const calculateTotal = () => {
    return formData.order_lines.reduce((sum, line) => sum + line.total_price, 0);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    
    const total = calculateTotal();
    const dataToSubmit = { ...formData, total_cost: total };

    setIsSubmitting(true);
    try {
      if (isEditingExisting && existingRequest?.id) {
        await api.updateRequest(existingRequest.id, dataToSubmit);
        toast({
          title: 'Request updated',
          description: 'Procurement request saved successfully',
        });
      } else {
        await api.createRequest(dataToSubmit);
        toast({
          title: 'Request created',
          description: 'Procurement request submitted successfully',
        });
      }
      onSuccess?.();
    } catch (error) {
      toast({
        title: isEditingExisting ? 'Update failed' : 'Submission failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label className="font-bold text-sm mb-2 block">REQUESTOR NAME</Label>
          <Input
            required
            value={formData.requestor_name}
            onChange={(e) => updateField('requestor_name', e.target.value)}
            className="border-heavy"
          />
        </div>
        <div>
          <Label className="font-bold text-sm mb-2 block">DEPARTMENT</Label>
          <Input
            required
            value={formData.department}
            onChange={(e) => updateField('department', e.target.value)}
            className="border-heavy"
          />
        </div>
      </div>

      <div>
        <Label className="font-bold text-sm mb-2 block">TITLE / SHORT DESCRIPTION</Label>
        <Input
          required
          value={formData.title}
          onChange={(e) => updateField('title', e.target.value)}
          className="border-heavy"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label className="font-bold text-sm mb-2 block">VENDOR NAME</Label>
          <Input
            required
            value={formData.vendor_name}
            onChange={(e) => updateField('vendor_name', e.target.value)}
            className="border-heavy"
          />
        </div>
        <div>
          <Label className="font-bold text-sm mb-2 block">VAT ID</Label>
          <Input
            required
            value={formData.vat_id}
            onChange={(e) => updateField('vat_id', e.target.value)}
            className="border-heavy mono"
          />
        </div>
      </div>

      <div>
        <Label className="font-bold text-sm mb-2 block">COMMODITY GROUP</Label>
        <Select
          value={formData.commodity_group_id?.toString() || '0'}
          onValueChange={(value) => updateField('commodity_group_id', value && value !== "0" ? parseInt(value) : undefined)}
          disabled={isLoadingGroups}
        >
          <SelectTrigger className="border-heavy">
            <SelectValue placeholder={isLoadingGroups ? "Loading..." : "Select commodity group"} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="0">No commodity group</SelectItem>
            {commodityGroups && commodityGroups.length > 0 && commodityGroups.map((group) => (
              <SelectItem key={group.id} value={group.id.toString()}>
                {group.category} - {group.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="border-heavy p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-bold text-lg">ORDER LINES</h3>
          <Button type="button" onClick={addOrderLine} variant="outline" size="sm" className="border-heavy">
            <Plus className="w-4 h-4 mr-2" />
            ADD LINE
          </Button>
        </div>

        <div className="space-y-4">
          {formData.order_lines.map((line, index) => (
            <div key={index} className="border-heavy p-3 space-y-3">
              <div className="flex justify-between items-start">
                <span className="mono font-bold text-sm">LINE {index + 1}</span>
                {formData.order_lines.length > 1 && (
                  <Button
                    type="button"
                    onClick={() => removeOrderLine(index)}
                    variant="ghost"
                    size="sm"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                )}
              </div>

              <Input
                required
                placeholder="Position Description"
                value={line.position_description}
                onChange={(e) => updateOrderLine(index, 'position_description', e.target.value)}
                className="border-heavy"
              />

              <div className="grid grid-cols-4 gap-2">
                <Input
                  required
                  type="number"
                  step="0.01"
                  placeholder="Unit Price"
                  value={line.unit_price || ''}
                  onChange={(e) => updateOrderLine(index, 'unit_price', parseFloat(e.target.value) || 0)}
                  className="border-heavy mono"
                />
                <Input
                  required
                  type="number"
                  placeholder="Amount"
                  value={line.amount || ''}
                  onChange={(e) => updateOrderLine(index, 'amount', parseFloat(e.target.value) || 0)}
                  className="border-heavy mono"
                />
                <Input
                  required
                  placeholder="Unit"
                  value={line.unit}
                  onChange={(e) => updateOrderLine(index, 'unit', e.target.value)}
                  className="border-heavy"
                />
                <Input
                  required
                  type="number"
                  step="0.01"
                  placeholder="Total Price"
                  value={line.total_price || ''}
                  onChange={(e) => updateOrderLine(index, 'total_price', parseFloat(e.target.value) || 0)}
                  className="border-heavy mono"
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="border-ultra p-4 bg-secondary">
        <div className="flex justify-between items-center">
          <span className="font-bold text-xl">TOTAL NET COST</span>
          <span className="mono font-bold text-2xl">{getCurrencySymbol(currentCurrency)}{calculateTotal().toFixed(2)}</span>
        </div>
      </div>

      <div className="flex gap-4">
        {isEditingExisting && onDelete && (
          <Button
            type="button"
            onClick={onDelete}
            variant="destructive"
            className="border-ultra h-14 text-lg font-bold shadow-brutal px-8"
          >
            <Trash className="w-5 h-5 mr-2" />
            DELETE
          </Button>
        )}
        <Button
          type="submit"
          disabled={isSubmitting}
          className="flex-1 border-ultra bg-accent text-accent-foreground hover:bg-accent/80 h-14 text-lg font-bold shadow-brutal"
        >
          {isSubmitting 
            ? (isEditingExisting ? 'SAVING...' : 'SUBMITTING...') 
            : (isEditingExisting ? 'SAVE AND EXIT' : 'SUBMIT REQUEST')
          }
        </Button>
      </div>
    </form>
  );
};
