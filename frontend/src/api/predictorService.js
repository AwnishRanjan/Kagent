import api from './api';

const predictorService = {
  // Get current metrics
  getMetrics: async () => {
    const response = await api.get('/predictor/metrics');
    return response.data;
  },
  
  // Get prediction results
  getPredictions: async () => {
    const response = await api.get('/predictor/predictions');
    return response.data;
  },
  
  // Get historical metrics
  getHistoricalMetrics: async (timespan = '24h') => {
    const response = await api.get(`/predictor/metrics/history?timespan=${timespan}`);
    return response.data;
  },
  
  // Train the ML model
  trainModel: async (params) => {
    const response = await api.post('/predictor/model/train', params);
    return response.data;
  },
  
  // Get model info
  getModelInfo: async () => {
    const response = await api.get('/predictor/model/info');
    return response.data;
  },
};

export default predictorService; 