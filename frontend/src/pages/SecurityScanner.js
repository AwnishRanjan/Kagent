import React, { useState, useEffect } from 'react';

function SecurityScanner() {
  const [securityIssues, setSecurityIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    // Simulate API call to fetch security issues
    setTimeout(() => {
      const mockIssues = [
        {
          id: 1,
          type: 'vulnerability',
          severity: 'critical',
          resource: 'nginx-test deployment',
          description: 'Container using outdated image with known vulnerabilities',
          remediation: 'Update to latest version',
          detected: '2025-05-12T12:00:00Z',
        },
        {
          id: 2,
          type: 'misconfiguration',
          severity: 'high',
          resource: 'prometheus-server pod',
          description: 'Container running with privileged access',
          remediation: 'Remove privileged flag from pod spec',
          detected: '2025-05-12T12:10:00Z',
        },
        {
          id: 3,
          type: 'compliance',
          severity: 'medium',
          resource: 'default namespace',
          description: 'Resources without resource limits',
          remediation: 'Define resource limits for all containers',
          detected: '2025-05-12T12:15:00Z',
        },
        {
          id: 4,
          type: 'vulnerability',
          severity: 'high',
          resource: 'prometheus-alertmanager pod',
          description: 'Known vulnerability in base image',
          remediation: 'Update base image and rebuild',
          detected: '2025-05-12T12:20:00Z',
        },
        {
          id: 5,
          type: 'misconfiguration',
          severity: 'low',
          resource: 'kube-state-metrics deployment',
          description: 'Service account with excessive permissions',
          remediation: 'Limit service account permissions',
          detected: '2025-05-12T12:25:00Z',
        },
      ];
      setSecurityIssues(mockIssues);
      setLoading(false);
    }, 1000);
  }, []);

  const filteredIssues = securityIssues.filter(issue => {
    if (filter === 'all') return true;
    return issue.type === filter;
  });

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

  const getTypeClass = (type) => {
    switch (type) {
      case 'vulnerability':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'misconfiguration':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'compliance':
        return 'bg-teal-100 text-teal-800 border-teal-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Security Scanner</h1>
        <button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
          Run New Scan
        </button>
      </div>

      <div className="bg-white shadow-md rounded-lg overflow-hidden mb-8">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">Security Issues Summary</h2>
          <div className="grid grid-cols-4 gap-4 mt-4">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
              <span className="text-3xl font-bold text-red-500">
                {securityIssues.filter(i => i.severity === 'critical').length}
              </span>
              <p className="text-sm text-gray-600 mt-1">Critical</p>
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 text-center">
              <span className="text-3xl font-bold text-orange-500">
                {securityIssues.filter(i => i.severity === 'high').length}
              </span>
              <p className="text-sm text-gray-600 mt-1">High</p>
            </div>
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
              <span className="text-3xl font-bold text-yellow-500">
                {securityIssues.filter(i => i.severity === 'medium').length}
              </span>
              <p className="text-sm text-gray-600 mt-1">Medium</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
              <span className="text-3xl font-bold text-green-500">
                {securityIssues.filter(i => i.severity === 'low').length}
              </span>
              <p className="text-sm text-gray-600 mt-1">Low</p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <div className="p-4 border-b flex justify-between items-center">
          <h2 className="text-lg font-semibold">Security Issues ({filteredIssues.length})</h2>
          <div className="flex space-x-2">
            <select
              className="border rounded-md px-3 py-1.5 bg-white text-sm"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="all">All Types</option>
              <option value="vulnerability">Vulnerabilities</option>
              <option value="misconfiguration">Misconfigurations</option>
              <option value="compliance">Compliance</option>
            </select>
          </div>
        </div>
        <div className="overflow-x-auto">
          {loading ? (
            <div className="p-8 text-center">
              <p className="text-gray-500">Loading security issues...</p>
            </div>
          ) : filteredIssues.length > 0 ? (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Severity
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Resource
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Remediation
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredIssues.map((issue) => (
                  <tr key={issue.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getTypeClass(issue.type)}`}>
                        {issue.type.charAt(0).toUpperCase() + issue.type.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getSeverityClass(issue.severity)}`}>
                        {issue.severity.charAt(0).toUpperCase() + issue.severity.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {issue.resource}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {issue.description}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {issue.remediation}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-8 text-center">
              <p className="text-gray-500">No security issues found matching your filter.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SecurityScanner; 