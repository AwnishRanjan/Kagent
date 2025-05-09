import React from 'react';

const Card = ({ title, children, className = '', titleClassName = '', bodyClassName = '' }) => {
  return (
    <div className={`bg-white shadow rounded-lg overflow-hidden ${className}`}>
      {title && (
        <div className={`px-4 py-3 border-b border-gray-200 bg-gray-50 ${titleClassName}`}>
          <h3 className="text-lg font-medium text-gray-900">{title}</h3>
        </div>
      )}
      <div className={`px-4 py-4 ${bodyClassName}`}>{children}</div>
    </div>
  );
};

export default Card; 