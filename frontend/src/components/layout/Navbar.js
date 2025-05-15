import React from 'react';

const Navbar = () => {
  return (
    <nav className="bg-white border-b border-gray-200 px-4 py-2.5 w-full z-10">
      <div className="flex flex-wrap justify-end items-center">
        <div className="flex items-center space-x-3">
          <button 
            type="button" 
            className="px-3 py-1.5 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50"
          >
            Create Cluster
          </button>
          <div className="relative">
            <button 
              type="button" 
              className="flex items-center text-sm font-medium text-gray-700 rounded-full hover:text-blue-500 focus:outline-none"
            >
              <span className="mr-2">Admin</span>
              <img className="w-8 h-8 rounded-full" src="https://via.placeholder.com/32" alt="user avatar" />
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 