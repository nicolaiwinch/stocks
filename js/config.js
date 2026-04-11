export const API_URL = localStorage.getItem('api_url') || 'http://localhost:8000';

export const SEGMENTS = ['All', 'C25', 'Large Cap', 'Mid Cap', 'Small Cap'];

export const SORT_OPTIONS = [
  { key: 'total', label: 'Total Score' },
  { key: 'momentum', label: 'Momentum' },
  { key: 'valuation', label: 'Valuation' },
  { key: 'ticker', label: 'Ticker' },
  { key: 'name', label: 'Name' },
];
