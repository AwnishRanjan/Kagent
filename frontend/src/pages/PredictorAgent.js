import React, { useState, useEffect } from 'react';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import predictorService from '../api/predictorService';

const PredictorAgent = () => {
  // State for data
  const [metrics, setMetrics] = useState(null);
  const [predictions, setPredictions] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  
  // Loading and error states
  const [loading, setLoading] = useState({
    metrics: true,
    predictions: true,
    modelInfo: true
  });
  const [error, setError] = useState({
    metrics: null,
    predictions: null,
    modelInfo: null
  });
  
  const [activeTab, setActiveTab] = useState('issues');

  // Fetch metrics data
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(prev => ({ ...prev, metrics: true }));
        const data = await predictorService.getMetrics();
        setMetrics(data);
        setError(prev => ({ ...prev, metrics: null }));
      } catch (err) {
        console.error('Error fetching metrics:', err);
        setError(prev => ({ ...prev, metrics: 'Failed to load metrics data' }));
      } finally {
        setLoading(prev => ({ ...prev, metrics: false }));
      }
    };

    fetchMetrics();
    
    // Refresh metrics every 30 seconds
    const intervalId = setInterval(fetchMetrics, 30000);
    
    // Clean up on unmount
    return () => clearInterval(intervalId);
  }, []);

  // Fetch predictions data
  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        setLoading(prev => ({ ...prev, predictions: true }));
        const data = await predictorService.getPredictions();
        setPredictions(data);
        setError(prev => ({ ...prev, predictions: null }));
      } catch (err) {
        console.error('Error fetching predictions:', err);
        setError(prev => ({ ...prev, predictions: 'Failed to load prediction data' }));
      } finally {
        setLoading(prev => ({ ...prev, predictions: false }));
      }
    };

    fetchPredictions();
  }, []);

  // Fetch model info
  useEffect(() => {
    const fetchModelInfo = async () => {
      try {
        setLoading(prev => ({ ...prev, modelInfo: true }));
        const data = await predictorService.getModelInfo();
        setModelInfo(data);
        setError(prev => ({ ...prev, modelInfo: null }));
      } catch (err) {
        console.error('Error fetching model info:', err);
        setError(prev => ({ ...prev, modelInfo: 'Failed to load model information' }));
      } finally {
        setLoading(prev => ({ ...prev, modelInfo: false }));
      }
    };

    fetchModelInfo();
  }, []);

  // Function to refresh data
  const refreshData = async () => {
    try {
      setLoading({
        metrics: true,
        predictions: true,
        modelInfo: true
      });
      
      const [metricsData, predictionsData, modelInfoData] = await Promise.all([
        predictorService.getMetrics(),
        predictorService.getPredictions(),
        predictorService.getModelInfo()
      ]);
      
      setMetrics(metricsData);
      setPredictions(predictionsData);
      setModelInfo(modelInfoData);
      
      setError({
        metrics: null,
        predictions: null,
        modelInfo: null
      });
    } catch (err) {
      console.error('Error refreshing data:', err);
    } finally {
      setLoading({
        metrics: false,
        predictions: false,
        modelInfo: false
      });
    }
  };

  // Function to train the model
  const trainModel = async () => {
    try {
      const params = {
        timespan: document.getElementById('training-timespan').value,
        model_type: document.getElementById('model-type').value
      };
      
      const result = await predictorService.trainModel(params);
      alert(`Model training started. Job ID: ${result.job_id}`);
      
      // Refresh model info after a delay to allow training to complete
      setTimeout(async () => {
        const updatedModelInfo = await predictorService.getModelInfo();
        setModelInfo(updatedModelInfo);
      }, 5000);
    } catch (err) {
      console.error('Error training model:', err);
      alert('Failed to start model training');
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'danger';
      case 'warning': return 'warning';
      case 'info': return 'primary';
      default: return 'default';
    }
  };

  // Loading state UI
  if (loading.metrics && loading.predictions && loading.modelInfo) {
    return (
      <div className="pt-16 pl-64">
        <div className="px-4 py-4">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-semibold text-gray-900">ML Predictor Agent</h1>
          </div>
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-gray-600">Loading data...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="pt-16 pl-64">
      <div className="px-4 py-4">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold text-gray-900">ML Predictor Agent</h1>
          <div>
            <Button variant="outline" className="mr-2" onClick={refreshData}>
              {loading.metrics || loading.predictions ? 'Refreshing...' : 'Refresh Data'}
            </Button>
            <Button variant="primary">Run Prediction</Button>
          </div>
        </div>

        {/* Error Messages */}
        {(error.metrics || error.predictions || error.modelInfo) && (
          <div className="mb-6 p-4 bg-danger-light text-danger-dark rounded-lg">
            <h3 className="font-medium mb-2">Error Loading Data</h3>
            <ul className="list-disc list-inside">
              {error.metrics && <li>{error.metrics}</li>}
              {error.predictions && <li>{error.predictions}</li>}
              {error.modelInfo && <li>{error.modelInfo}</li>}
            </ul>
          </div>
        )}

        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              <button
                onClick={() => setActiveTab('issues')}
                className={`${
                  activeTab === 'issues'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm`}
              >
                Issues {predictions?.issues ? `(${predictions.issues.length})` : ''}
              </button>
              <button
                onClick={() => setActiveTab('metrics')}
                className={`${
                  activeTab === 'metrics'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm`}
              >
                Current Metrics
              </button>
              <button
                onClick={() => setActiveTab('model')}
                className={`${
                  activeTab === 'model'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm`}
              >
                ML Model
              </button>
            </nav>
          </div>
        </div>

        {/* Tab content */}
        {activeTab === 'issues' && predictions && (
          <>
            {/* Prediction Summary */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <Card className="col-span-4">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Prediction Summary</h3>
                  <Badge variant="primary">
                    {`Confidence: ${Math.round(predictions.confidence * 100)}%`}
                  </Badge>
                </div>
                <div className="grid grid-cols-4 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-500 mb-1">Issues Detected</h4>
                    <p className="text-2xl font-bold text-gray-900">{predictions.issues.length}</p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-500 mb-1">Critical Issues</h4>
                    <p className="text-2xl font-bold text-danger">
                      {predictions.issues.filter(i => i.severity === 'critical').length}
                    </p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-500 mb-1">Warning Issues</h4>
                    <p className="text-2xl font-bold text-warning">
                      {predictions.issues.filter(i => i.severity === 'warning').length}
                    </p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-500 mb-1">Remediation Options</h4>
                    <p className="text-2xl font-bold text-primary">{predictions.remediation_suggestions.length}</p>
                  </div>
                </div>
              </Card>
            </div>

            {/* Issues List */}
            <Card className="mb-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Detected Issues</h3>
                <Button variant="outline" size="sm">Remediate All</Button>
              </div>
              {loading.predictions && (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              )}
              {!loading.predictions && predictions.issues.length === 0 && (
                <div className="py-8 text-center">
                  <p className="text-gray-500">No issues detected</p>
                </div>
              )}
              {!loading.predictions && predictions.issues.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Issue Type
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Component
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Severity
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Description
                        </th>
                        <th scope="col" className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {predictions.issues.map((issue) => (
                        <tr key={issue.id}>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <span className="text-sm font-medium text-gray-900">
                              {issue.type.replace(/_/g, ' ')}
                            </span>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <span className="text-sm text-gray-900">{issue.component}</span>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <Badge 
                              variant={getSeverityColor(issue.severity)} 
                              size="sm"
                            >
                              {issue.severity}
                            </Badge>
                          </td>
                          <td className="px-4 py-3">
                            <span className="text-sm text-gray-900">{issue.description}</span>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-right">
                            <Button variant="success" size="sm" className="mr-2">Remediate</Button>
                            <Button variant="outline" size="sm">Ignore</Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>

            {/* Remediation Suggestions */}
            <Card>
              <div className="mb-4">
                <h3 className="text-lg font-medium text-gray-900">Remediation Suggestions</h3>
                <p className="text-sm text-gray-500 mt-1">
                  The following actions are recommended to address the detected issues
                </p>
              </div>
              {loading.predictions && (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              )}
              {!loading.predictions && predictions.remediation_suggestions.length === 0 && (
                <div className="py-8 text-center">
                  <p className="text-gray-500">No remediation suggestions available</p>
                </div>
              )}
              {!loading.predictions && predictions.remediation_suggestions.length > 0 && (
                <div className="space-y-4">
                  {predictions.remediation_suggestions.map((suggestion) => (
                    <div key={suggestion.id} className="p-4 bg-gray-50 rounded-lg">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="text-md font-medium text-gray-900 mb-1">{suggestion.description}</h4>
                          <p className="text-sm text-gray-500 mb-2">
                            For component: <span className="font-medium">{suggestion.component}</span>
                          </p>
                          <div className="mt-3">
                            <h5 className="text-sm font-medium text-gray-900 mb-1">Steps:</h5>
                            <ul className="list-disc list-inside text-sm text-gray-600 ml-2">
                              {suggestion.steps.map((step, idx) => (
                                <li key={idx}>{step}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                        <Button variant="primary" size="sm">Apply</Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </>
        )}

        {activeTab === 'metrics' && metrics && (
          <>
            {/* Node Metrics */}
            <Card className="mb-6">
              <div className="mb-4">
                <h3 className="text-lg font-medium text-gray-900">Node Metrics</h3>
                <p className="text-sm text-gray-500 mt-1">
                  Current performance metrics for all cluster nodes
                </p>
              </div>
              {loading.metrics && (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              )}
              {!loading.metrics && Object.keys(metrics.nodes).length === 0 && (
                <div className="py-8 text-center">
                  <p className="text-gray-500">No node metrics available</p>
                </div>
              )}
              {!loading.metrics && Object.keys(metrics.nodes).length > 0 && (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Node Name
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          CPU Usage
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Memory Usage
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Network I/O
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Pressure
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {Object.entries(metrics.nodes).map(([nodeName, nodeData]) => (
                        <tr key={nodeName}>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <span className="text-sm font-medium text-gray-900">{nodeName}</span>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <Badge 
                              variant={nodeData.status === 'Ready' ? 'success' : 'warning'} 
                              size="sm"
                            >
                              {nodeData.status}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="w-full bg-gray-200 rounded-full h-2.5 mr-2">
                                <div 
                                  className={`h-2.5 rounded-full ${nodeData.cpu_usage > 80 ? 'bg-danger' : nodeData.cpu_usage > 60 ? 'bg-warning' : 'bg-success'}`} 
                                  style={{ width: `${nodeData.cpu_usage}%` }}
                                ></div>
                              </div>
                              <span className="text-sm text-gray-900">{nodeData.cpu_usage}%</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="w-full bg-gray-200 rounded-full h-2.5 mr-2">
                                <div 
                                  className={`h-2.5 rounded-full ${nodeData.memory_usage > 80 ? 'bg-danger' : nodeData.memory_usage > 60 ? 'bg-warning' : 'bg-success'}`} 
                                  style={{ width: `${nodeData.memory_usage}%` }}
                                ></div>
                              </div>
                              <span className="text-sm text-gray-900">{nodeData.memory_usage}%</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <span className="text-sm text-gray-900">
                              {`In: ${nodeData.network_io.in / 1000}KB/s, Out: ${nodeData.network_io.out / 1000}KB/s`}
                            </span>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <div className="flex space-x-1">
                              {nodeData.disk_pressure && <Badge variant="danger" size="sm">Disk</Badge>}
                              {nodeData.memory_pressure && <Badge variant="danger" size="sm">Memory</Badge>}
                              {nodeData.pid_pressure && <Badge variant="danger" size="sm">PID</Badge>}
                              {!nodeData.disk_pressure && !nodeData.memory_pressure && !nodeData.pid_pressure && 
                                <span className="text-sm text-gray-500">None</span>
                              }
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          
            {/* Pod Metrics */}
            <Card>
              <div className="mb-4">
                <h3 className="text-lg font-medium text-gray-900">Pod Metrics</h3>
                <p className="text-sm text-gray-500 mt-1">
                  Current performance metrics for all pods
                </p>
              </div>
              {loading.metrics && (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              )}
              {!loading.metrics && Object.keys(metrics.pods).length === 0 && (
                <div className="py-8 text-center">
                  <p className="text-gray-500">No pod metrics available</p>
                </div>
              )}
              {!loading.metrics && Object.keys(metrics.pods).length > 0 && (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Pod Name
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          CPU Usage
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Memory Usage
                        </th>
                        <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Restarts
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {Object.entries(metrics.pods).map(([podName, podData]) => (
                        <tr key={podName}>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <span className="text-sm font-medium text-gray-900">{podName}</span>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <Badge 
                              variant={podData.status === 'Running' ? 'success' : 'warning'} 
                              size="sm"
                            >
                              {podData.status}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="w-full bg-gray-200 rounded-full h-2.5 mr-2">
                                <div 
                                  className={`h-2.5 rounded-full ${podData.cpu_usage > 80 ? 'bg-danger' : podData.cpu_usage > 60 ? 'bg-warning' : 'bg-success'}`} 
                                  style={{ width: `${podData.cpu_usage}%` }}
                                ></div>
                              </div>
                              <span className="text-sm text-gray-900">{podData.cpu_usage}%</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="w-full bg-gray-200 rounded-full h-2.5 mr-2">
                                <div 
                                  className={`h-2.5 rounded-full ${podData.memory_usage > 80 ? 'bg-danger' : podData.memory_usage > 60 ? 'bg-warning' : 'bg-success'}`} 
                                  style={{ width: `${podData.memory_usage}%` }}
                                ></div>
                              </div>
                              <span className="text-sm text-gray-900">{podData.memory_usage}%</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <span className={`text-sm ${podData.restarts > 0 ? 'text-warning font-medium' : 'text-gray-900'}`}>
                              {podData.restarts}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </>
        )}

        {activeTab === 'model' && modelInfo && (
          <>
            {/* ML Model Information */}
            <div className="grid grid-cols-3 gap-6">
              <Card className="col-span-2">
                <div className="mb-4">
                  <h3 className="text-lg font-medium text-gray-900">ML Model Information</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Details about the currently used machine learning model
                  </p>
                </div>
                
                {loading.modelInfo && (
                  <div className="flex justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                )}
                
                {!loading.modelInfo && (
                  <>
                    <div className="grid grid-cols-2 gap-4 mb-6">
                      <div>
                        <h4 className="text-sm font-medium text-gray-500 mb-1">Model Name</h4>
                        <p className="text-base text-gray-900">{modelInfo.name}</p>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-500 mb-1">Version</h4>
                        <p className="text-base text-gray-900">{modelInfo.version}</p>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-500 mb-1">Trained At</h4>
                        <p className="text-base text-gray-900">
                          {new Date(modelInfo.trained_at).toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-500 mb-1">Accuracy</h4>
                        <p className="text-base text-gray-900">{modelInfo.accuracy * 100}%</p>
                      </div>
                    </div>
                    
                    <div className="mb-6">
                      <h4 className="text-sm font-medium text-gray-500 mb-2">Features Used</h4>
                      <div className="flex flex-wrap gap-2">
                        {modelInfo.features.map((feature, idx) => (
                          <Badge key={idx} variant="primary" size="md">
                            {feature.replace(/_/g, ' ')}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="text-sm font-medium text-gray-500 mb-2">Model Parameters</h4>
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <pre className="text-xs text-gray-700">
                          {JSON.stringify(modelInfo.parameters, null, 2)}
                        </pre>
                      </div>
                    </div>
                  </>
                )}
              </Card>
              
              <Card>
                <div className="mb-4">
                  <h3 className="text-lg font-medium text-gray-900">ML Training</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Train or update the prediction model
                  </p>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Training Data Timespan
                    </label>
                    <select 
                      id="training-timespan"
                      className="w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50"
                    >
                      <option value="7d">Last 7 Days</option>
                      <option value="14d">Last 14 Days</option>
                      <option value="30d">Last 30 Days</option>
                      <option value="90d">Last 90 Days</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Model Type
                    </label>
                    <select 
                      id="model-type"
                      className="w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50"
                    >
                      <option value="isolation_forest">Isolation Forest</option>
                      <option value="one_class_svm">One-Class SVM</option>
                      <option value="local_outlier_factor">Local Outlier Factor</option>
                    </select>
                  </div>
                  
                  <div className="pt-4">
                    <Button variant="primary" className="w-full" onClick={trainModel}>
                      Train New Model
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default PredictorAgent; 