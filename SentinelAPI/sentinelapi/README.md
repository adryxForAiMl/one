# SentinelAPI: Zero-Trust API Vulnerability Scanner

## Overview

SentinelAPI is a cutting-edge tool designed to identify vulnerabilities in APIs, focusing on zero-trust principles. It automates the detection of common API vulnerabilities such as Broken Object Level Authorization (BOLA), excessive data exposure, and misconfigured authentication, ensuring that your APIs are secure before they go live.

## Features

- **Automated Scanning**: Ingest OpenAPI/Swagger specifications or observe live traffic to identify vulnerabilities.
- **Authorization Flaw Detection**: Automatically test for IDOR and other authorization issues by manipulating identifiers across authenticated sessions.
- **Data Exposure Analysis**: Detect excessive data exposure by analyzing API responses.
- **Comprehensive Reporting**: Generate severity-ranked findings with clear reproduction steps and actionable insights.
- **Continuous Integration**: Optionally integrate with CI/CD pipelines for ongoing security assessments.

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Node.js (for frontend)
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/sentinelapi.git
   cd sentinelapi
   ```

2. Install backend dependencies:
   ```
   cd backend
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```
   cd frontend
   npm install
   ```

### Running the Application

#### Backend

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Start the FastAPI server:
   ```
   uvicorn app.main:app --reload
   ```

#### Frontend

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Start the development server:
   ```
   npm run dev
   ```

## Usage

- Access the API documentation at `http://localhost:8000/docs` after starting the backend server.
- Use the frontend application to interact with the API and view scan results.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

- Inspired by the need for robust API security in modern applications.
- Developed by a team of passionate engineers and security experts.