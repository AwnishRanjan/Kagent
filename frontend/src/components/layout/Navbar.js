import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="bg-white border-b border-gray-200 px-4 py-2.5 fixed left-0 right-0 top-0 z-50">
      <div className="flex flex-wrap justify-between items-center">
        <div className="flex items-center">
          <Link to="/" className="flex items-center">
            <span className="self-center text-xl font-semibold whitespace-nowrap text-primary">Kagent</span>
          </Link>
        </div>
        <div className="flex items-center space-x-3">
          <button 
            type="button" 
            className="px-3 py-1.5 bg-primary text-white rounded hover:bg-primary-dark focus:outline-none focus:ring-2 focus:ring-primary focus:ring-opacity-50"
          >
            Create Cluster
          </button>
          <div className="relative">
            <button 
              type="button" 
              className="flex items-center text-sm font-medium text-gray-700 rounded-full hover:text-primary focus:outline-none"
            >
              <img className="w-8 h-8 rounded-full" src="https://via.placeholder.com/32" alt="user avatar" />
              <span className="ml-2">Admin</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 