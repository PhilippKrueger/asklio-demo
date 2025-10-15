export const getCurrencySymbol = (currencyCode?: string): string => {
  if (!currencyCode) return '€';
  
  const currencyMap: Record<string, string> = {
    'EUR': '€',
    'USD': '$',
    'GBP': '£',
    'JPY': '¥',
    'CHF': '₣',
    'CAD': 'C$',
    'AUD': 'A$',
    'CNY': '¥',
    'SEK': 'kr',
    'NOK': 'kr',
    'DKK': 'kr',
    'PLN': 'zł',
    'CZK': 'Kč',
    'HUF': 'Ft',
    'RUB': '₽',
    'BRL': 'R$',
    'INR': '₹',
    'KRW': '₩',
    'SGD': 'S$',
    'HKD': 'HK$',
    'NZD': 'NZ$',
    'MXN': '$',
    'ZAR': 'R',
    'TRY': '₺',
    'THB': '฿'
  };

  return currencyMap[currencyCode.toUpperCase()] || currencyCode;
};