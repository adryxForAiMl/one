// This file defines types for API responses.

export interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: string;
}

export interface ScanResult {
    id: string;
    status: string;
    findings: Finding[];
}

export interface Finding {
    id: string;
    title: string;
    severity: string;
    description: string;
    remediation: string;
    timestamp: string;
}

export interface User {
    id: string;
    username: string;
    email: string;
}

export interface AuthResponse {
    token: string;
    user: User;
}