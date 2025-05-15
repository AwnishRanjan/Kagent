import React from 'react';
import { NavLink } from 'react-router-dom';

const Sidebar = () => {
  // Define navigation items
  const navItems = [
    { to: '/', label: 'Dashboard', icon: '📊' },
    { to: '/predictor', label: 'Predictor', icon: '🔮' },
    { to: '/security', label: 'Security Scanner', icon: '🔒' },
    { to: '/cost', label: 'Cost Optimizer', icon: '💰' },
    { to: '/backup', label: 'Backup Manager', icon: '💾' },
    { to: '/remediator', label: 'Remediator', icon: '🔧' },
    { to: '/settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <aside className="w-64 bg-white border-r border-gray-200 h-screen sticky left-0 top-0 z-10">
      <div className="overflow-y-auto py-4 px-3 h-full">
        <div className="flex items-center mb-6 pl-2.5">
          <span className="self-center text-xl font-semibold text-primary">Kagent</span>
        </div>
        <ul className="space-y-2">
          {navItems.map((item, index) => (
            <li key={index}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center p-2 text-base font-normal rounded-lg ${
                    isActive
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-900 hover:bg-gray-100'
                  }`
                }
              >
                <span className="mr-3 text-xl">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
        <div className="pt-5 mt-5 border-t border-gray-200">
          <div className="px-3 py-4 rounded-lg bg-gray-50">
            <div className="text-sm font-medium text-gray-500 mb-2">Cluster Status</div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
              <span className="text-sm font-medium text-gray-900">Connected</span>
            </div>
            <div className="mt-2 text-xs text-gray-500">kagent-cluster</div>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar; 