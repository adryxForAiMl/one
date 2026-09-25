# SentinelAPI Frontend Documentation

## Overview

The SentinelAPI frontend is built using Next.js and TypeScript, providing a user-friendly interface for interacting with the Zero-Trust API Vulnerability Scanner. This application allows users to manage scans, view findings, and generate reports related to API vulnerabilities.

## Project Structure

The frontend project is organized as follows:

- **src/**: Contains the main source code for the application.
  - **app/**: Contains global styles and layout components.
  - **components/**: Contains reusable components for different parts of the application.
    - **common/**: Commonly used components such as Header, Sidebar, and StatusBadge.
    - **dashboard/**: Components related to the dashboard, including ScanOverview, FindingsTable, and AuthPanel.
    - **reports/**: Components for displaying findings reports.
  - **lib/**: Contains utility functions for API requests and other helper functions.
  - **types/**: TypeScript type definitions for API responses and findings.

## Getting Started

To get started with the SentinelAPI frontend, follow these steps:

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd SentinelAPI/frontend
   ```

2. **Install dependencies**:
   ```
   npm install
   ```

3. **Run the development server**:
   ```
   npm run dev
   ```

4. **Open your browser** and navigate to `http://localhost:3000` to view the application.

## Environment Variables

Create a `.env` file in the root of the frontend directory and configure the necessary environment variables. You can refer to the `.env.example` file for the required variables.

## Scripts

The following scripts are available in the `package.json`:

- `dev`: Starts the development server.
- `build`: Builds the application for production.
- `start`: Starts the production server.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.