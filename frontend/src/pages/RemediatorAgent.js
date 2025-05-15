import React, { useState, useEffect } from 'react';

function RemediatorAgent() {
  const [actions, setActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autoRemediate, setAutoRemediate] = useState(false);
  const [activeTab, setActiveTab] = useState('pending');

  useEffect(() => {
    // Simulate API call to fetch remediation actions
    setTimeout(() => {
      const mockActions = [
        {
          id: 'action-001',
          status: 'pending',
          issue: 'High CPU usage on node kagent-cluster-worker',
          description: 'CPU usage at 92%, exceeding threshold of 80%',
          severity: 'critical',
          timestamp: '2025-05-12T12:40:00Z',
          resource: 'kagent-cluster-worker',
          resourceType: 'Node',
          remediation: 'Evict non-critical pods to reduce load',
          autoRemediate: true
        },
        {
          id: 'action-002',
          status: 'completed',
          issue: 'Memory pressure on node kagent-cluster-worker2',
          description: 'Memory usage at 85%, exceeding threshold of 80%',
          severity: 'high',
          timestamp: '2025-05-12T12:35:00Z',
          resource: 'kagent-cluster-worker2',
          resourceType: 'Node',
          remediation: 'Evicted pods with lower priority',
          autoRemediate: true,
          executedAt: '2025-05-12T12:36:00Z',
          result: 'success',
          details: 'Evicted 3 pods to reduce memory pressure'
        },
        {
          id: 'action-003',
          status: 'failed',
          issue: 'Pod restart loop for nginx-test-7f8bcbcf44-5zxkq',
          description: 'Pod has restarted 5 times in the last 15 minutes',
          severity: 'high',
          timestamp: '2025-05-12T12:30:00Z',
          resource: 'nginx-test-7f8bcbcf44-5zxkq',
          resourceType: 'Pod',
          remediation: 'Delete and recreate pod',
          autoRemediate: true,
          executedAt: '2025-05-12T12:31:00Z',
          result: 'failure',
          details: 'Failed to delete pod: permission denied'
        },
        {
          id: 'action-004',
          status: 'pending',
          issue: 'Service endpoint mismatch for prometheus-server',
          description: 'Service has no matching endpoints',
          severity: 'medium',
          timestamp: '2025-05-12T12:25:00Z',
          resource: 'prometheus-server',
          resourceType: 'Service',
          remediation: 'Recreate service with correct selector',
          autoRemediate: false
        },
        {
          id: 'action-005',
          status: 'completed',
          issue: 'ConfigMap prometheus-alertmanager out of sync',
          description: 'ConfigMap data does not match desired state',
          severity: 'low',
          timestamp: '2025-05-12T12:20:00Z',
          resource: 'prometheus-alertmanager',
          resourceType: 'ConfigMap',
          remediation: 'Update ConfigMap with correct data',
          autoRemediate: true,
          executedAt: '2025-05-12T12:21:00Z',
          result: 'success',
          details: 'ConfigMap updated successfully'
        }
      ];
      
      setActions(mockActions);
      setLoading(false);
    }, 1000);
  }, []);

  const handleExecuteAction = (actionId) => {
    // Here would be the API call to execute a remediation action
    setActions(actions.map(action => {
      if (action.id === actionId) {
        return {
          ...action,
          status: 'in-progress',
        };
      }
      return action;
    }));
    
    // Simulate action completion after a delay
    setTimeout(() => {
      setActions(actions.map(action => {
        if (action.id === actionId) {
          return {
            ...action,
            status: 'completed',
            executedAt: new Date().toISOString(),
            result: 'success',
            details: 'Remediation action executed successfully'
          };
        }
        return action;
      }));
    }, 2000);
  };

  const handleToggleAutoRemediate = () => {
    setAutoRemediate(!autoRemediate);
    // Here would be the API call to update auto-remediation setting
  };

  const getFilteredActions = () => {
    if (activeTab === 'all') return actions;
    return actions.filter(action => {
      if (activeTab === 'pending') return action.status === 'pending';
      if (activeTab === 'completed') return action.status === 'completed';
      if (activeTab === 'failed') return action.status === 'failed';
      return true;
    });
  };

  const formatDate = (dateString) => {
    const options = { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit', 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  const getSeverityClass = (severity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'in-progress':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getResourceTypeClass = (type) => {
    switch (type) {
      case 'Node':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'Pod':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'Service':
        return 'bg-teal-100 text-teal-800 border-teal-300';
      case 'ConfigMap':
        return 'bg-indigo-100 text-indigo-800 border-indigo-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const pendingCount = actions.filter(a => a.status === 'pending').length;
  const completedCount = actions.filter(a => a.status === 'completed').length;
  const failedCount = actions.filter(a => a.status === 'failed').length;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Remediator Agent</h1>
        <div className="flex items-center">
          <span className="mr-3 text-sm text-gray-700">Auto-Remediate</span>
          <div className="relative inline-block w-12 align-middle select-none">
            <input
              type="checkbox"
              id="toggle"
              checked={autoRemediate}
              onChange={handleToggleAutoRemediate}
              className="hidden"
            />
            <label 
              htmlFor="toggle" 
              className={`block h-6 rounded-full cursor-pointer transition-colors ${autoRemediate ? 'bg-green-500' : 'bg-gray-300'}`}
            >
              <span 
                className={`block h-6 w-6 rounded-full bg-white shadow transform transition-transform ${autoRemediate ? 'translate-x-6' : 'translate-x-0'}`}
              ></span>
            </label>
          </div>
        </div>
      </div>

      <div className="bg-white shadow-md rounded-lg overflow-hidden mb-8">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">Remediation Summary</h2>
          <div className="grid grid-cols-4 gap-4 mt-4">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
              <span className="text-3xl font-bold text-yellow-500">{pendingCount}</span>
              <p className="text-sm text-gray-600 mt-1">Pending</p>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
              <span className="text-3xl font-bold text-blue-500">
                {actions.filter(a => a.status === 'in-progress').length}
              </span>
              <p className="text-sm text-gray-600 mt-1">In Progress</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
              <span className="text-3xl font-bold text-green-500">{completedCount}</span>
              <p className="text-sm text-gray-600 mt-1">Completed</p>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
              <span className="text-3xl font-bold text-red-500">{failedCount}</span>
              <p className="text-sm text-gray-600 mt-1">Failed</p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex">
            <button
              className={`py-4 px-6 font-medium text-sm border-b-2 focus:outline-none ${
                activeTab === 'all'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => setActiveTab('all')}
            >
              All Actions ({actions.length})
            </button>
            <button
              className={`py-4 px-6 font-medium text-sm border-b-2 focus:outline-none ${
                activeTab === 'pending'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => setActiveTab('pending')}
            >
              Pending ({pendingCount})
            </button>
            <button
              className={`py-4 px-6 font-medium text-sm border-b-2 focus:outline-none ${
                activeTab === 'completed'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => setActiveTab('completed')}
            >
              Completed ({completedCount})
            </button>
            <button
              className={`py-4 px-6 font-medium text-sm border-b-2 focus:outline-none ${
                activeTab === 'failed'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              onClick={() => setActiveTab('failed')}
            >
              Failed ({failedCount})
            </button>
          </nav>
        </div>
        <div className="overflow-x-auto">
          {loading ? (
            <div className="p-8 text-center">
              <p className="text-gray-500">Loading remediation actions...</p>
            </div>
          ) : getFilteredActions().length > 0 ? (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Severity
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Issue
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Resource
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Detected
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {getFilteredActions().map((action) => (
                  <tr key={action.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusClass(action.status)}`}>
                        {action.status.charAt(0).toUpperCase() + action.status.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getSeverityClass(action.severity)}`}>
                        {action.severity.charAt(0).toUpperCase() + action.severity.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{action.issue}</div>
                      <div className="text-sm text-gray-500">{action.description}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="text-sm font-medium text-gray-900">
                          {action.resource}
                        </div>
                        <span className={`ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getResourceTypeClass(action.resourceType)}`}>
                          {action.resourceType}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(action.timestamp)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      {action.status === 'pending' && (
                        <button 
                          className="text-blue-600 hover:text-blue-900 mr-3"
                          onClick={() => handleExecuteAction(action.id)}
                        >
                          Execute
                        </button>
                      )}
                      <button className="text-indigo-600 hover:text-indigo-900">
                        Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-8 text-center">
              <p className="text-gray-500">No remediation actions found for the selected filter.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default RemediatorAgent; 