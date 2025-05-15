import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/layout/Navbar';
import Sidebar from './components/layout/Sidebar';
import Dashboard from './pages/Dashboard';
import PredictorAgent from './pages/PredictorAgent';
import SecurityScanner from './pages/SecurityScanner';
import CostOptimizer from './pages/CostOptimizer';
import BackupManager from './pages/BackupManager';
import RemediatorAgent from './pages/RemediatorAgent';
import Settings from './pages/Settings';

function App() {
  return (
    <Router>
      <div className="flex min-h-screen bg-gray-100">
        <Sidebar />
        <div className="flex flex-col flex-1">
          <Navbar />
          <main className="flex-1 overflow-y-auto bg-gray-50 p-4 pl-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/predictor" element={<PredictorAgent />} />
              <Route path="/security" element={<SecurityScanner />} />
              <Route path="/cost" element={<CostOptimizer />} />
              <Route path="/backup" element={<BackupManager />} />
              <Route path="/remediator" element={<RemediatorAgent />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App; 