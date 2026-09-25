# SentinelAPI Frontend

This README provides an overview of the SentinelAPI frontend application, including setup instructions, usage guidelines, and project structure.

## Project Overview

The SentinelAPI frontend is designed to provide a user-friendly interface for interacting with the SentinelAPI backend. It allows users to initiate scans, view findings, and manage their accounts securely.

## Setup Instructions

To set up the frontend application, follow these steps:

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd sentinelapi/frontend
   ```

2. **Install Dependencies**
   Ensure you have [Node.js](https://nodejs.org/) installed. Then, run:
   ```bash
   npm install
   ```

3. **Run the Development Server**
   Start the development server with:
   ```bash
   npm run dev
   ```
   The application will be available at `http://localhost:3000`.

## Usage Guidelines

- **Login**: Users can log in using their credentials. Ensure that the backend is running to authenticate users.
- **Dashboard**: The dashboard provides an overview of scan statistics and findings.
- **Scans**: Users can initiate new scans and view the results of previous scans.
- **Findings**: Users can review findings from scans, including details and remediation steps.

## Project Structure

The frontend project is organized as follows:

```
frontend
├── public                # Static assets
│   └── favicon.svg      # Favicon for the application
├── src                   # Source code
│   ├── app               # Main application components
│   ├── components        # Reusable components
│   ├── pages             # Page components
│   ├── services          # API service functions
│   ├── store             # Redux store configuration
│   ├── styles            # CSS styles
│   ├── utils             # Utility functions
│   ├── main.tsx          # Entry point for the application
│   └── vite-env.d.ts     # TypeScript definitions for Vite
├── package.json          # Project dependencies and scripts
├── tsconfig.json         # TypeScript configuration
├── tsconfig.node.json    # Node-specific TypeScript configuration
└── vite.config.ts        # Vite configuration
```

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.