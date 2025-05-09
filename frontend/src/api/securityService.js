import api from './api';

const securityService = {
  // Get security scan results
  getScanResults: async () => {
    const response = await api.get('/security/scan/results');
    return response.data;
  },
  
  // Start a new security scan
  startScan: async (params = {}) => {
    const response = await api.post('/security/scan/start', params);
    return response.data;
  },
  
  // Get vulnerabilities
  getVulnerabilities: async (severity = 'all') => {
    const response = await api.get(`/security/vulnerabilities?severity=${severity}`);
    return response.data;
  },
  
  // Get misconfigurations
  getMisconfigurations: async () => {
    const response = await api.get('/security/misconfigurations');
    return response.data;
  },
  
  // Get compliance issues
  getComplianceIssues: async () => {
    const response = await api.get('/security/compliance');
    return response.data;
  },
  
  // Get scan history
  getScanHistory: async () => {
    const response = await api.get('/security/scan/history');
    return response.data;
  },
};

export default securityService; 