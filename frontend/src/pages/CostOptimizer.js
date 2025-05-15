import React, { useState, useEffect } from 'react';

function CostOptimizer() {
  const [optimizations, setOptimizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savingsSummary, setSavingsSummary] = useState({
    current: 0,
    potential: 0,
    percentage: 0
  });

  useEffect(() => {
    // Simulate API call to fetch cost optimization data
    setTimeout(() => {
      const mockOptimizations = [
        {
          id: 1,
          resource: 'nginx-test-7f8bcbcf44-5zxkq',
          type: 'cpu',
          recommendation: 'Reduce CPU limit from 500m to 250m',
          currentCost: 15.40,
          potentialCost: 7.70,
          savings: 7.70,
          severity: 'high'
        },
        {
          id: 2,
          resource: 'prometheus-server-b88bf7978-pjl8g',
          type: 'memory',
          recommendation: 'Reduce memory request from 512Mi to 256Mi',
          currentCost: 12.80,
          potentialCost: 6.40,
          savings: 6.40,
          severity: 'medium'
        },
        {
          id: 3,
          resource: 'prometheus-alertmanager-0',
          type: 'pod',
          recommendation: 'Scale down replicas from 3 to 2',
          currentCost: 18.50,
          potentialCost: 12.33,
          savings: 6.17,
          severity: 'medium'
        },
        {
          id: 4,
          resource: 'kagent-cluster-worker2',
          type: 'node',
          recommendation: 'Consider downsizing node type',
          currentCost: 70.00,
          potentialCost: 50.00,
          savings: 20.00,
          severity: 'high'
        },
        {
          id: 5,
          resource: 'prometheus-kube-state-metrics-66858d7dfd-phczq',
          type: 'storage',
          recommendation: 'Use cheaper storage class for PVC',
          currentCost: 8.20,
          potentialCost: 4.10,
          savings: 4.10,
          severity: 'low'
        },
      ];
      
      const totalCurrent = mockOptimizations.reduce((sum, item) => sum + item.currentCost, 0);
      const totalPotential = mockOptimizations.reduce((sum, item) => sum + item.potentialCost, 0);
      const percentage = ((totalCurrent - totalPotential) / totalCurrent) * 100;
      
      setOptimizations(mockOptimizations);
      setSavingsSummary({
        current: totalCurrent,
        potential: totalPotential,
        percentage: percentage.toFixed(1)
      });
      setLoading(false);
    }, 1000);
  }, []);

  const getSeverityClass = (severity) => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-300';
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
      case 'cpu':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'memory':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case 'pod':
        return 'bg-teal-100 text-teal-800 border-teal-300';
      case 'node':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'storage':
        return 'bg-indigo-100 text-indigo-800 border-indigo-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Cost Optimizer</h1>
        <button className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
          Analyze Costs
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-700 mb-2">Current Monthly Cost</h2>
          <p className="text-3xl font-bold text-gray-900">${savingsSummary.current.toFixed(2)}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-700 mb-2">Potential Monthly Cost</h2>
          <p className="text-3xl font-bold text-green-600">${savingsSummary.potential.toFixed(2)}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-700 mb-2">Potential Savings</h2>
          <div className="flex items-end">
            <p className="text-3xl font-bold text-green-600">
              ${(savingsSummary.current - savingsSummary.potential).toFixed(2)}
            </p>
            <p className="ml-2 text-sm text-gray-500 mb-1">({savingsSummary.percentage}%)</p>
          </div>
        </div>
      </div>

      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">Cost Optimization Recommendations</h2>
        </div>
        <div className="overflow-x-auto">
          {loading ? (
            <div className="p-8 text-center">
              <p className="text-gray-500">Loading cost optimization data...</p>
            </div>
          ) : optimizations.length > 0 ? (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Resource
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Recommendation
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Current Cost
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Potential Cost
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Savings
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Priority
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {optimizations.map((optimization) => (
                  <tr key={optimization.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {optimization.resource}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getTypeClass(optimization.type)}`}>
                        {optimization.type.charAt(0).toUpperCase() + optimization.type.slice(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {optimization.recommendation}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      ${optimization.currentCost.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                      ${optimization.potentialCost.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">
                      ${optimization.savings.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getSeverityClass(optimization.severity)}`}>
                        {optimization.severity.charAt(0).toUpperCase() + optimization.severity.slice(1)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-8 text-center">
              <p className="text-gray-500">No cost optimization recommendations found.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CostOptimizer; 