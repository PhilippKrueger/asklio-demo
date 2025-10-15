export interface ValidationResult {
  isValid: boolean;
  error?: string;
  sanitizedValue: string | number;
}

export const sanitizeText = (input: string): string => {
  return input
    .replace(/[<>]/g, '') // Remove potential XSS characters
    .replace(/[&"']/g, (match) => { // Escape HTML entities
      const entities: { [key: string]: string } = {
        '&': '&amp;',
        '"': '&quot;',
        "'": '&#x27;'
      };
      return entities[match];
    })
    .trim();
};

export const validateTextLength = (
  value: string, 
  maxLength: number, 
  fieldName: string
): ValidationResult => {
  const sanitized = sanitizeText(value);
  
  if (sanitized.length === 0) {
    return {
      isValid: false,
      error: `${fieldName} is required`,
      sanitizedValue: sanitized
    };
  }
  
  if (sanitized.length > maxLength) {
    return {
      isValid: false,
      error: `${fieldName} must be ${maxLength} characters or less`,
      sanitizedValue: sanitized.substring(0, maxLength)
    };
  }
  
  return {
    isValid: true,
    sanitizedValue: sanitized
  };
};

export const validateVatId = (vatId: string): ValidationResult => {
  const sanitized = sanitizeText(vatId);
  
  if (sanitized.length === 0) {
    return {
      isValid: false,
      error: 'VAT ID is required',
      sanitizedValue: sanitized
    };
  }
  
  // VAT ID pattern: 2-4 letters followed by 8-12 digits
  const vatPattern = /^[A-Z]{2,4}[0-9]{8,12}$/;
  const upperCased = sanitized.toUpperCase();
  
  if (!vatPattern.test(upperCased)) {
    return {
      isValid: false,
      error: 'VAT ID must be 2-4 letters followed by 8-12 digits (e.g., DE123456789)',
      sanitizedValue: upperCased
    };
  }
  
  return {
    isValid: true,
    sanitizedValue: upperCased
  };
};

export const validateDepartment = (department: string): ValidationResult => {
  const sanitized = sanitizeText(department);
  
  if (sanitized.length === 0) {
    return {
      isValid: false,
      error: 'Department is required',
      sanitizedValue: sanitized
    };
  }
  
  // Department pattern: letters, spaces, hyphens, and common abbreviations
  const departmentPattern = /^[A-Za-z\s\-&.()]+$/;
  
  if (!departmentPattern.test(sanitized)) {
    return {
      isValid: false,
      error: 'Department can only contain letters, spaces, hyphens, and common punctuation',
      sanitizedValue: sanitized.replace(/[^A-Za-z\s\-&.()]/g, '')
    };
  }
  
  if (sanitized.length > 50) {
    return {
      isValid: false,
      error: 'Department must be 50 characters or less',
      sanitizedValue: sanitized.substring(0, 50)
    };
  }
  
  return {
    isValid: true,
    sanitizedValue: sanitized
  };
};

export const validateNumericInput = (
  value: string,
  fieldName: string,
  min: number = 0,
  max: number = 1000000
): ValidationResult => {
  const numValue = parseFloat(value);
  
  if (isNaN(numValue)) {
    return {
      isValid: false,
      error: `${fieldName} must be a valid number`,
      sanitizedValue: 0
    };
  }
  
  if (numValue < min) {
    return {
      isValid: false,
      error: `${fieldName} must be at least ${min}`,
      sanitizedValue: min
    };
  }
  
  if (numValue > max) {
    return {
      isValid: false,
      error: `${fieldName} cannot exceed ${max}`,
      sanitizedValue: max
    };
  }
  
  return {
    isValid: true,
    sanitizedValue: numValue
  };
};

export const validatePositionDescription = (description: string): ValidationResult => {
  const sanitized = sanitizeText(description);
  
  if (sanitized.length === 0) {
    return {
      isValid: false,
      error: 'Position description is required',
      sanitizedValue: sanitized
    };
  }
  
  if (sanitized.length > 500) {
    return {
      isValid: false,
      error: 'Position description must be 500 characters or less',
      sanitizedValue: sanitized.substring(0, 500)
    };
  }
  
  return {
    isValid: true,
    sanitizedValue: sanitized
  };
};

export const validateUnit = (unit: string): ValidationResult => {
  const trimmed = unit.trim();
  
  if (trimmed.length === 0) {
    return {
      isValid: false,
      error: 'Unit is required',
      sanitizedValue: trimmed
    };
  }
  
  if (trimmed.length > 20) {
    return {
      isValid: false,
      error: 'Unit must be 20 characters or less',
      sanitizedValue: trimmed.substring(0, 20)
    };
  }
  
  return {
    isValid: true,
    sanitizedValue: trimmed
  };
};

export const VALIDATION_LIMITS = {
  REQUESTOR_NAME: 100,
  TITLE: 200,
  VENDOR_NAME: 100,
  DEPARTMENT: 50,
  POSITION_DESCRIPTION: 500,
  UNIT: 20,
  MAX_PRICE: 1000000,
  MAX_QUANTITY: 10000
};