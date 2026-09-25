# SentinelAPI: Zero-Trust API Vulnerability Scanner

## Overview

SentinelAPI is a cutting-edge tool designed to identify vulnerabilities in APIs, focusing on zero-trust principles. It automates the detection of common API vulnerabilities, such as broken object-level authorization and excessive data exposure, ensuring that your API surface is secure against potential breaches.

## Features

- **Automated Scanning**: Ingests OpenAPI/Swagger specifications or observes live traffic to identify vulnerabilities.
- **Authorization Flaw Detection**: Tests for IDOR (Insecure Direct Object References) and other authorization issues by manipulating identifiers across authenticated sessions.
- **Data Exposure Analysis**: Detects excessive data exposure, ensuring that responses do not return more information than necessary.
- **Comprehensive Reporting**: Generates severity-ranked findings with clear reproduction steps, making it easier for developers to address vulnerabilities.
- **Continuous Integration**: Optionally integrates with CI/CD pipelines for ongoing security assessments.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- FastAPI
- HTTPX
- Other dependencies listed in `requirements.txt`

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/sentinelapi.git
   cd sentinelapi/backend
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables by copying the example:
   ```
   cp .env.example .env
   ```

### Running the Application

To start the backend application, run:
```
uvicorn app.main:app --reload
```

### Usage

1. Access the API documentation at `http://localhost:8000/docs` to explore available endpoints.
2. Use the provided endpoints to initiate scans and retrieve findings.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the need for robust API security in modern applications.
- Thanks to the open-source community for their invaluable contributions to security tooling.