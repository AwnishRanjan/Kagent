import api from './api';

const backupService = {
  // Get all backups
  getBackups: async () => {
    const response = await api.get('/backup/list');
    return response.data;
  },
  
  // Get backup details
  getBackupDetails: async (backupId) => {
    const response = await api.get(`/backup/${backupId}`);
    return response.data;
  },
  
  // Create a new backup
  createBackup: async (params) => {
    const response = await api.post('/backup/create', params);
    return response.data;
  },
  
  // Restore from backup
  restoreFromBackup: async (backupId, params = {}) => {
    const response = await api.post(`/backup/${backupId}/restore`, params);
    return response.data;
  },
  
  // Delete a backup
  deleteBackup: async (backupId) => {
    const response = await api.delete(`/backup/${backupId}`);
    return response.data;
  },
  
  // Get restore jobs
  getRestoreJobs: async () => {
    const response = await api.get('/backup/restore/jobs');
    return response.data;
  },
  
  // Get backup schedule
  getBackupSchedule: async () => {
    const response = await api.get('/backup/schedule');
    return response.data;
  },
  
  // Update backup schedule
  updateBackupSchedule: async (params) => {
    const response = await api.put('/backup/schedule', params);
    return response.data;
  },
};

export default backupService; 