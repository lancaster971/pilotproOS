// Simulazione produzione
const API_BASE_URL = 'https://api.pilotpros.com';
const VITE_API_URL = process.env.VITE_API_URL || API_BASE_URL;

console.log('🚀 Production Test:');
console.log('Environment VITE_API_URL:', process.env.VITE_API_URL);
console.log('Fallback API_BASE_URL:', API_BASE_URL);
console.log('Final URL used:', VITE_API_URL);
console.log('');

// Test con env var settata
process.env.VITE_API_URL = 'https://api.customer.com';
const customUrl = process.env.VITE_API_URL || API_BASE_URL;
console.log('🏢 Customer deployment:');
console.log('Customer VITE_API_URL:', process.env.VITE_API_URL);
console.log('Final URL:', customUrl);
