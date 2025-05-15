import React, { useState, useEffect } from 'react';

function Settings() {
  const [settings, setSettings] = useState({
    // Predictor agent settings
    cpuUsageCritical: 90,
    cpuUsageWarning: 80,
    memoryUsageCritical: 90,
    memoryUsageWarning: 80,
    podRestartThreshold: 5,
    predictionWindow: 3600,
    
    // Security scanner settings
    scanInterval: 3600,
    enableVulnerabilityScans: true,
    enableComplianceScans: true,
    enableMisconfigScans: true,
    
    // Cost optimizer settings
    costAnalysisInterval: 86400,
    optimizationThreshold: 20,
    
    // Backup settings
    autoBackupEnabled: true,
    backupInterval: 86400,
    backupRetention: 7,
    
    // Remediator settings
    autoRemediateEnabled: false,
    autoRemediateHighCpu: true,
    autoRemediateHighMemory: true,
    autoRemediatePodRestarts: false,
    
    // System settings
    kubernetesApiUrl: 'https://kubernetes.default.svc',
    loggingLevel: 'info',
    telemetryEnabled: true,
    uiRefreshRate: 30
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('predictor');

  useEffect(() => {
    // Simulate API call to fetch settings
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings({
      ...settings,
      [name]: type === 'checkbox' ? checked : type === 'number' ? Number(value) : value
    });
  };

  const handleSave = () => {
    setSaving(true);
    // Simulate API call to save settings
    setTimeout(() => {
      setSaving(false);
      alert('Settings saved successfully!');
    }, 1000);
  };

  const renderPredictorSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Thresholds</h3>
        <p className="text-sm text-gray-500">Configure when alerts and remediations should be triggered.</p>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">CPU Usage Critical (%)</label>
            <input
              type="number"
              name="cpuUsageCritical"
              className="w-full p-2 border border-gray-300 rounded"
              value={settings.cpuUsageCritical}
              onChange={handleChange}
              min="1"
              max="100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">CPU Usage Warning (%)</label>
            <input
              type="number"
              name="cpuUsageWarning"
              className="w-full p-2 border border-gray-300 rounded"
              value={settings.cpuUsageWarning}
              onChange={handleChange}
              min="1"
              max="100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Memory Usage Critical (%)</label>
            <input
              type="number"
              name="memoryUsageCritical"
              className="w-full p-2 border border-gray-300 rounded"
              value={settings.memoryUsageCritical}
              onChange={handleChange}
              min="1"
              max="100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Memory Usage Warning (%)</label>
            <input
              type="number"
              name="memoryUsageWarning"
              className="w-full p-2 border border-gray-300 rounded"
              value={settings.memoryUsageWarning}
              onChange={handleChange}
              min="1"
              max="100"
            />
          </div>
        </div>
      </div>
      
      <div>
        <h3 className="text-lg font-medium text-gray-900">ML Prediction</h3>
        <p className="text-sm text-gray-500">Configure ML-based prediction settings.</p>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Pod Restart Threshold</label>
            <input
              type="number"
              name="podRestartThreshold"
              className="w-full p-2 border border-gray-300 rounded"
              value={settings.podRestartThreshold}
              onChange={handleChange}
              min="1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Prediction Window (seconds)</label>
            <input
              type="number"
              name="predictionWindow"
              className="w-full p-2 border border-gray-300 rounded"
              value={settings.predictionWindow}
              onChange={handleChange}
              min="300"
            />
          </div>
        </div>
      </div>
    </div>
  );

  const renderSecuritySettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Security Scanning</h3>
        <p className="text-sm text-gray-500">Configure security scanning settings.</p>
        <div className="mt-4 grid grid-cols-1 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Scan Interval (seconds)</label>
            <input
              type="number"
              name="scanInterval"
              className="w-full p-2 border border-gray-300 rounded"
              value={settings.scanInterval}
              onChange={handleChange}
              min="300"
            />
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              id="enableVulnerabilityScans"
              name="enableVulnerabilityScans"
              checked={settings.enableVulnerabilityScans}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="enableVulnerabilityScans" className="ml-2 block text-sm text-gray-900">
              Enable Vulnerability Scans
            </label>
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              id="enableComplianceScans"
              name="enableComplianceScans"
              checked={settings.enableComplianceScans}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="enableComplianceScans" className="ml-2 block text-sm text-gray-900">
              Enable Compliance Scans
            </label>
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              id="enableMisconfigScans"
              name="enableMisconfigScans"
              checked={settings.enableMisconfigScans}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="enableMisconfigScans" className="ml-2 block text-sm text-gray-900">
              Enable Misconfiguration Scans
            </label>
          </div>
        </div>
      </div>
    </div>
  );

  const renderCostSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Cost Optimization</h3>
        <p className="text-sm text-gray-500">Configure cost optimization settings.</p>
        <div className="mt-4 grid grid-cols-1 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cost Analysis Interval (seconds)</label>
            <input
              type="number"
              name="costAnalysisInterval"
              className="w-full p-2 border border-gray-300 rounded"
              value={settings.costAnalysisInterval}
              onChange={handleChange}
              min="3600"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Optimization Threshold (%)</label>
            <p className="text-xs text-gray-500">Minimum resource reduction to suggest an optimization</p>
            <input
              type="number"
              name="optimizationThreshold"
              className="w-full p-2 border border-gray-300 rounded"
              value={settings.optimizationThreshold}
              onChange={handleChange}
              min="5"
              max="50"
            />
          </div>
        </div>
      </div>
    </div>
  );

  const renderBackupSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Backup Configuration</h3>
        <p className="text-sm text-gray-500">Configure backup settings.</p>
        <div className="mt-4 grid grid-cols-1 gap-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="autoBackupEnabled"
              name="autoBackupEnabled"
              checked={settings.autoBackupEnabled}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="autoBackupEnabled" className="ml-2 block text-sm text-gray-900">
              Enable Automatic Backups
            </label>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Backup Interval (seconds)</label>
            <input
              type="number"
              name="backupInterval"
              className="w-full p-2 border border-gray-300 rounded"
              value={settings.backupInterval}
              onChange={handleChange}
              min="3600"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Backup Retention (days)</label>
            <input
              type="number"
              name="backupRetention"
              className="w-full p-2 border border-gray-300 rounded"
              value={settings.backupRetention}
              onChange={handleChange}
              min="1"
              max="90"
            />
          </div>
        </div>
      </div>
    </div>
  );

  const renderRemediatorSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Automatic Remediation</h3>
        <p className="text-sm text-gray-500">Configure remediation settings.</p>
        <div className="mt-4 grid grid-cols-1 gap-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="autoRemediateEnabled"
              name="autoRemediateEnabled"
              checked={settings.autoRemediateEnabled}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="autoRemediateEnabled" className="ml-2 block text-sm text-gray-900">
              Enable Automatic Remediation
            </label>
          </div>
          <div className="ml-6 space-y-2">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="autoRemediateHighCpu"
                name="autoRemediateHighCpu"
                checked={settings.autoRemediateHighCpu}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                disabled={!settings.autoRemediateEnabled}
              />
              <label htmlFor="autoRemediateHighCpu" className={`ml-2 block text-sm ${settings.autoRemediateEnabled ? 'text-gray-900' : 'text-gray-400'}`}>
                Auto-remediate High CPU Issues
              </label>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="autoRemediateHighMemory"
                name="autoRemediateHighMemory"
                checked={settings.autoRemediateHighMemory}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                disabled={!settings.autoRemediateEnabled}
              />
              <label htmlFor="autoRemediateHighMemory" className={`ml-2 block text-sm ${settings.autoRemediateEnabled ? 'text-gray-900' : 'text-gray-400'}`}>
                Auto-remediate High Memory Issues
              </label>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="autoRemediatePodRestarts"
                name="autoRemediatePodRestarts"
                checked={settings.autoRemediatePodRestarts}
                onChange={handleChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                disabled={!settings.autoRemediateEnabled}
              />
              <label htmlFor="autoRemediatePodRestarts" className={`ml-2 block text-sm ${settings.autoRemediateEnabled ? 'text-gray-900' : 'text-gray-400'}`}>
                Auto-remediate Pod Restart Issues
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderSystemSettings = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">System Configuration</h3>
        <p className="text-sm text-gray-500">Configure system-wide settings.</p>
        <div className="mt-4 grid grid-cols-1 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Kubernetes API URL</label>
            <input
              type="text"
              name="kubernetesApiUrl"
              className="w-full p-2 border border-gray-300 rounded"
              value={settings.kubernetesApiUrl}
              onChange={handleChange}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Logging Level</label>
            <select
              name="loggingLevel"
              className="w-full p-2 border border-gray-300 rounded"
              value={settings.loggingLevel}
              onChange={handleChange}
            >
              <option value="debug">Debug</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              id="telemetryEnabled"
              name="telemetryEnabled"
              checked={settings.telemetryEnabled}
              onChange={handleChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="telemetryEnabled" className="ml-2 block text-sm text-gray-900">
              Enable Telemetry
            </label>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">UI Refresh Rate (seconds)</label>
            <input
              type="number"
              name="uiRefreshRate"
              className="w-full p-2 border border-gray-300 rounded"
              value={settings.uiRefreshRate}
              onChange={handleChange}
              min="5"
              max="300"
            />
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Settings</h1>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <p className="text-gray-500">Loading settings...</p>
        </div>
      ) : (
        <div className="bg-white shadow-md rounded-lg overflow-hidden">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex overflow-x-auto">
              <button
                className={`py-4 px-6 font-medium text-sm border-b-2 focus:outline-none whitespace-nowrap ${
                  activeTab === 'predictor'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
                onClick={() => setActiveTab('predictor')}
              >
                Predictor Settings
              </button>
              <button
                className={`py-4 px-6 font-medium text-sm border-b-2 focus:outline-none whitespace-nowrap ${
                  activeTab === 'security'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
                onClick={() => setActiveTab('security')}
              >
                Security Settings
              </button>
              <button
                className={`py-4 px-6 font-medium text-sm border-b-2 focus:outline-none whitespace-nowrap ${
                  activeTab === 'cost'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
                onClick={() => setActiveTab('cost')}
              >
                Cost Settings
              </button>
              <button
                className={`py-4 px-6 font-medium text-sm border-b-2 focus:outline-none whitespace-nowrap ${
                  activeTab === 'backup'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
                onClick={() => setActiveTab('backup')}
              >
                Backup Settings
              </button>
              <button
                className={`py-4 px-6 font-medium text-sm border-b-2 focus:outline-none whitespace-nowrap ${
                  activeTab === 'remediator'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
                onClick={() => setActiveTab('remediator')}
              >
                Remediator Settings
              </button>
              <button
                className={`py-4 px-6 font-medium text-sm border-b-2 focus:outline-none whitespace-nowrap ${
                  activeTab === 'system'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
                onClick={() => setActiveTab('system')}
              >
                System Settings
              </button>
            </nav>
          </div>
          <div className="p-6">
            {activeTab === 'predictor' && renderPredictorSettings()}
            {activeTab === 'security' && renderSecuritySettings()}
            {activeTab === 'cost' && renderCostSettings()}
            {activeTab === 'backup' && renderBackupSettings()}
            {activeTab === 'remediator' && renderRemediatorSettings()}
            {activeTab === 'system' && renderSystemSettings()}
            
            <div className="mt-8 flex justify-end">
              <button
                className="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-4 rounded mr-2"
                onClick={() => window.location.reload()}
              >
                Reset
              </button>
              <button
                className={`bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Settings'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Settings; 