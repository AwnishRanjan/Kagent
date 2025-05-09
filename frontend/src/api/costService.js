import api from './api';

const costService = {
  // Get cost analysis
  getCostAnalysis: async () => {
    const response = await api.get('/cost/analysis');
    return response.data;
  },
  
  // Get optimization suggestions
  getOptimizationSuggestions: async () => {
    const response = await api.get('/cost/suggestions');
    return response.data;
  },
  
  // Get resource utilization
  getResourceUtilization: async () => {
    const response = await api.get('/cost/utilization');
    return response.data;
  },
  
  // Apply optimization
  applyOptimization: async (optimizationId) => {
    const response = await api.post(`/cost/optimize/${optimizationId}`);
    return response.data;
  },
  
  // Get cost history
  getCostHistory: async (timespan = '30d') => {
    const response = await api.get(`/cost/history?timespan=${timespan}`);
    return response.data;
  },
  
  // Get cloud provider cost details
  getCloudProviderDetails: async () => {
    const response = await api.get('/cost/cloud/details');
    return response.data;
  },
};

export default costService; 