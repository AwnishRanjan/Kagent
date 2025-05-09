import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import predictorService from '../api/predictorService';
import securityService from '../api/securityService';
import costService from '../api/costService';
import backupService from '../api/backupService';
import remediatorService from '../api/remediatorService';

const Dashboard = () => {
  // State for data
  const [clusterStatus, setClusterStatus] = useState(null);
  const [issues, setIssues] = useState([]);
  const [securityIssues, setSecurityIssues] = useState(null);
  const [costOptimization, setCostOptimization] = useState(null);
  const [backupStatus, setBackupStatus] = useState(null);
  
  // Loading and error states
  const [loading, setLoading] = useState({
    cluster: true,
    issues: true,
    security: true,
    cost: true,
    backup: true
  });
  
  const [error, setError] = useState({
    cluster: null,
    issues: null,
    security: null,
    cost: null,
    backup: null
  });

  // Fetch cluster status (we'll use metrics for this)
  useEffect(() => {
    const fetchClusterStatus = async () => {
      try {
        setLoading(prev => ({ ...prev, cluster: true }));
        const metrics = await predictorService.getMetrics();
        
        // Convert metrics to cluster status format
        const nodes = Object.keys(metrics.nodes).length;
        const pods = Object.keys(metrics.pods).length;
        
        // Calculate average CPU and memory usage
        let totalCpu = 0;
        let totalMemory = 0;
        
        Object.values(metrics.nodes).forEach(node => {
          totalCpu += node.cpu_usage;
          totalMemory += node.memory_usage;
        });
        
        const cpuUsage = Math.round(totalCpu / nodes);
        const memoryUsage = Math.round(totalMemory / nodes);
        
        // Format uptime (mock for now)
        const uptime = "2d 5h";
        
        setClusterStatus({
          status: 'running',
          name: 'kagent-cluster',
          nodes,
          pods,
          cpuUsage,
          memoryUsage,
          uptime
        });
        
        setError(prev => ({ ...prev, cluster: null }));
      } catch (err) {
        console.error('Error fetching cluster status:', err);
        setError(prev => ({ ...prev, cluster: 'Failed to load cluster status' }));
      } finally {
        setLoading(prev => ({ ...prev, cluster: false }));
      }
    };

    fetchClusterStatus();
  }, []);

  // Fetch issues (from predictor service)
  useEffect(() => {
    const fetchIssues = async () => {
      try {
        setLoading(prev => ({ ...prev, issues: true }));
        const predictions = await predictorService.getPredictions();
        
        // Extract and format issues from predictions
        const formattedIssues = predictions.issues.map(issue => ({
          id: issue.id,
          type: issue.type,
          component: issue.component,
          severity: issue.severity,
          timestamp: issue.timestamp
        }));
        
        setIssues(formattedIssues);
        setError(prev => ({ ...prev, issues: null }));
      } catch (err) {
        console.error('Error fetching issues:', err);
        setError(prev => ({ ...prev, issues: 'Failed to load issues' }));
      } finally {
        setLoading(prev => ({ ...prev, issues: false }));
      }
    };

    fetchIssues();
  }, []);

  // Fetch security issues
  useEffect(() => {
    const fetchSecurityIssues = async () => {
      try {
        setLoading(prev => ({ ...prev, security: true }));
        const securityData = await securityService.getScanResults();
        
        setSecurityIssues({
          vulnerabilities: securityData.vulnerabilities || 0,
          misconfigurations: securityData.misconfigurations || 0,
          compliance: securityData.compliance_issues || 0
        });
        
        setError(prev => ({ ...prev, security: null }));
      } catch (err) {
        console.error('Error fetching security issues:', err);
        setError(prev => ({ ...prev, security: 'Failed to load security data' }));
      } finally {
        setLoading(prev => ({ ...prev, security: false }));
      }
    };

    fetchSecurityIssues();
  }, []);

  // Fetch cost optimization
  useEffect(() => {
    const fetchCostOptimization = async () => {
      try {
        setLoading(prev => ({ ...prev, cost: true }));
        const costData = await costService.getCostAnalysis();
        
        setCostOptimization({
          monthlyCost: costData.monthlyCost || 0,
          potentialSavings: costData.potentialSavings || 0,
          efficiency: costData.efficiency || 0
        });
        
        setError(prev => ({ ...prev, cost: null }));
      } catch (err) {
        console.error('Error fetching cost optimization:', err);
        setError(prev => ({ ...prev, cost: 'Failed to load cost data' }));
      } finally {
        setLoading(prev => ({ ...prev, cost: false }));
      }
    };

    fetchCostOptimization();
  }, []);

  // Fetch backup status
  useEffect(() => {
    const fetchBackupStatus = async () => {
      try {
        setLoading(prev => ({ ...prev, backup: true }));
        
        // We need to make multiple API calls to get backup status
        const [backups, schedule] = await Promise.all([
          backupService.getBackups(),
          backupService.getBackupSchedule().catch(() => ({ enabled: false }))
        ]);
        
        const lastBackupTime = backups && backups.length > 0 
          ? new Date(backups[0].timestamp).getTime()
          : Date.now() - 86400000; // Default to 1 day ago
        
        setBackupStatus({
          lastBackup: lastBackupTime,
          totalBackups: backups ? backups.length : 0,
          scheduled: schedule ? schedule.enabled : false,
          nextBackup: schedule && schedule.nextBackup 
            ? new Date(schedule.nextBackup).getTime()
            : Date.now() + 3600000 // Default to 1 hour from now
        });
        
        setError(prev => ({ ...prev, backup: null }));
      } catch (err) {
        console.error('Error fetching backup status:', err);
        setError(prev => ({ ...prev, backup: 'Failed to load backup data' }));
      } finally {
        setLoading(prev => ({ ...prev, backup: false }));
      }
    };

    fetchBackupStatus();
  }, []);

  // Function to format time ago from timestamp
  const formatTimeAgo = (timestamp) => {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    
    if (seconds < 60) return `${seconds} seconds ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    return `${Math.floor(seconds / 86400)} days ago`;
  };

  // Function to run security scan
  const runSecurityScan = async () => {
    try {
      await securityService.startScan();
      alert('Security scan started successfully.');
    } catch (err) {
      console.error('Error starting security scan:', err);
      alert('Failed to start security scan.');
    }
  };

  // Function to create backup
  const createBackup = async () => {
    try {
      const result = await backupService.createBackup({
        name: `manual-backup-${new Date().toISOString().split('T')[0]}`
      });
      alert(`Backup started successfully. ID: ${result.id}`);
    } catch (err) {
      console.error('Error creating backup:', err);
      alert('Failed to create backup.');
    }
  };

  // Function to train model
  const trainModel = async () => {
    try {
      const result = await predictorService.trainModel({
        timespan: '7d',
        model_type: 'isolation_forest'
      });
      alert(`Model training started. Job ID: ${result.job_id}`);
    } catch (err) {
      console.error('Error training model:', err);
      alert('Failed to start model training.');
    }
  };

  // Function to view optimizations
  const viewOptimizations = () => {
    window.location.href = '/cost';
  };

  // Full page loading state
  if (loading.cluster && loading.issues && loading.security && loading.cost && loading.backup) {
    return (
      <div className="pt-16 pl-64">
        <div className="px-4 py-4">
          <h1 className="text-2xl font-semibold text-gray-900 mb-6">Dashboard</h1>
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-gray-600">Loading dashboard data...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="pt-16 pl-64">
      <div className="px-4 py-4">
        <h1 className="text-2xl font-semibold text-gray-900 mb-6">Dashboard</h1>
        
        {/* Error Messages */}
        {(error.cluster || error.issues || error.security || error.cost || error.backup) && (
          <div className="mb-6 p-4 bg-danger-light text-danger-dark rounded-lg">
            <h3 className="font-medium mb-2">Error Loading Data</h3>
            <ul className="list-disc list-inside">
              {error.cluster && <li>{error.cluster}</li>}
              {error.issues && <li>{error.issues}</li>}
              {error.security && <li>{error.security}</li>}
              {error.cost && <li>{error.cost}</li>}
              {error.backup && <li>{error.backup}</li>}
            </ul>
          </div>
        )}
        
        {/* Cluster Overview */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <Card className="col-span-2 flex flex-col">
            {loading.cluster ? (
              <div className="flex justify-center items-center h-40">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : clusterStatus && (
              <>
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-lg font-medium text-gray-900">Cluster Overview</h3>
                  <Badge 
                    variant={clusterStatus.status === 'running' ? 'success' : 'warning'}
                  >
                    {clusterStatus.status}
                  </Badge>
                </div>
                <div className="flex-1">
                  <div className="grid grid-cols-2 gap-4 mb-2">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Cluster Name</p>
                      <p className="text-base text-gray-900">{clusterStatus.name}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-500">Uptime</p>
                      <p className="text-base text-gray-900">{clusterStatus.uptime}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-500">Nodes</p>
                      <p className="text-base text-gray-900">{clusterStatus.nodes}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-500">Pods</p>
                      <p className="text-base text-gray-900">{clusterStatus.pods}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-500">CPU Usage</p>
                      <p className="text-base text-gray-900">{clusterStatus.cpuUsage}%</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-500">Memory</p>
                      <p className="text-base text-gray-900">{clusterStatus.memoryUsage}%</p>
                    </div>
                  </div>
                </div>
                <div className="mt-4">
                  <Button variant="outline" size="sm">View Details</Button>
                </div>
              </>
            )}
          </Card>
          
          {/* Predictor Status */}
          <Card>
            {loading.issues ? (
              <div className="flex justify-center items-center h-40">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : (
              <>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">ML Predictor</h3>
                  <Badge variant="primary">Active</Badge>
                </div>
                <div className="mb-4">
                  <div className="flex justify-between items-center">
                    <p className="text-sm font-medium text-gray-500">Detected Issues</p>
                    <span className="text-lg font-semibold text-gray-900">{issues.length}</span>
                  </div>
                  <div className="flex justify-between items-center mt-2">
                    <p className="text-sm font-medium text-gray-500">Model Confidence</p>
                    <span className="text-lg font-semibold text-gray-900">87%</span>
                  </div>
                </div>
                <div className="mt-4">
                  <Link to="/predictor">
                    <Button variant="primary" size="sm" className="w-full">View Predictions</Button>
                  </Link>
                </div>
              </>
            )}
          </Card>
          
          {/* Security Status */}
          <Card>
            {loading.security ? (
              <div className="flex justify-center items-center h-40">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : securityIssues && (
              <>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Security Status</h3>
                  <Badge 
                    variant={securityIssues.vulnerabilities > 0 ? 'warning' : 'success'}
                  >
                    {securityIssues.vulnerabilities > 0 ? 'Issues Found' : 'Secure'}
                  </Badge>
                </div>
                <div className="mb-4">
                  <div className="flex justify-between items-center">
                    <p className="text-sm font-medium text-gray-500">Vulnerabilities</p>
                    <span className="text-lg font-semibold text-danger">{securityIssues.vulnerabilities}</span>
                  </div>
                  <div className="flex justify-between items-center mt-2">
                    <p className="text-sm font-medium text-gray-500">Misconfigurations</p>
                    <span className="text-lg font-semibold text-warning">{securityIssues.misconfigurations}</span>
                  </div>
                </div>
                <div className="mt-4">
                  <Link to="/security">
                    <Button variant="primary" size="sm" className="w-full">View Security</Button>
                  </Link>
                </div>
              </>
            )}
          </Card>
        </div>
        
        {/* Issues List */}
        <Card className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">Active Issues</h3>
            <Button variant="outline" size="sm">Remediate All</Button>
          </div>
          {loading.issues ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : issues.length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-gray-500">No active issues detected</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Component
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Severity
                    </th>
                    <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Detected
                    </th>
                    <th scope="col" className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {issues.map((issue) => (
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
                          variant={issue.severity === 'critical' ? 'danger' : 'warning'} 
                          size="sm"
                        >
                          {issue.severity}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="text-sm text-gray-500">{formatTimeAgo(issue.timestamp)}</span>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-right">
                        <Button variant="outline" size="sm">Remediate</Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="mt-4 text-center">
            <Link to="/remediator" className="text-sm text-primary hover:text-primary-dark">
              View all issues
            </Link>
          </div>
        </Card>
        
        {/* Bottom Row */}
        <div className="grid grid-cols-3 gap-4">
          {/* Cost Optimization */}
          <Card>
            {loading.cost ? (
              <div className="flex justify-center items-center h-40">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : costOptimization && (
              <>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Cost Optimization</h3>
                </div>
                <div className="mb-4">
                  <div className="flex justify-between items-center mb-1">
                    <p className="text-sm font-medium text-gray-500">Monthly Cost</p>
                    <span className="text-lg font-semibold text-gray-900">${costOptimization.monthlyCost}</span>
                  </div>
                  <div className="flex justify-between items-center mb-1">
                    <p className="text-sm font-medium text-gray-500">Potential Savings</p>
                    <span className="text-lg font-semibold text-success">${costOptimization.potentialSavings}</span>
                  </div>
                  <div className="flex justify-between items-center mb-1">
                    <p className="text-sm font-medium text-gray-500">Resource Efficiency</p>
                    <span className="text-lg font-semibold text-primary">{costOptimization.efficiency}%</span>
                  </div>
                </div>
                <div className="mt-4">
                  <Link to="/cost">
                    <Button variant="primary" size="sm" className="w-full">Optimize Costs</Button>
                  </Link>
                </div>
              </>
            )}
          </Card>
          
          {/* Backup Status */}
          <Card>
            {loading.backup ? (
              <div className="flex justify-center items-center h-40">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : backupStatus && (
              <>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Backup Status</h3>
                  <Badge variant={backupStatus.scheduled ? 'success' : 'warning'}>
                    {backupStatus.scheduled ? 'Auto Backup On' : 'Auto Backup Off'}
                  </Badge>
                </div>
                <div className="mb-4">
                  <div className="flex justify-between items-center mb-1">
                    <p className="text-sm font-medium text-gray-500">Last Backup</p>
                    <span className="text-sm text-gray-900">{formatTimeAgo(backupStatus.lastBackup)}</span>
                  </div>
                  <div className="flex justify-between items-center mb-1">
                    <p className="text-sm font-medium text-gray-500">Total Backups</p>
                    <span className="text-sm text-gray-900">{backupStatus.totalBackups}</span>
                  </div>
                  <div className="flex justify-between items-center mb-1">
                    <p className="text-sm font-medium text-gray-500">Next Scheduled</p>
                    <span className="text-sm text-gray-900">{formatTimeAgo(backupStatus.nextBackup).replace('ago', 'from now')}</span>
                  </div>
                </div>
                <div className="mt-4">
                  <Link to="/backup">
                    <Button variant="primary" size="sm" className="w-full">Manage Backups</Button>
                  </Link>
                </div>
              </>
            )}
          </Card>
          
          {/* Quick Actions */}
          <Card>
            <div className="mb-4">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-2">
                <Button variant="primary" className="w-full" onClick={runSecurityScan}>Run Security Scan</Button>
                <Button variant="success" className="w-full" onClick={createBackup}>Create Backup</Button>
                <Button variant="outline" className="w-full" onClick={trainModel}>Train ML Model</Button>
                <Button variant="warning" className="w-full" onClick={viewOptimizations}>View Optimizations</Button>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;