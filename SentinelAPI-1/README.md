# SentinelAPI: Zero-Trust API Vulnerability Scanner

## Overview

SentinelAPI is a comprehensive vulnerability scanner designed to identify and mitigate Broken Object Level Authorization (BOLA) vulnerabilities in APIs. By implementing a zero-trust approach, this tool ensures that only authorized users can access sensitive resources, thereby enhancing the security posture of your applications.

## Features

- **BOLA Detection**: Automatically identifies instances of Broken Object Level Authorization in your APIs.
- **Bidirectional Verification**: Validates access controls by testing both the attacker and victim perspectives.
- **Response Fingerprinting**: Captures and analyzes API responses to detect unauthorized data exposure.
- **Remediation Guidance**: Provides detailed instructions and code examples for developers to fix identified vulnerabilities.
- **Reporting**: Generates comprehensive reports on scan findings, including sensitive data exposure and security recommendations.

## Project Structure

```
SentinelAPI
├── app                # Backend application code
│   ├── api            # API routes and dependencies
│   ├── core           # Core application logic (config, security, logging)
│   ├── db             # Database models and session management
│   ├── models         # Data models for the application
│   ├── schemas        # Pydantic schemas for data validation
│   ├── services       # Business logic and service layer
│   ├── scanner        # Scanning logic and utilities
│   └── utils          # Utility functions and helpers
├── frontend           # Frontend application code
│   ├── src            # Source files for the frontend
│   └── public         # Public assets (e.g., favicon)
├── tests              # Test suite for the application
├── .env.example       # Example environment configuration
├── .gitignore         # Git ignore file
├── docker-compose.yml  # Docker Compose configuration
├── requirements.txt   # Python dependencies
├── pyproject.toml     # Python project configuration
├── Makefile           # Build and management commands
└── README.md          # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js and npm (for the frontend)
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/SentinelAPI.git
   cd SentinelAPI
   ```

2. Set up the backend:
   - Navigate to the `app` directory and install the required Python packages:
     ```
     pip install -r requirements.txt
     ```

3. Set up the frontend:
   - Navigate to the `frontend` directory and install the required Node.js packages:
     ```
     npm install
     ```

4. Configure environment variables:
   - Copy `.env.example` to `.env` and update the values as needed.

### Running the Application

- To start the backend server:
  ```
  uvicorn app.main:app --reload
  ```

- To start the frontend development server:
  ```
  npm run dev
  ```

### Running Tests

To run the test suite, use:
```
pytest tests/
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.