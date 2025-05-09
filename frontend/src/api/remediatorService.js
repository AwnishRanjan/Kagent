import api from './api';

const remediatorService = {
  // Get current issues
  getIssues: async () => {
    const response = await api.get('/remediator/issues');
    return response.data;
  },
  
  // Get remediation suggestions
  getRemediationSuggestions: async (issueId) => {
    const response = await api.get(`/remediator/issues/${issueId}/suggestions`);
    return response.data;
  },
  
  // Apply remediation
  applyRemediation: async (issueId, remediationId) => {
    const response = await api.post(`/remediator/issues/${issueId}/remediate`, { remediationId });
    return response.data;
  },
  
  // Get remediation history
  getRemediationHistory: async () => {
    const response = await api.get('/remediator/history');
    return response.data;
  },
  
  // Get remediation details
  getRemediationDetails: async (remediationId) => {
    const response = await api.get(`/remediator/remediation/${remediationId}`);
    return response.data;
  },
  
  // Set auto-remediation settings
  setAutoRemediationSettings: async (settings) => {
    const response = await api.put('/remediator/settings/auto', settings);
    return response.data;
  },
  
  // Get auto-remediation settings
  getAutoRemediationSettings: async () => {
    const response = await api.get('/remediator/settings/auto');
    return response.data;
  },
};

export default remediatorService; 