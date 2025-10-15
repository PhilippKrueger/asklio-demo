import { useState, useEffect } from 'react';
import { Plus, Trash2, Trash, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RequestCreate, RequestUpdate, OrderLine, ExtractedData, Request, CommodityGroup } from '@/types/request';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/lib/api';
import { getCurrencySymbol } from '@/lib/currency';
import { 
  validateTextLength, 
  validateVatId, 
  validateDepartment, 
  validateNumericInput, 
  validatePositionDescription, 
  validateUnit,
  VALIDATION_LIMITS,
  ValidationResult 
} from '@/lib/validation';

interface RequestFormProps {
  extractedData?: ExtractedData;
  existingRequest?: Request;
  mode?: 'create' | 'view';
  onSuccess?: () => void;
  onDelete?: () => void;
}

export const RequestForm = ({ extractedData, existingRequest, mode = 'create', onSuccess, onDelete }: RequestFormProps) => {
  console.log('RequestForm - extractedData:', extractedData);
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [commodityGroups, setCommodityGroups] = useState<CommodityGroup[]>([]);
  const [isLoadingGroups, setIsLoadingGroups] = useState(true);
  const isViewMode = mode === 'view';
  const isEditingExisting = Boolean(existingRequest);
  
  const [validationErrors, setValidationErrors] = useState<{ [key: string]: string }>({});
  const [touchedFields, setTouchedFields] = useState<{ [key: string]: boolean }>({});

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
      requestor_name: extractedData?.requestor_name || '',
      title: extractedData?.title || '',
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

  const validateAndUpdateField = (field: keyof RequestCreate, value: any, validator?: (val: string) => ValidationResult) => {
    setTouchedFields(prev => ({ ...prev, [field]: true }));
    
    if (validator && typeof value === 'string') {
      const result = validator(value);
      setValidationErrors(prev => ({
        ...prev,
        [field]: result.isValid ? '' : result.error || ''
      }));
      setFormData((prev) => ({ ...prev, [field]: result.sanitizedValue }));
    } else {
      setFormData((prev) => ({ ...prev, [field]: value }));
      setValidationErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const updateField = (field: keyof RequestCreate, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleFieldChange = (field: keyof RequestCreate, value: string, validator?: (val: string) => ValidationResult) => {
    if (validator) {
      validateAndUpdateField(field, value, validator);
    } else {
      updateField(field, value);
    }
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

  const handleOrderLineChange = (index: number, field: keyof OrderLine, value: string) => {
    const fieldKey = `orderLine_${index}_${field}`;
    setTouchedFields(prev => ({ ...prev, [fieldKey]: true }));

    let validationResult: ValidationResult | null = null;
    let processedValue: any = value;

    switch (field) {
      case 'position_description':
        validationResult = validatePositionDescription(value);
        processedValue = validationResult.sanitizedValue;
        break;
      case 'unit':
        validationResult = validateUnit(value);
        processedValue = validationResult.sanitizedValue;
        break;
      case 'unit_price':
      case 'amount':
      case 'total_price':
        validationResult = validateNumericInput(
          value, 
          field === 'unit_price' ? 'Unit Price' : 
          field === 'amount' ? 'Amount' : 'Total Price',
          0,
          field === 'amount' ? VALIDATION_LIMITS.MAX_QUANTITY : VALIDATION_LIMITS.MAX_PRICE
        );
        processedValue = validationResult.sanitizedValue;
        break;
      default:
        processedValue = value;
    }

    if (validationResult) {
      setValidationErrors(prev => ({
        ...prev,
        [fieldKey]: validationResult!.isValid ? '' : validationResult!.error || ''
      }));
    }

    updateOrderLine(index, field, processedValue);
  };

  const calculateTotal = () => {
    return formData.order_lines.reduce((sum, line) => sum + line.total_price, 0);
  };

  const validateAllFields = (): boolean => {
    const errors: { [key: string]: string } = {};
    
    // Validate main fields
    const requestorNameResult = validateTextLength(formData.requestor_name, VALIDATION_LIMITS.REQUESTOR_NAME, 'Requestor Name');
    if (!requestorNameResult.isValid) errors.requestor_name = requestorNameResult.error!;
    
    const titleResult = validateTextLength(formData.title, VALIDATION_LIMITS.TITLE, 'Title');
    if (!titleResult.isValid) errors.title = titleResult.error!;
    
    const vendorNameResult = validateTextLength(formData.vendor_name, VALIDATION_LIMITS.VENDOR_NAME, 'Vendor Name');
    if (!vendorNameResult.isValid) errors.vendor_name = vendorNameResult.error!;
    
    const vatIdResult = validateVatId(formData.vat_id || '');
    if (!vatIdResult.isValid) errors.vat_id = vatIdResult.error!;
    
    const departmentResult = validateDepartment(formData.department || '');
    if (!departmentResult.isValid) errors.department = departmentResult.error!;
    
    // Validate order lines
    formData.order_lines.forEach((line, index) => {
      const descResult = validatePositionDescription(line.position_description);
      if (!descResult.isValid) errors[`orderLine_${index}_position_description`] = descResult.error!;
      
      const unitResult = validateUnit(line.unit);
      if (!unitResult.isValid) errors[`orderLine_${index}_unit`] = unitResult.error!;
      
      const priceResult = validateNumericInput(line.unit_price.toString(), 'Unit Price', 0, VALIDATION_LIMITS.MAX_PRICE);
      if (!priceResult.isValid) errors[`orderLine_${index}_unit_price`] = priceResult.error!;
      
      const amountResult = validateNumericInput(line.amount.toString(), 'Amount', 0, VALIDATION_LIMITS.MAX_QUANTITY);
      if (!amountResult.isValid) errors[`orderLine_${index}_amount`] = amountResult.error!;
    });
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateAllFields()) {
      toast({
        title: 'Validation Error',
        description: 'Please fix the errors below before submitting',
        variant: 'destructive',
      });
      return;
    }
    
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

  const ErrorMessage = ({ fieldKey }: { fieldKey: string }) => {
    const error = validationErrors[fieldKey];
    const isTouched = touchedFields[fieldKey];
    
    if (!error || !isTouched) return null;
    
    return (
      <div className="flex items-center gap-1 text-red-500 text-xs mt-1">
        <AlertCircle className="w-3 h-3" />
        <span>{error}</span>
      </div>
    );
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label className="font-bold text-sm mb-2 block">REQUESTOR NAME</Label>
          <Input
            required
            maxLength={VALIDATION_LIMITS.REQUESTOR_NAME}
            value={formData.requestor_name}
            onChange={(e) => handleFieldChange('requestor_name', e.target.value, (val) => validateTextLength(val, VALIDATION_LIMITS.REQUESTOR_NAME, 'Requestor Name'))}
            className={`border-heavy ${validationErrors.requestor_name && touchedFields.requestor_name ? 'border-red-500' : ''}`}
          />
          <ErrorMessage fieldKey="requestor_name" />
        </div>
        <div>
          <Label className="font-bold text-sm mb-2 block">DEPARTMENT</Label>
          <Input
            required
            maxLength={VALIDATION_LIMITS.DEPARTMENT}
            value={formData.department}
            onChange={(e) => handleFieldChange('department', e.target.value, validateDepartment)}
            className={`border-heavy ${validationErrors.department && touchedFields.department ? 'border-red-500' : ''}`}
          />
          <ErrorMessage fieldKey="department" />
        </div>
      </div>

      <div>
        <Label className="font-bold text-sm mb-2 block">TITLE / SHORT DESCRIPTION</Label>
        <Input
          required
          maxLength={VALIDATION_LIMITS.TITLE}
          value={formData.title}
          onChange={(e) => handleFieldChange('title', e.target.value, (val) => validateTextLength(val, VALIDATION_LIMITS.TITLE, 'Title'))}
          className={`border-heavy ${validationErrors.title && touchedFields.title ? 'border-red-500' : ''}`}
        />
        <ErrorMessage fieldKey="title" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label className="font-bold text-sm mb-2 block">VENDOR NAME</Label>
          <Input
            required
            maxLength={VALIDATION_LIMITS.VENDOR_NAME}
            value={formData.vendor_name}
            onChange={(e) => handleFieldChange('vendor_name', e.target.value, (val) => validateTextLength(val, VALIDATION_LIMITS.VENDOR_NAME, 'Vendor Name'))}
            className={`border-heavy ${validationErrors.vendor_name && touchedFields.vendor_name ? 'border-red-500' : ''}`}
          />
          <ErrorMessage fieldKey="vendor_name" />
        </div>
        <div>
          <Label className="font-bold text-sm mb-2 block">VAT ID</Label>
          <Input
            required
            value={formData.vat_id}
            onChange={(e) => handleFieldChange('vat_id', e.target.value, validateVatId)}
            className={`border-heavy mono ${validationErrors.vat_id && touchedFields.vat_id ? 'border-red-500' : ''}`}
            placeholder="e.g., DE123456789"
          />
          <ErrorMessage fieldKey="vat_id" />
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
                <Button
                  type="button"
                  onClick={() => removeOrderLine(index)}
                  variant="ghost"
                  size="sm"
                  disabled={formData.order_lines.length === 1}
                  title={formData.order_lines.length === 1 ? "Cannot delete last line item" : "Delete line item"}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>

              <Input
                required
                maxLength={VALIDATION_LIMITS.POSITION_DESCRIPTION}
                placeholder="Position Description"
                value={line.position_description}
                onChange={(e) => handleOrderLineChange(index, 'position_description', e.target.value)}
                className={`border-heavy ${validationErrors[`orderLine_${index}_position_description`] && touchedFields[`orderLine_${index}_position_description`] ? 'border-red-500' : ''}`}
              />
              <ErrorMessage fieldKey={`orderLine_${index}_position_description`} />

              <div className="grid grid-cols-4 gap-2">
                <div>
                  <Input
                    required
                    type="number"
                    step="0.01"
                    min="0"
                    max={VALIDATION_LIMITS.MAX_PRICE}
                    placeholder="Unit Price"
                    value={line.unit_price || ''}
                    onChange={(e) => handleOrderLineChange(index, 'unit_price', e.target.value)}
                    className={`border-heavy mono ${validationErrors[`orderLine_${index}_unit_price`] && touchedFields[`orderLine_${index}_unit_price`] ? 'border-red-500' : ''}`}
                  />
                  <ErrorMessage fieldKey={`orderLine_${index}_unit_price`} />
                </div>
                <div>
                  <Input
                    required
                    type="number"
                    step="0.01"
                    min="0"
                    max={VALIDATION_LIMITS.MAX_QUANTITY}
                    placeholder="Amount"
                    value={line.amount || ''}
                    onChange={(e) => handleOrderLineChange(index, 'amount', e.target.value)}
                    className={`border-heavy mono ${validationErrors[`orderLine_${index}_amount`] && touchedFields[`orderLine_${index}_amount`] ? 'border-red-500' : ''}`}
                  />
                  <ErrorMessage fieldKey={`orderLine_${index}_amount`} />
                </div>
                <div>
                  <Input
                    required
                    maxLength={VALIDATION_LIMITS.UNIT}
                    placeholder="Unit"
                    value={line.unit}
                    onChange={(e) => handleOrderLineChange(index, 'unit', e.target.value)}
                    className={`border-heavy ${validationErrors[`orderLine_${index}_unit`] && touchedFields[`orderLine_${index}_unit`] ? 'border-red-500' : ''}`}
                  />
                  <ErrorMessage fieldKey={`orderLine_${index}_unit`} />
                </div>
                <div>
                  <Input
                    required
                    type="number"
                    step="0.01"
                    placeholder="Total Price"
                    value={line.total_price || ''}
                    readOnly
                    className="border-heavy mono bg-gray-50"
                  />
                </div>
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
