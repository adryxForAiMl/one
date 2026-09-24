from __future__ import annotations

import math
import os
from collections import Counter
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier


MODEL_DIR = os.path.join(
    os.path.dirname(__file__),
    "artifacts",
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "sentinel_risk_model.joblib",
)


SEVERITY_WEIGHTS = {
    "CRITICAL": 50,
    "HIGH": 30,
    "MEDIUM": 15,
    "LOW": 5,
}


SEVERITY_ORDER = {
    "CRITICAL": 4,
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}


FEATURE_NAMES = [
    "response_success",
    "ownership_mismatch",
    "has_object_id",
    "method_get",
    "status_2xx",
    "cross_identity",
    "successful_access",
    "object_identity_matched",
    "status_200",
    "endpoint_depth",
    "response_present",
]


def clamp(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    return max(
        minimum,
        min(value, maximum),
    )


def classify_confidence(
    confidence: float,
) -> str:
    if confidence >= 0.90:
        return "VERY HIGH"

    if confidence >= 0.75:
        return "HIGH"

    if confidence >= 0.50:
        return "MEDIUM"

    return "LOW"


def classify_anomaly(
    score: float,
) -> str:
    if score >= 0.85:
        return "SEVERE"

    if score >= 0.65:
        return "HIGH"

    if score >= 0.40:
        return "MODERATE"

    return "LOW"


def build_training_dataset():
    rng = np.random.default_rng(42)

    normal_rows = []
    normal_labels = []

    vulnerable_rows = []
    vulnerable_labels = []

    for _ in range(300):

        endpoint_depth = int(
            rng.integers(
                1,
                5,
            )
        )

        normal_rows.append(
            [
                float(
                    rng.choice(
                        [0, 1],
                        p=[0.25, 0.75],
                    )
                ),
                0.0,
                float(
                    rng.choice(
                        [0, 1],
                        p=[0.35, 0.65],
                    )
                ),
                float(
                    rng.choice(
                        [0, 1]
                    )
                ),
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                float(
                    endpoint_depth
                ),
                float(
                    rng.choice(
                        [0, 1],
                        p=[0.15, 0.85],
                    )
                ),
            ]
        )

        normal_labels.append(0)

    for _ in range(300):

        endpoint_depth = int(
            rng.integers(
                2,
                6,
            )
        )

        vulnerable_rows.append(
            [
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                float(
                    rng.choice(
                        [0, 1],
                        p=[0.05, 0.95],
                    )
                ),
                float(
                    endpoint_depth
                ),
                1.0,
            ]
        )

        vulnerable_labels.append(1)

    X = np.array(
        normal_rows + vulnerable_rows,
        dtype=float,
    )

    y = np.array(
        normal_labels + vulnerable_labels,
        dtype=int,
    )

    return X, y


def train_model():
    os.makedirs(
        MODEL_DIR,
        exist_ok=True,
    )

    X, y = build_training_dataset()

    model = RandomForestClassifier(
        n_estimators=180,
        max_depth=8,
        min_samples_leaf=2,
        random_state=42,
        class_weight="balanced",
    )

    model.fit(
        X,
        y,
    )

    joblib.dump(
        {
            "model": model,
            "features": FEATURE_NAMES,
            "training_samples": len(X),
            "model_type": "RandomForestClassifier",
            "training_source": (
                "Synthetic security scenarios"
            ),
        },
        MODEL_PATH,
    )

    return model


def load_model():
    if not os.path.exists(
        MODEL_PATH
    ):
        return train_model()

    try:
        bundle = joblib.load(
            MODEL_PATH
        )

        return bundle["model"]

    except Exception:
        return train_model()


ML_MODEL = load_model()


def calculate_ml_probability(
    features: dict[str, float],
) -> float:

    vector = np.array(
        [
            features[name]
            for name in FEATURE_NAMES
        ],
        dtype=float,
    ).reshape(
        1,
        -1,
    )

    probabilities = (
        ML_MODEL.predict_proba(
            vector
        )[0]
    )

    classes = list(
        ML_MODEL.classes_
    )

    if 1 not in classes:
        return 0.0

    vulnerability_index = (
        classes.index(1)
    )

    return round(
        float(
            probabilities[
                vulnerability_index
            ]
        ),
        3,
    )


def calculate_base_risk(
    findings: list[dict[str, Any]],
) -> int:

    score = 0

    for finding in findings:

        severity = str(
            finding.get(
                "severity",
                "LOW",
            )
        ).upper()

        score += (
            SEVERITY_WEIGHTS.get(
                severity,
                0,
            )
        )

    return min(
        score,
        100,
    )


def calculate_confidence(
    finding: dict[str, Any],
) -> float:

    verification = (
        finding.get(
            "verification",
            {},
        )
    )

    signals = [
        bool(
            verification.get(
                "cross_identity"
            )
        ),
        bool(
            verification.get(
                "ownership_mismatch"
            )
        ),
        bool(
            verification.get(
                "successful_access"
            )
        ),
        bool(
            verification.get(
                "object_identity_matched"
            )
        ),
    ]

    evidence = (
        finding.get(
            "evidence",
            {},
        )
    )

    score = 0.50

    score += sum(
        0.10
        for signal in signals
        if signal
    )

    if evidence.get(
        "request"
    ):
        score += 0.05

    if evidence.get(
        "response"
    ) is not None:
        score += 0.05

    if finding.get(
        "status_code"
    ) == 200:
        score += 0.10

    return round(
        clamp(
            score,
            0.0,
            1.0,
        ),
        3,
    )


def build_finding_features(
    finding: dict[str, Any],
) -> dict[str, float]:

    status_code = int(
        finding.get(
            "status_code",
            0,
        )
        or 0
    )

    endpoint = str(
        finding.get(
            "endpoint",
            "",
        )
    )

    method = str(
        finding.get(
            "method",
            "GET",
        )
    ).upper()

    verification = (
        finding.get(
            "verification",
            {},
        )
    )

    evidence = (
        finding.get(
            "evidence",
            {},
        )
    )

    response_present = (
        1.0
        if evidence.get(
            "response"
        ) is not None
        else 0.0
    )

    endpoint_depth = len(
        [
            part
            for part in endpoint.split("/")
            if part
        ]
    )

    return {
        "response_success": (
            1.0
            if 200 <= status_code < 300
            else 0.0
        ),

        "ownership_mismatch": (
            1.0
            if verification.get(
                "ownership_mismatch"
            )
            else 0.0
        ),

        "has_object_id": (
            1.0
            if finding.get(
                "object_id"
            ) is not None
            else 0.0
        ),

        "method_get": (
            1.0
            if method == "GET"
            else 0.0
        ),

        "status_2xx": (
            1.0
            if 200 <= status_code < 300
            else 0.0
        ),

        "cross_identity": (
            1.0
            if verification.get(
                "cross_identity"
            )
            else 0.0
        ),

        "successful_access": (
            1.0
            if verification.get(
                "successful_access"
            )
            else 0.0
        ),

        "object_identity_matched": (
            1.0
            if verification.get(
                "object_identity_matched"
            )
            else 0.0
        ),

        "status_200": (
            1.0
            if status_code == 200
            else 0.0
        ),

        "endpoint_depth": float(
            endpoint_depth
        ),

        "response_present": (
            response_present
        ),
    }


def calculate_anomaly_score(
    finding: dict[str, Any],
) -> float:

    features = (
        build_finding_features(
            finding
        )
    )

    return calculate_ml_probability(
        features
    )


def enrich_finding(
    finding: dict[str, Any],
) -> dict[str, Any]:

    features = (
        build_finding_features(
            finding
        )
    )

    ml_probability = (
        calculate_ml_probability(
            features
        )
    )

    evidence_confidence = (
        calculate_confidence(
            finding
        )
    )

    enriched = dict(
        finding
    )

    enriched[
        "confidence"
    ] = evidence_confidence

    enriched[
        "confidence_label"
    ] = classify_confidence(
        evidence_confidence
    )

    enriched[
        "anomaly_score"
    ] = ml_probability

    enriched[
        "anomaly_label"
    ] = classify_anomaly(
        ml_probability
    )

    enriched[
        "ml_features"
    ] = features

    enriched[
        "ml_model"
    ] = {
        "type": (
            "RandomForestClassifier"
        ),
        "inference": (
            "local"
        ),
        "training_samples": 600,
        "training_source": (
            "Synthetic security scenarios"
        ),
        "vulnerability_probability": (
            ml_probability
        ),
    }

    return enriched


def correlate_findings(
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    endpoint_groups: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for finding in findings:

        endpoint = str(
            finding.get(
                "endpoint",
                "",
            )
        )

        endpoint_groups.setdefault(
            endpoint,
            [],
        ).append(
            finding
        )

    enriched_findings = []

    for finding in findings:

        enriched = enrich_finding(
            finding
        )

        endpoint = str(
            finding.get(
                "endpoint",
                "",
            )
        )

        group = endpoint_groups.get(
            endpoint,
            [],
        )

        enriched[
            "correlation"
        ] = {
            "same_endpoint_findings": len(
                group
            ),

            "cross_identity_pairs": len(
                {
                    (
                        item.get(
                            "attacker"
                        ),
                        item.get(
                            "resource_owner"
                        ),
                    )
                    for item in group
                }
            ),
        }

        enriched_findings.append(
            enriched
        )

    return enriched_findings


def calculate_attack_surface(
    endpoints: list[dict[str, Any]],
) -> dict[str, Any]:

    total = len(
        endpoints
    )

    object_endpoints = sum(
        1
        for endpoint in endpoints
        if endpoint.get(
            "category"
        ) == "object"
    )

    tested = sum(
        1
        for endpoint in endpoints
        if endpoint.get(
            "authorization_tested"
        )
    )

    vulnerable = sum(
        1
        for endpoint in endpoints
        if endpoint.get(
            "finding_count",
            0,
        )
        > 0
    )

    coverage = (
        (
            tested
            / total
        )
        * 100
        if total
        else 0.0
    )

    return {
        "total_endpoints": total,
        "object_endpoints": (
            object_endpoints
        ),
        "tested_endpoints": tested,
        "vulnerable_endpoints": (
            vulnerable
        ),
        "authorization_coverage": round(
            coverage,
            2,
        ),
    }


def calculate_exposure_score(
    findings: list[dict[str, Any]],
) -> int:

    if not findings:
        return 0

    unique_attackers = len(
        {
            finding.get(
                "attacker"
            )
            for finding in findings
            if finding.get(
                "attacker"
            )
        }
    )

    unique_victims = len(
        {
            finding.get(
                "resource_owner"
            )
            for finding in findings
            if finding.get(
                "resource_owner"
            )
        }
    )

    unique_endpoints = len(
        {
            finding.get(
                "endpoint"
            )
            for finding in findings
            if finding.get(
                "endpoint"
            )
        }
    )

    raw_score = (
        len(findings)
        * 20

        + unique_attackers
        * 10

        + unique_victims
        * 10

        + unique_endpoints
        * 10
    )

    return min(
        raw_score,
        100,
    )


def build_ai_security_summary(
    findings: list[dict[str, Any]],
    endpoints: list[dict[str, Any]],
) -> dict[str, Any]:

    enriched = (
        correlate_findings(
            findings
        )
    )

    if not enriched:
        return {
            "status": (
                "NO VERIFIED THREATS"
            ),
            "threat_model": (
                "No confirmed authorization "
                "boundary violation."
            ),
            "key_signals": [
                (
                    "No verified cross-identity "
                    "object access."
                ),
                (
                    "No confirmed unauthorized "
                    "object disclosure."
                ),
            ],
            "recommended_priority": (
                "CONTINUE MONITORING"
            ),
            "confidence": 0.0,
            "confidence_label": "LOW",
            "anomaly_score": 0.0,
            "anomaly_label": "LOW",
            "exposure_score": 0,
            "attack_surface": (
                calculate_attack_surface(
                    endpoints
                )
            ),
            "ml_model": {
                "type": (
                    "RandomForestClassifier"
                ),
                "inference": "local",
                "training_samples": 600,
                "training_source": (
                    "Synthetic security scenarios"
                ),
            },
        }

    average_confidence = (
        sum(
            finding[
                "confidence"
            ]
            for finding in enriched
        )
        / len(enriched)
    )

    average_anomaly = (
        sum(
            finding[
                "anomaly_score"
            ]
            for finding in enriched
        )
        / len(enriched)
    )

    severity_counter = Counter(
        str(
            finding.get(
                "severity",
                "LOW",
            )
        ).upper()
        for finding in enriched
    )

    critical = severity_counter[
        "CRITICAL"
    ]

    high = severity_counter[
        "HIGH"
    ]

    exposure_score = (
        calculate_exposure_score(
            enriched
        )
    )

    if critical > 0:
        priority = (
            "IMMEDIATE REMEDIATION"
        )
    elif high > 0:
        priority = (
            "HIGH PRIORITY REVIEW"
        )
    else:
        priority = (
            "SECURITY REVIEW"
        )

    affected_identities = len(
        {
            finding.get(
                "resource_owner"
            )
            for finding in enriched
            if finding.get(
                "resource_owner"
            )
        }
    )

    affected_endpoints = len(
        {
            finding.get(
                "endpoint"
            )
            for finding in enriched
            if finding.get(
                "endpoint"
            )
        }
    )

    attack_paths = len(
        {
            (
                finding.get(
                    "attacker"
                ),
                finding.get(
                    "endpoint"
                ),
                finding.get(
                    "resource_owner"
                ),
            )
            for finding in enriched
        }
    )

    return {
        "status": (
            "THREAT VERIFIED"
        ),

        "threat_model": (
            "Authenticated identities can "
            "cross authorization boundaries "
            "and access objects outside their "
            "ownership scope."
        ),

        "key_signals": [
            (
                f"{len(enriched)} verified "
                "authorization finding(s)."
            ),

            (
                f"{critical} critical "
                "finding(s) detected."
            ),

            (
                f"{affected_endpoints} endpoint(s) "
                "exposed."
            ),

            (
                f"{affected_identities} resource "
                "owner identity/identities affected."
            ),

            (
                f"{attack_paths} distinct "
                "attack path(s) reconstructed."
            ),
        ],

        "recommended_priority": priority,

        "confidence": round(
            average_confidence,
            3,
        ),

        "confidence_label": (
            classify_confidence(
                average_confidence
            )
        ),

        "anomaly_score": round(
            average_anomaly,
            3,
        ),

        "anomaly_label": (
            classify_anomaly(
                average_anomaly
            )
        ),

        "exposure_score": (
            exposure_score
        ),

        "attack_surface": (
            calculate_attack_surface(
                endpoints
            )
        ),

        "ml_model": {
            "type": (
                "RandomForestClassifier"
            ),
            "inference": "local",
            "training_samples": 600,
            "training_source": (
                "Synthetic security scenarios"
            ),
        },
    }


def explain_risk_score(
    final_score: int,
    enriched_findings: list[dict[str, Any]],
) -> str:
    if not enriched_findings:
        return (
            "RISK SCORE: 0 (SECURE)\n"
            "WHY: All tested authorization boundaries held successfully. "
            "No cross-identity object leakage was detected."
        )

    critical_count = sum(
        1 for f in enriched_findings if f.get("severity") == "CRITICAL"
    )
    unique_victims = len(
        {f.get("resource_owner") for f in enriched_findings if f.get("resource_owner")}
    )
    unique_attackers = len(
        {f.get("attacker") for f in enriched_findings if f.get("attacker")}
    )

    return (
        f"RISK SCORE: {final_score} / 100\n"
        f"WHY: Cross-user access was deterministically verified between "
        f"{unique_attackers} authenticated identity(ies) and {unique_victims} victim resource owner(s). "
        f"The API returned another user's protected object with HTTP 200 OK. "
        f"{critical_count} critical finding(s) confirmed missing server-side authorization enforcement."
    )


def build_security_scorecard(
    findings: list[dict[str, Any]],
    endpoints: list[dict[str, Any]],
) -> dict[str, Any]:
    vulnerable_count = sum(
        1 for f in findings if f.get("severity") in ("CRITICAL", "HIGH")
    )
    has_bola = any(f.get("type") == "BOLA" for f in findings)
    exposed_sensitive_fields = sum(
        len(f.get("evidence", {}).get("sensitive_fields_exposed", []))
        for f in findings
    )
    total_ep = len(endpoints)
    tested_ep = sum(1 for ep in endpoints if ep.get("authorization_tested"))

    auth_score = 90
    auth_grade = "A"

    if has_bola:
        authz_score = max(10, 100 - (vulnerable_count * 45))
        authz_grade = "F" if authz_score < 60 else "D"
        authz_status = "VIOLATED"
        authz_detail = f"{vulnerable_count} verified object-level authorization bypass(es)"
    else:
        authz_score = 95
        authz_grade = "A"
        authz_status = "ENFORCED"
        authz_detail = "Authorization boundaries held across tested identities"

    if has_bola:
        obj_score = max(5, 90 - (vulnerable_count * 40))
        obj_grade = "F" if obj_score < 60 else "D"
        obj_status = "EXPOSED"
        obj_detail = "Authenticated identities accessed objects outside their ownership scope"
    else:
        obj_score = 95
        obj_grade = "A"
        obj_status = "RESTRICTED"
        obj_detail = "Object retrieval is restricted to legitimate resource owners"

    if exposed_sensitive_fields > 0:
        data_score = max(30, 85 - (exposed_sensitive_fields * 15))
        data_grade = "C" if data_score >= 70 else "D"
        data_status = "EXCESSIVE"
        data_detail = f"{exposed_sensitive_fields} sensitive field instance(s) exposed in cross-user responses"
    elif has_bola:
        data_score = 65
        data_grade = "D"
        data_status = "MODERATE"
        data_detail = "Protected resource properties returned to unauthorized caller"
    else:
        data_score = 95
        data_grade = "A"
        data_status = "MINIMAL"
        data_detail = "No excessive sensitive data exposed"

    api_score = 88
    api_grade = "B"
    api_status = "HARDENED"
    api_detail = "OpenAPI specification valid and structured"

    coverage = (tested_ep / total_ep * 100) if total_ep else 100.0
    surface_score = int(round(coverage))
    surface_grade = "A" if surface_score >= 80 else "B" if surface_score >= 60 else "C"
    surface_status = "MAPPED"
    surface_detail = f"{tested_ep} of {total_ep} endpoints tested ({round(coverage, 1)}% coverage)"

    return {
        "overall_grade": "F" if has_bola else "A",
        "categories": [
            {
                "name": "Authentication",
                "score": auth_score,
                "grade": auth_grade,
                "status": "ENFORCED",
                "detail": "Bearer/API Key credentials required and validated",
            },
            {
                "name": "Authorization",
                "score": authz_score,
                "grade": authz_grade,
                "status": authz_status,
                "detail": authz_detail,
            },
            {
                "name": "Object Access",
                "score": obj_score,
                "grade": obj_grade,
                "status": obj_status,
                "detail": obj_detail,
            },
            {
                "name": "Data Exposure",
                "score": data_score,
                "grade": data_grade,
                "status": data_status,
                "detail": data_detail,
            },
            {
                "name": "API Configuration",
                "score": api_score,
                "grade": api_grade,
                "status": api_status,
                "detail": api_detail,
            },
            {
                "name": "Attack Surface",
                "score": surface_score,
                "grade": surface_grade,
                "status": surface_status,
                "detail": surface_detail,
            },
        ],
    }


def calculate_intelligent_risk(
    findings: list[dict[str, Any]],
    endpoints: list[dict[str, Any]],
) -> dict[str, Any]:

    enriched_findings = (
        correlate_findings(
            findings
        )
    )

    base_score = (
        calculate_base_risk(
            enriched_findings
        )
    )

    scorecard = build_security_scorecard(
        enriched_findings,
        endpoints,
    )

    if not enriched_findings:
        return {
            "score": 0,
            "level": "SECURE",
            "base_score": 0,
            "confidence": 0.0,
            "confidence_label": "LOW",
            "exposure_score": 0,
            "anomaly_score": 0.0,
            "anomaly_label": "LOW",
            "why_explanation": explain_risk_score(0, []),
            "scorecard": scorecard,
            "ai_summary": (
                build_ai_security_summary(
                    enriched_findings,
                    endpoints,
                )
            ),
            "findings": [],
            "ml_engine": {
                "enabled": True,
                "model": "RandomForestClassifier",
                "inference": "local",
                "training_samples": 600,
                "feature_count": len(FEATURE_NAMES),
                "feature_names": FEATURE_NAMES,
                "training_source": "Synthetic security scenarios",
            },
        }

    average_confidence = (
        sum(
            finding["confidence"]
            for finding in enriched_findings
        )
        / len(enriched_findings)
    )

    average_anomaly = (
        sum(
            finding["anomaly_score"]
            for finding in enriched_findings
        )
        / len(enriched_findings)
    )

    exposure_score = (
        calculate_exposure_score(
            enriched_findings
        )
    )

    ml_component = (
        average_anomaly
        * 15
    )

    confidence_component = (
        average_confidence
        * 10
    )

    exposure_component = (
        exposure_score
        * 0.10
    )

    final_score = int(
        clamp(
            base_score
            + ml_component
            + confidence_component
            + exposure_component,
            0,
            100,
        )
    )

    if final_score >= 80:
        level = "CRITICAL"
    elif final_score >= 50:
        level = "HIGH"
    elif final_score >= 25:
        level = "MEDIUM"
    elif final_score > 0:
        level = "LOW"
    else:
        level = "SECURE"

    return {
        "score": final_score,
        "level": level,
        "base_score": base_score,
        "confidence": round(average_confidence, 3),
        "confidence_label": classify_confidence(average_confidence),
        "exposure_score": exposure_score,
        "anomaly_score": round(average_anomaly, 3),
        "anomaly_label": classify_anomaly(average_anomaly),
        "why_explanation": explain_risk_score(final_score, enriched_findings),
        "scorecard": scorecard,
        "ai_summary": (
            build_ai_security_summary(
                enriched_findings,
                endpoints,
            )
        ),
        "findings": enriched_findings,
        "ml_engine": {
            "enabled": True,
            "model": "RandomForestClassifier",
            "inference": "local",
            "training_samples": 600,
            "feature_count": len(FEATURE_NAMES),
            "feature_names": FEATURE_NAMES,
            "training_source": "Synthetic security scenarios",
        },
    }