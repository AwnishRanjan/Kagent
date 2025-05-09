# Kagent Frontend

A modern React-based frontend for Kagent, a Kubernetes AI management platform.

## Features

- **Dashboard**: Overview of cluster health, detected issues, and key metrics
- **ML Predictor**: Visualize predictions, metrics, and machine learning models
- **Security Scanner**: Identify vulnerabilities and misconfigurations
- **Cost Optimizer**: Optimize Kubernetes resource utilization and costs
- **Backup Manager**: Manage backups and restores of Kubernetes resources
- **Remediator**: Automated remediation of detected issues

## Technology Stack

- React 18.x
- React Router for navigation
- Tailwind CSS for styling
- Chart.js for data visualization
- Axios for API communication

## Getting Started

### Prerequisites

- Node.js 16.x or higher
- npm 8.x or higher

### Installation

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

3. Build for production:
   ```bash
   npm run build
   ```

## Project Structure

```
frontend/
├── public/                # Static files
├── src/
│   ├── api/               # API service modules
│   │   ├── api.js         # Base API configuration
│   │   ├── predictorService.js
│   │   ├── securityService.js
│   │   ├── costService.js
│   │   ├── backupService.js
│   │   └── remediatorService.js
│   ├── components/        # Reusable components
│   │   ├── layout/        # Layout components (Navbar, Sidebar)
│   │   └── ui/            # UI components (Button, Card, Badge)
│   ├── pages/             # Page components
│   ├── App.js             # Main app component
│   └── index.js           # Entry point
├── package.json           # Dependencies and scripts
└── tailwind.config.js     # Tailwind CSS configuration
```

## API Communication

The frontend communicates with the Kagent backend through a set of API services located in the `src/api` directory:

- `predictorService.js`: Metrics, predictions, and ML model operations
- `securityService.js`: Security scanning and vulnerability management
- `costService.js`: Cost analysis and optimization
- `backupService.js`: Backup and restore operations
- `remediatorService.js`: Issue remediation

## Screenshots

![Dashboard](https://example.com/dashboard.png)
![ML Predictor](https://example.com/predictor.png)
![Security Scanner](https://example.com/security.png)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request 