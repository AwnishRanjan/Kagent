import React, { useState, useEffect } from 'react';

function BackupManager() {
  const [backups, setBackups] = useState([]);
  const [restores, setRestores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedResources, setSelectedResources] = useState([]);
  const [backupName, setBackupName] = useState('');
  const [namespaces, setNamespaces] = useState([]);
  const [selectedNamespace, setSelectedNamespace] = useState('all');

  useEffect(() => {
    // Simulate API call to fetch backup data
    setTimeout(() => {
      const mockBackups = [
        {
          id: 'backup-001',
          name: 'daily-backup-20250511',
          status: 'completed',
          timestamp: '2025-05-11T23:00:00Z',
          resources: 42,
          size: '56 MB',
          namespace: 'default'
        },
        {
          id: 'backup-002',
          name: 'daily-backup-20250510',
          status: 'completed',
          timestamp: '2025-05-10T23:00:00Z',
          resources: 42,
          size: '55 MB',
          namespace: 'default'
        },
        {
          id: 'backup-003',
          name: 'weekly-backup-20250505',
          status: 'completed',
          timestamp: '2025-05-05T22:00:00Z',
          resources: 68,
          size: '102 MB',
          namespace: 'all'
        },
        {
          id: 'backup-004',
          name: 'custom-nginx-backup',
          status: 'completed',
          timestamp: '2025-05-09T14:30:00Z',
          resources: 5,
          size: '8 MB',
          namespace: 'default'
        },
        {
          id: 'backup-005',
          name: 'pre-update-backup',
          status: 'completed',
          timestamp: '2025-05-07T09:15:00Z',
          resources: 36,
          size: '48 MB',
          namespace: 'kube-system'
        }
      ];
      
      const mockRestores = [
        {
          id: 'restore-001',
          name: 'restore-after-issue',
          status: 'completed',
          timestamp: '2025-05-11T10:22:00Z',
          resources: 15,
          sourceBackup: 'daily-backup-20250510',
          namespace: 'default'
        },
        {
          id: 'restore-002',
          name: 'test-restore-procedure',
          status: 'completed',
          timestamp: '2025-05-09T15:45:00Z',
          resources: 5,
          sourceBackup: 'custom-nginx-backup',
          namespace: 'default'
        },
        {
          id: 'restore-003',
          name: 'rollback-faulty-update',
          status: 'completed',
          timestamp: '2025-05-08T11:30:00Z',
          resources: 36,
          sourceBackup: 'pre-update-backup',
          namespace: 'kube-system'
        }
      ];
      
      const mockNamespaces = ['default', 'kube-system', 'monitoring', 'ingress-nginx'];
      
      const mockSelectedResources = [
        { kind: 'Deployment', name: 'nginx-test', namespace: 'default' },
        { kind: 'Service', name: 'nginx-test', namespace: 'default' },
        { kind: 'ConfigMap', name: 'prometheus-server', namespace: 'default' }
      ];
      
      setBackups(mockBackups);
      setRestores(mockRestores);
      setNamespaces(mockNamespaces);
      setSelectedResources(mockSelectedResources);
      setLoading(false);
    }, 1000);
  }, []);

  const handleCreateBackup = () => {
    if (!backupName) {
      alert('Please enter a backup name');
      return;
    }
    
    // Here would be the API call to create a backup
    alert(`Creating backup: ${backupName}`);
  };

  const handleRestore = (backupId) => {
    // Here would be the API call to restore from a backup
    const backup = backups.find(b => b.id === backupId);
    if (backup) {
      alert(`Restoring from backup: ${backup.name}`);
    }
  };

  const handleSelectResource = (resource) => {
    if (selectedResources.some(r => r.name === resource.name && r.kind === resource.kind)) {
      setSelectedResources(selectedResources.filter(r => !(r.name === resource.name && r.kind === resource.kind)));
    } else {
      setSelectedResources([...selectedResources, resource]);
    }
  };

  const formatDate = (dateString) => {
    const options = { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit', 
      hour: '2-digit', 
      minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'in-progress':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Backup Manager</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white shadow-md rounded-lg overflow-hidden">
          <div className="p-4 bg-blue-50 border-b border-blue-100">
            <h2 className="text-lg font-semibold text-blue-800">Create New Backup</h2>
          </div>
          <div className="p-4">
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Backup Name</label>
              <input 
                type="text"
                className="w-full p-2 border border-gray-300 rounded"
                placeholder="Enter backup name"
                value={backupName}
                onChange={(e) => setBackupName(e.target.value)}
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Namespace</label>
              <select 
                className="w-full p-2 border border-gray-300 rounded"
                value={selectedNamespace}
                onChange={(e) => setSelectedNamespace(e.target.value)}
              >
                <option value="all">All Namespaces</option>
                {namespaces.map(ns => (
                  <option key={ns} value={ns}>{ns}</option>
                ))}
              </select>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Resources to Backup ({selectedResources.length} selected)
              </label>
              <div className="border border-gray-300 rounded max-h-60 overflow-y-auto p-2">
                {loading ? (
                  <p className="text-gray-500 text-center p-4">Loading resources...</p>
                ) : (
                  <div className="space-y-2">
                    {[
                      { kind: 'Deployment', name: 'nginx-test', namespace: 'default' },
                      { kind: 'Service', name: 'nginx-test', namespace: 'default' },
                      { kind: 'ConfigMap', name: 'prometheus-server', namespace: 'default' },
                      { kind: 'Secret', name: 'prometheus-token', namespace: 'default' },
                      { kind: 'Deployment', name: 'prometheus-server', namespace: 'default' },
                      { kind: 'Service', name: 'prometheus-server', namespace: 'default' }
                    ].map((resource, idx) => (
                      <div key={idx} className="flex items-center">
                        <input
                          type="checkbox"
                          id={`resource-${idx}`}
                          checked={selectedResources.some(r => r.name === resource.name && r.kind === resource.kind)}
                          onChange={() => handleSelectResource(resource)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <label htmlFor={`resource-${idx}`} className="ml-2 block text-sm text-gray-900">
                          <span className="font-medium">{resource.kind}</span>: {resource.name} 
                          <span className="text-xs text-gray-500 ml-1">({resource.namespace})</span>
                        </label>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            <button 
              className="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
              onClick={handleCreateBackup}
            >
              Create Backup
            </button>
          </div>
        </div>
        
        <div className="bg-white shadow-md rounded-lg overflow-hidden">
          <div className="p-4 bg-green-50 border-b border-green-100">
            <h2 className="text-lg font-semibold text-green-800">Backup Status</h2>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 text-center">
                <span className="text-2xl font-bold text-blue-700">{backups.length}</span>
                <p className="text-sm text-gray-600">Total Backups</p>
              </div>
              <div className="bg-green-50 border border-green-100 rounded-lg p-4 text-center">
                <span className="text-2xl font-bold text-green-700">{restores.length}</span>
                <p className="text-sm text-gray-600">Restore Operations</p>
              </div>
            </div>
            
            <div className="space-y-2">
              <h3 className="text-md font-medium text-gray-700">Latest Backup:</h3>
              {loading ? (
                <p className="text-gray-500">Loading...</p>
              ) : backups.length > 0 ? (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">{backups[0].name}</p>
                      <p className="text-sm text-gray-500">
                        {formatDate(backups[0].timestamp)} • {backups[0].resources} resources • {backups[0].size}
                      </p>
                    </div>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusClass(backups[0].status)}`}>
                      {backups[0].status.charAt(0).toUpperCase() + backups[0].status.slice(1)}
                    </span>
                  </div>
                </div>
              ) : (
                <p className="text-gray-500">No backups found</p>
              )}
              
              <h3 className="text-md font-medium text-gray-700 mt-4">Latest Restore:</h3>
              {loading ? (
                <p className="text-gray-500">Loading...</p>
              ) : restores.length > 0 ? (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">{restores[0].name}</p>
                      <p className="text-sm text-gray-500">
                        {formatDate(restores[0].timestamp)} • {restores[0].resources} resources
                      </p>
                      <p className="text-sm text-gray-500">
                        From: {restores[0].sourceBackup}
                      </p>
                    </div>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusClass(restores[0].status)}`}>
                      {restores[0].status.charAt(0).toUpperCase() + restores[0].status.slice(1)}
                    </span>
                  </div>
                </div>
              ) : (
                <p className="text-gray-500">No restores found</p>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white shadow-md rounded-lg overflow-hidden mt-8">
        <div className="p-4 border-b flex justify-between items-center">
          <h2 className="text-lg font-semibold">Backup History</h2>
        </div>
        <div className="overflow-x-auto">
          {loading ? (
            <div className="p-8 text-center">
              <p className="text-gray-500">Loading backup history...</p>
            </div>
          ) : backups.length > 0 ? (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Resources
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Size
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Namespace
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {backups.map((backup) => (
                  <tr key={backup.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {backup.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(backup.timestamp)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusClass(backup.status)}`}>
                        {backup.status.charAt(0).toUpperCase() + backup.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {backup.resources}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {backup.size}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {backup.namespace}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button 
                        className="text-blue-600 hover:text-blue-900 mr-3"
                        onClick={() => handleRestore(backup.id)}
                      >
                        Restore
                      </button>
                      <button className="text-red-600 hover:text-red-900">
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-8 text-center">
              <p className="text-gray-500">No backups found.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default BackupManager; 