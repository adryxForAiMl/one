module.exports = {
  reactStrictMode: true,
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000/api',
  },
  images: {
    domains: ['example.com'], // Add your image domains here
  },
  webpack: (config) => {
    // Custom webpack configurations can go here
    return config;
  },
};