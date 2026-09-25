export interface Finding {
    id: string;
    title: string;
    type: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    confidence: number;
    confidence_label: string;
    category: string;
    cwe: string;
    cwe_title: string;
    owasp: string;
    endpoint: string;
    endpoint_template: string;
    method: string;
    attacker: string;
    resource_owner: string;
    object_id: string;
    status_code: number;
    status: 'vulnerable' | 'not vulnerable';
    timestamp: string;
    verification: {
        cross_identity: boolean;
        ownership_mismatch: boolean;
        successful_access: boolean;
        object_identity_matched: boolean;
        bidirectional_tested: boolean;
    };
    evidence: {
        finding_id: string;
        timestamp: string;
        request: {
            method: string;
            url: string;
            user: string;
            headers: Record<string, string>;
        };
        response: any;
        response_metadata: {
            status_code: number;
            content_type: string;
            content_length: number;
            body_type: string;
            body_hash: string;
            headers: Record<string, string>;
        };
        response_fingerprint: string;
        attacker_collection: any;
        resource_owner_collection: any;
        sensitive_fields_exposed: string[];
    };
    impact: string;
    remediation: string;
    developer_remediation: {
        what_happened: string;
        why_it_matters: string;
        how_to_fix: string;
        code_example: {
            vulnerable: string;
            remediated: string;
        };
        fix_verification: string;
    };
    description: string;
    security_reasoning: string[];
}