import { useState, useMemo } from "react"
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Eye,
  EyeOff,
  Globe2,
  Info,
  KeyRound,
  Loader2,
  Play,
  Plus,
  Radar,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  UserRound,
  XCircle,
  Zap,
} from "lucide-react"
import {
  validateTargetApi,
  executeSecurityScan,
  type PreflightResponse,
  type AuthenticationProfilePayload,
} from "./api/client"
import { validateTargetUrl } from "./utils/urlValidator"

type Finding = {
  id: string
  title?: string
  type: string
  severity: string
  category?: string
  cwe?: string
  owasp?: string
  endpoint: string
  endpoint_template?: string
  method: string
  attacker: string
  resource_owner: string
  object_id: number | string
  status_code: number
  confidence?: number
  confidence_label?: string
  anomaly_score?: number
  anomaly_label?: string
  impact: string
  remediation: string
  description: string
  security_reasoning?: string[]
  evidence?: {
    request?: {
      method: string
      url: string
      user: string
      headers?: Record<string, string>
    }
    response?: Record<string, unknown>
    response_metadata?: Record<string, unknown>
    response_fingerprint?: string
    sensitive_fields_exposed?: string[]
  }
}

type Endpoint = {
  path: string
  method: string
  category: string
  parameter?: string | null
  collection_path?: string | null
  authorization_tested: boolean
  finding_count: number
  severity?: string | null
  status: string
}

type ScorecardCategory = {
  name: string
  score: number
  grade: string
  status: string
  detail: string
}

type ScanResult = {
  scan_id: string
  status: string
  target: string
  target_url?: string
  scan_metadata?: {
    scanner?: string
    tagline?: string
    started_at?: string
    authentication_profiles?: number
    authorization_testing?: boolean
    openapi_discovery?: boolean
    openapi_version?: string
    discovered_endpoints?: number
    tested_endpoints?: number
    vulnerable_endpoints?: number
    intelligence_engine?: string
  }
  discovery?: {
    openapi_url?: string
    openapi_version?: string
    endpoint_count?: number
    object_endpoint_count?: number
    collection_endpoint_count?: number
  }
  endpoints?: Endpoint[]
  risk?: {
    score: number
    level: string
    base_score?: number
    confidence?: number
    confidence_label?: string
    anomaly_score?: number
    anomaly_label?: string
    exposure_score?: number
    why_explanation?: string
    scorecard?: {
      overall_grade: string
      categories: ScorecardCategory[]
    }
    ai_summary?: {
      status?: string
      threat_model?: string
      key_signals?: string[]
      recommended_priority?: string
      confidence?: number
      anomaly_score?: number
      exposure_score?: number
    }
    ml_engine?: {
      enabled?: boolean
      model?: string
      inference?: string
      training_samples?: number
      training_source?: string
    }
  }
  summary: {
    vulnerabilities: number
    critical: number
    high: number
    medium: number
    low: number
  }
  findings: Finding[]
  attack_graph?: {
    paths: Array<{
      finding_id: string
      title: string
      nodes: unknown[]
      edges: unknown[]
    }>
  }
}

type AuthenticationType = "bearer" | "api-key"

type AuthenticationProfile = {
  id: number
  name: string
  type: AuthenticationType
  credential: string
  header: string
  showSecret?: boolean
}

type ApiScannerProps = {
  onScanComplete?: (result: ScanResult) => void
  onNavigateToDashboard?: () => void
}

const PIPELINE_STAGES = [
  "1. Target",
  "2. Netra Discovery",
  "3. Access Verification",
  "4. Raksha Authorization Tests",
  "5. Drishti Risk Intelligence",
  "6. Pramaan Evidence",
  "7. Security Verdict",
]

type TraceEntry = {
  id: string
  title: string
  detail: string
  status: "pass" | "warn" | "active" | "pending"
  meta?: string
}

const DEFAULT_TARGET_URL = import.meta.env.VITE_TARGET_API_URL?.trim() || "http://localhost:8000"

function createDefaultProfile(id: number): AuthenticationProfile {
  return {
    id,
    name: id === 1 ? "User A" : id === 2 ? "User B" : `Identity ${id}`,
    type: "bearer",
    credential: id === 1 ? "token-user-a" : id === 2 ? "token-user-b" : "",
    header: "Authorization",
    showSecret: false,
  }
}

export default function ApiScanner({
  onScanComplete,
  onNavigateToDashboard,
}: ApiScannerProps) {
  const [targetUrl, setTargetUrl] = useState(DEFAULT_TARGET_URL)
  const [profiles, setProfiles] = useState<AuthenticationProfile[]>([
    createDefaultProfile(1),
    createDefaultProfile(2),
  ])

  // Preflight states
  const [preflightRunning, setPreflightRunning] = useState(false)
  const [preflightData, setPreflightData] = useState<PreflightResponse | null>(null)
  const [preflightError, setPreflightError] = useState("")

  // Scan states
  const [scanning, setScanning] = useState(false)
  const [currentStageIndex, setCurrentStageIndex] = useState(0)
  const [scanError, setScanError] = useState("")
  const [scanResult, setScanResult] = useState<ScanResult | null>(null)

  // Strict URL Validation on current input
  const urlValidation = useMemo(() => {
    return validateTargetUrl(targetUrl)
  }, [targetUrl])

  // Check if credentials are valid across all profiles
  const authValidation = useMemo(() => {
    if (profiles.length < 2) {
      return { isValid: false, message: "At least 2 authenticated identities are required for zero-trust authorization testing." }
    }
    const emptyProfiles = profiles.filter((p) => !p.credential.trim())
    if (emptyProfiles.length > 0) {
      return {
        isValid: false,
        message: `Missing credential token for: ${emptyProfiles.map((p) => p.name).join(", ")}. Provide valid credentials to test tenancy boundaries.`,
      }
    }
    return { isValid: true, message: "" }
  }, [profiles])

  // Autofill local demo
  const loadLocalDemo = () => {
    setTargetUrl("http://localhost:8000")
    setProfiles([createDefaultProfile(1), createDefaultProfile(2)])
    setPreflightData(null)
    setPreflightError("")
    setScanResult(null)
    setScanError("")
    setCurrentStageIndex(0)
  }

  // Preflight validation execution
  const executePreflight = async () => {
    if (preflightRunning || scanning) return

    if (!urlValidation.isValid) {
      setPreflightError(urlValidation.error || "Please provide a valid HTTP or HTTPS API URL.")
      return
    }

    try {
      setPreflightRunning(true)
      setPreflightError("")

      const data = await validateTargetApi(urlValidation.normalizedUrl)
      setPreflightData(data)
    } catch (err) {
      setPreflightError(
        err instanceof Error
          ? err.message
          : "Unable to complete target validation. Ensure the KAVACH backend is online."
      )
    } finally {
      setPreflightRunning(false)
    }
  }

  // Security scan execution
  const startSecurityScan = async () => {
    if (scanning || preflightRunning) return

    if (!preflightData || preflightData.status !== "SCAN_READY") {
      setScanError("Target validation must succeed with a discovered OpenAPI specification before starting the zero-trust scan.")
      return
    }

    if (!authValidation.isValid) {
      setScanError(authValidation.message)
      return
    }

    let interval: ReturnType<typeof setInterval> | undefined

    try {
      setScanning(true)
      setScanError("")
      setScanResult(null)
      setCurrentStageIndex(0)

      // Smooth progression for visual pipeline feedback
      interval = setInterval(() => {
        setCurrentStageIndex((prev) => {
          if (prev < PIPELINE_STAGES.length - 2) {
            return prev + 1
          }
          return prev
        })
      }, 400)

      const authPayload: AuthenticationProfilePayload[] = profiles.map((p) => ({
        name: p.name.trim(),
        type: p.type,
        token: p.type === "bearer" ? p.credential.trim() : undefined,
        api_key: p.type === "api-key" ? p.credential.trim() : undefined,
        header: p.header.trim() || (p.type === "bearer" ? "Authorization" : "X-API-Key"),
      }))

      const result = await executeSecurityScan<ScanResult>({
        target_url: urlValidation.normalizedUrl || targetUrl.trim(),
        authentication_profiles: authPayload,
      })

      clearInterval(interval)
      setCurrentStageIndex(PIPELINE_STAGES.length - 1)

      setScanResult(result)
      if (onScanComplete) {
        onScanComplete(result)
      }
    } catch (err) {
      setScanError(
        err instanceof Error ? err.message : "Error executing zero-trust security scan."
      )
    } finally {
      if (interval) clearInterval(interval)
      setScanning(false)
    }
  }

  // Profile management
  const addProfile = () => {
    if (profiles.length >= 6) return
    setProfiles((prev) => [...prev, createDefaultProfile(prev.length + 1)])
  }

  const removeProfile = (id: number) => {
    if (profiles.length <= 2) return
    setProfiles((prev) => prev.filter((p) => p.id !== id))
  }

  const updateProfile = (id: number, field: keyof AuthenticationProfile, value: unknown) => {
    setProfiles((prev) =>
      prev.map((p) => (p.id === id ? { ...p, [field]: value } : p))
    )
  }

  const isScanReady = preflightData?.status === "SCAN_READY"

  const liveTrace = useMemo<TraceEntry[]>(() => {
    if (scanResult) {
      return [
        {
          id: "target",
          title: "Target validated",
          detail: `Connected to ${scanResult.target_url ?? scanResult.target}`,
          status: "pass",
          meta: scanResult.scan_metadata?.openapi_version ?? "OpenAPI",
        },
        {
          id: "discovery",
          title: "Endpoint discovery",
          detail: `${scanResult.discovery?.endpoint_count ?? scanResult.endpoints?.length ?? 0} routes inventoried`,
          status: "pass",
          meta: scanResult.discovery?.openapi_url ?? "Inventory complete",
        },
        {
          id: "identity",
          title: "Authorization verification",
          detail: `${scanResult.summary.vulnerabilities} confirmed findings across ${scanResult.scan_metadata?.authentication_profiles ?? profiles.length} identities`,
          status: scanResult.summary.vulnerabilities > 0 ? "warn" : "pass",
          meta: `${scanResult.summary.critical} critical / ${scanResult.summary.high} high`,
        },
        {
          id: "risk",
          title: "Risk intelligence",
          detail: `Overall risk score ${scanResult.risk?.score ?? 0} with ${scanResult.risk?.level ?? "unknown"} severity`,
          status: scanResult.risk?.score && scanResult.risk.score >= 70 ? "warn" : "pass",
          meta: scanResult.risk?.confidence_label ?? "confidence locked",
        },
      ]
    }

    if (preflightData) {
      return [
        {
          id: "target",
          title: "Target validation",
          detail: preflightData.message || "Target validation completed",
          status: preflightData.status === "SCAN_READY" ? "pass" : preflightData.status === "OPENAPI_NOT_FOUND" ? "warn" : "warn",
          meta: preflightData.status,
        },
        {
          id: "discovery",
          title: "OpenAPI discovery",
          detail: preflightData.openapi_discovered
            ? `${preflightData.total_endpoints} endpoints discovered`
            : "OpenAPI schema not available yet",
          status: preflightData.openapi_discovered ? "pass" : "warn",
          meta: preflightData.openapi_version ?? "Awaiting spec",
        },
        {
          id: "identity",
          title: "Identity matrix",
          detail: `${profiles.length} authenticated identities ready for comparison`,
          status: authValidation.isValid ? "pass" : "warn",
          meta: authValidation.isValid ? "ready" : "missing credentials",
        },
      ]
    }

    return [
      {
        id: "target",
        title: "Awaiting target validation",
        detail: "Enter the API base URL and validate the target before running the scan.",
        status: scanning ? "active" : "pending",
        meta: "waiting",
      },
      {
        id: "discovery",
        title: "Endpoint discovery",
        detail: "The scanner will inventory routes using OpenAPI and API probing.",
        status: scanning ? "active" : "pending",
        meta: "queued",
      },
      {
        id: "identity",
        title: "Authorization verification",
        detail: "Cross-user checks will compare responses across identities.",
        status: scanning ? "active" : "pending",
        meta: "queued",
      },
    ]
  }, [authValidation, preflightData, profiles.length, scanResult, scanning])

  const advancedTrace = useMemo(() => {
    if (!scanResult?.findings?.length) {
      return []
    }

    return scanResult.findings.slice(0, 4).map((finding, index) => ({
      id: finding.id,
      step: `Trace ${index + 1}`,
      title: finding.title ?? finding.type,
      severity: finding.severity,
      endpoint: finding.endpoint,
      method: finding.method,
      impact: finding.impact,
      reasoning: finding.security_reasoning?.[0] ?? finding.description,
    }))
  }, [scanResult])

  const traceStats = useMemo(() => {
    const findings = scanResult?.findings ?? []
    return {
      total: findings.length,
      critical: findings.filter((f) => f.severity.toLowerCase() === "critical").length,
      high: findings.filter((f) => f.severity.toLowerCase() === "high").length,
      medium: findings.filter((f) => f.severity.toLowerCase() === "medium").length,
      risk: scanResult?.risk?.score ?? 0,
      level: scanResult?.risk?.level ?? "unknown",
    }
  }, [scanResult])

  // Determine button state message
  const scanButtonReason = useMemo(() => {
    if (scanning) return "EXECUTING ZERO-TRUST SCAN..."
    if (preflightRunning) return "VALIDATING TARGET..."
    if (!preflightData) return "VALIDATE TARGET TO ENABLE SCAN"
    if (preflightData.status === "OPENAPI_NOT_FOUND") return "OPENAPI SPECIFICATION REQUIRED"
    if (preflightData.status === "NETWORK_ERROR" || preflightData.status === "TIMEOUT") return "TARGET HOST UNREACHABLE"
    if (preflightData.status !== "SCAN_READY") return "TARGET NOT SCAN-READY"
    if (!authValidation.isValid) return "CONFIGURE ≥2 IDENTITIES"
    return "START SECURITY SCAN"
  }, [scanning, preflightRunning, preflightData, authValidation])

  return (
    <div className="depth-stage p-6 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Hero Section */}
      <div className="depth-card relative overflow-hidden rounded-3xl border border-cyan-500/25 bg-gradient-to-br from-slate-900/90 via-[#0d152a]/95 to-slate-950 p-8 shadow-2xl backdrop-blur-xl">
        <div className="absolute right-0 top-0 -mr-16 -mt-16 h-80 w-80 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none" />
        <div className="absolute left-1/3 bottom-0 -mb-20 h-64 w-64 rounded-full bg-blue-500/10 blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-950/60 px-3.5 py-1 text-xs font-semibold text-cyan-300">
            <Radar className="h-3.5 w-3.5 animate-spin text-cyan-400" />
            KAVACH SCAN · ZERO-TRUST API SECURITY
          </div>

          <h1 className="mt-4 text-3xl font-extrabold tracking-tight sm:text-5xl text-white">
            Discover. Verify. <span className="text-cyan-400">Explain.</span> Protect.
          </h1>

          <p className="mt-3 text-base text-slate-300 leading-relaxed">
            Deterministic Broken Object Level Authorization (Raksha) auditing with Netra discovery,
            Pramaan behavioral response verification, Drishti ML intelligence, and Suraksha remediation.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={loadLocalDemo}
              className="inline-flex items-center gap-2 rounded-xl border border-cyan-500/40 bg-cyan-950/60 px-4 py-2.5 text-xs font-bold text-cyan-200 transition hover:bg-cyan-900/70 hover:border-cyan-400 hover:text-white shadow-lg shadow-cyan-950/40"
            >
              <Zap className="h-4 w-4 text-cyan-400" />
              TRY LOCAL SECURITY DEMO
            </button>

            <span className="text-xs text-slate-400">
              Populates KAVACH Lab controlled sandbox at <span className="font-mono text-cyan-300 font-semibold">http://localhost:8000</span>
            </span>
          </div>
        </div>
      </div>

      {/* Target API & Action Grid */}
      <div className="grid gap-6 lg:grid-cols-[1.8fr_1.2fr]">
        {/* Left Column: Target Input & Identity Management */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-[#0f172a]/90 p-6 shadow-xl backdrop-blur-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Globe2 className="h-5 w-5 text-cyan-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Target API Scope
                </h3>
              </div>
              <span className="rounded-full border border-slate-700 bg-slate-900 px-2.5 py-0.5 font-mono text-[10px] text-cyan-300">
                Non-Destructive Testing
              </span>
            </div>

            <div className="mt-4">
              <label htmlFor="target-api-scope" className="block text-xs font-semibold text-slate-300 mb-1.5">
                Target Base URL (HTTP / HTTPS Only)
              </label>
              <div className="flex gap-2">
                <input
                  id="target-api-scope"
                  type="text"
                  value={targetUrl}
                  onChange={(e) => {
                    setTargetUrl(e.target.value)
                    setPreflightData(null)
                    setPreflightError("")
                    setScanError("")
                    setScanResult(null)
                  }}
                  placeholder="http://localhost:8000 or https://api.jsonplaceholder.dev"
                  disabled={scanning || preflightRunning}
                  className={`flex-1 rounded-xl border bg-slate-950 px-4 py-3 font-mono text-sm text-slate-100 placeholder:text-slate-600 transition-colors focus:outline-none focus:ring-1 ${
                    urlValidation.isValid
                      ? "border-slate-700 focus:border-cyan-500 focus:ring-cyan-500"
                      : "border-red-500/70 focus:border-red-500 focus:ring-red-500"
                  }`}
                />

                <button
                  type="button"
                  onClick={executePreflight}
                  disabled={preflightRunning || scanning || !urlValidation.isValid}
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-600/90 hover:bg-cyan-500 border border-cyan-500/30 px-5 py-3 text-xs font-bold text-slate-950 transition hover:text-black shadow-lg shadow-cyan-900/30 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {preflightRunning ? (
                    <Loader2 className="h-4 w-4 animate-spin text-slate-950" />
                  ) : (
                    <ShieldCheck className="h-4 w-4 text-slate-950" />
                  )}
                  VALIDATE TARGET
                </button>
              </div>

              {/* Inline URL format validation feedback */}
              <div className="mt-2 text-xs">
                {urlValidation.isValid ? (
                  <div className="flex items-center gap-1.5 text-emerald-400">
                    <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
                    <span>
                      Valid API Target:{" "}
                      <a
                        href={urlValidation.normalizedUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="font-mono underline decoration-cyan-500/50 underline-offset-2 hover:text-cyan-200"
                      >
                        {urlValidation.normalizedUrl}
                      </a>
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 text-red-400">
                    <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                    <span>{urlValidation.error}</span>
                  </div>
                )}
                {urlValidation.warning && (
                  <div className="mt-1 flex items-center gap-1.5 text-amber-400">
                    <Info className="h-3.5 w-3.5 shrink-0" />
                    <span>{urlValidation.warning}</span>
                  </div>
                )}
              </div>

              {preflightError && (
                <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-900/60 bg-red-950/40 p-3 text-xs text-red-200">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
                  <span>{preflightError}</span>
                </div>
              )}
            </div>
          </div>

          {/* Authentication Identities Section */}
          <div className="rounded-2xl border border-slate-800 bg-[#0f172a]/90 p-6 shadow-xl backdrop-blur-md">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <UserRound className="h-5 w-5 text-cyan-400" />
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                    Multi-Identity Authorization Scope
                  </h3>
                </div>
                <p className="mt-1 text-xs text-slate-400">
                  Zero-trust testing requires ≥2 authenticated identities to verify cross-user resource isolation.
                </p>
              </div>

              <button
                type="button"
                onClick={addProfile}
                disabled={profiles.length >= 6 || scanning}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-700 hover:text-white disabled:opacity-40 transition"
              >
                <Plus className="h-3.5 w-3.5 text-cyan-400" />
                Add Identity
              </button>
            </div>

            {!authValidation.isValid && (
              <div className="mt-3 flex items-center gap-2 rounded-lg border border-amber-900/50 bg-amber-950/30 p-2.5 text-xs text-amber-300">
                <AlertCircle className="h-4 w-4 shrink-0 text-amber-400" />
                <span>{authValidation.message}</span>
              </div>
            )}

            <div className="mt-4 space-y-3">
              {profiles.map((profile, idx) => (
                <div
                  key={profile.id}
                  className="rounded-xl border border-slate-800/90 bg-slate-950/90 p-4 transition-all hover:border-slate-700"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/60 pb-2.5">
                    <div className="flex items-center gap-2">
                      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-cyan-950 border border-cyan-500/30 text-[10px] font-bold text-cyan-300">
                        {idx + 1}
                      </span>
                      <input
                        type="text"
                        value={profile.name}
                        onChange={(e) => updateProfile(profile.id, "name", e.target.value)}
                        placeholder="Identity Name"
                        disabled={scanning}
                        className="bg-transparent text-xs font-bold text-slate-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 rounded px-1"
                      />
                    </div>

                    <div className="flex items-center gap-2">
                      <select
                        value={profile.type}
                        onChange={(e) =>
                          updateProfile(profile.id, "type", e.target.value as AuthenticationType)
                        }
                        disabled={scanning}
                        className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-[11px] text-slate-300 focus:outline-none"
                      >
                        <option value="bearer">Bearer Token</option>
                        <option value="api-key">API Key</option>
                      </select>

                      {profiles.length > 2 && (
                        <button
                          type="button"
                          onClick={() => removeProfile(profile.id)}
                          disabled={scanning}
                          className="rounded p-1 text-slate-500 hover:text-red-400 transition"
                          title="Remove identity"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="mt-3">
                    <div className="flex items-center gap-2">
                      <KeyRound className="h-4 w-4 shrink-0 text-slate-500" />
                      <input
                        type={profile.showSecret ? "text" : "password"}
                        value={profile.credential}
                        onChange={(e) => updateProfile(profile.id, "credential", e.target.value)}
                        placeholder={
                          profile.type === "bearer"
                            ? "Bearer Token (e.g. token-user-a)"
                            : "API Key Value"
                        }
                        disabled={scanning}
                        className={`flex-1 rounded-lg border bg-slate-900/90 px-3 py-1.5 font-mono text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none transition ${
                          profile.credential.trim()
                            ? "border-slate-800 focus:border-cyan-500"
                            : "border-amber-500/60 focus:border-amber-500"
                        }`}
                      />
                      <button
                        type="button"
                        onClick={() => updateProfile(profile.id, "showSecret", !profile.showSecret)}
                        className="rounded p-1.5 text-slate-500 hover:text-slate-300 transition"
                        title={profile.showSecret ? "Hide credential" : "Show credential"}
                      >
                        {profile.showSecret ? <EyeOff size={14} /> : <Eye size={14} />}
                      </button>
                    </div>
                    {!profile.credential.trim() && (
                      <span className="mt-1 block text-[10px] text-amber-400/90 font-mono">
                        * Required credential token for cross-identity BOLA testing
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Preflight Checklist & Scan Action */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-[#0f172a]/90 p-6 shadow-xl backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-cyan-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Target Preflight Status
                </h3>
              </div>

              {preflightData && (
                <span
                  className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                    isScanReady
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                      : preflightData.status === "OPENAPI_NOT_FOUND"
                      ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                      : "bg-red-500/20 text-red-400 border border-red-500/30"
                  }`}
                >
                  {preflightData.status}
                </span>
              )}
            </div>

            {/* Checklist items */}
            <div className="mt-4 space-y-2.5">
              {!preflightData && !preflightRunning && (
                <div className="rounded-xl border border-dashed border-slate-800 bg-slate-950/60 p-8 text-center text-xs text-slate-400">
                  <Radar className="mx-auto mb-2 h-7 w-7 text-slate-600" />
                  Click <span className="font-semibold text-cyan-300">VALIDATE TARGET</span> above to run non-destructive reachability and OpenAPI discovery checks.
                </div>
              )}

              {preflightRunning && (
                <div className="rounded-xl border border-slate-800 bg-slate-950 p-8 text-center text-xs text-slate-300">
                  <Loader2 className="mx-auto mb-3 h-6 w-6 animate-spin text-cyan-400" />
                  Probing network reachability, OpenAPI specifications, and authorization boundaries...
                </div>
              )}

              {preflightData && (
                <>
                  {/* Detailed message banner if OpenAPI missing or error */}
                  {preflightData.status === "OPENAPI_NOT_FOUND" && (
                    <div className="rounded-xl border border-amber-500/40 bg-amber-950/20 p-3.5 text-xs text-amber-200">
                      <div className="flex items-center gap-2 font-bold text-amber-300">
                        <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
                        Target Reachable · OpenAPI Specification Missing
                      </div>
                      <p className="mt-1 text-[11px] leading-relaxed text-amber-200/90">
                        {preflightData.message}
                      </p>
                      <p className="mt-1.5 font-mono text-[10px] text-amber-300/80">
                        Zero-Trust scanning requires an OpenAPI or Swagger schema to map object routes and authorization boundaries.
                      </p>
                    </div>
                  )}

                  {preflightData.checklist.map((item) => (
                    <div
                      key={item.name}
                      className="flex items-start justify-between gap-3 rounded-xl border border-slate-800/80 bg-slate-950/90 px-3.5 py-2.5 text-xs"
                    >
                      <div className="flex items-start gap-2.5 min-w-0">
                        {item.status === "pass" ? (
                          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                        ) : item.status === "warn" ? (
                          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
                        ) : (
                          <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
                        )}
                        <div className="min-w-0">
                          <p className="font-bold uppercase tracking-wider text-slate-200">
                            {item.label}
                          </p>
                          <p className="mt-0.5 truncate text-[11px] text-slate-400">
                            {item.detail}
                          </p>
                        </div>
                      </div>

                      <span
                        className={`shrink-0 rounded px-1.5 py-0.5 text-[9px] font-bold uppercase ${
                          item.status === "pass"
                            ? "bg-emerald-950/60 text-emerald-400 border border-emerald-900/50"
                            : item.status === "warn"
                            ? "bg-amber-950/60 text-amber-400 border border-amber-900/50"
                            : "bg-red-950/60 text-red-400 border border-red-900/50"
                        }`}
                      >
                        {item.status}
                      </span>
                    </div>
                  ))}
                </>
              )}
            </div>

            {/* Scan Action Button */}
            <div className="mt-6 pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={startSecurityScan}
                disabled={!isScanReady || scanning || preflightRunning || !authValidation.isValid}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 via-blue-500 to-cyan-400 px-6 py-4 text-sm font-extrabold text-slate-950 transition-all hover:shadow-lg hover:shadow-cyan-500/25 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {scanning ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    EXECUTING ZERO-TRUST SCAN...
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5 fill-current" />
                    {scanButtonReason}
                  </>
                )}
              </button>

              {scanError && (
                <div className="mt-3 rounded-lg border border-red-900/50 bg-red-950/30 p-3 text-xs text-red-200">
                  {scanError}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 7-Stage Scan Pipeline Tracker */}
      {(scanning || preflightData || scanResult) && (
        <div className="rounded-2xl border border-cyan-500/30 bg-slate-900/95 p-6 shadow-2xl backdrop-blur-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-cyan-400" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-300">
                Live Trace Monitor
              </h3>
            </div>
            <span className="font-mono text-xs text-slate-400">
              {scanning ? `Stage ${currentStageIndex + 1} of ${PIPELINE_STAGES.length}` : "Trace ready"}
            </span>
          </div>

          <div className="mt-5 space-y-3">
            {liveTrace.map((entry) => (
              <div
                key={entry.id}
                className="flex items-start gap-3 rounded-xl border border-slate-800 bg-slate-950/80 p-3.5"
              >
                <div className="mt-0.5">
                  {entry.status === "pass" ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  ) : entry.status === "warn" ? (
                    <AlertTriangle className="h-4 w-4 text-amber-400" />
                  ) : entry.status === "active" ? (
                    <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
                  ) : (
                    <div className="h-2.5 w-2.5 rounded-full bg-slate-600" />
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-xs font-bold uppercase tracking-wider text-slate-200">
                      {entry.title}
                    </p>
                    {entry.meta && (
                      <span className="rounded border border-slate-700 bg-slate-900 px-1.5 py-0.5 font-mono text-[9px] text-slate-300">
                        {entry.meta}
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-[11px] leading-relaxed text-slate-400">{entry.detail}</p>
                </div>
              </div>
            ))}
          </div>

          {scanning && (
            <div className="mt-5 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
              {PIPELINE_STAGES.map((stg, i) => {
                const isPast = i < currentStageIndex
                const isCurrent = i === currentStageIndex
                return (
                  <div
                    key={stg}
                    className={`rounded-lg border p-2.5 text-[10px] font-bold tracking-tight transition-all ${
                      isPast
                        ? "border-emerald-500/30 bg-emerald-950/20 text-emerald-400"
                        : isCurrent
                        ? "border-cyan-500/80 bg-cyan-950/40 text-cyan-300 shadow-sm animate-pulse"
                        : "border-slate-800 bg-slate-950 text-slate-500"
                    }`}
                  >
                    <p className="truncate">{stg}</p>
                    <span className="mt-1 block text-[9px] font-mono opacity-80">
                      {isPast ? "COMPLETED" : isCurrent ? "ACTIVE" : "QUEUED"}
                    </span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {scanResult && (
        <div className="rounded-3xl border border-cyan-500/30 bg-[#0b1221]/95 p-6 shadow-2xl">
          <div className="flex items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-cyan-400" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-300">
                Advanced Trace Intelligence
              </h3>
            </div>
            <span className="rounded-full border border-cyan-500/30 bg-cyan-950/40 px-2.5 py-1 text-[10px] font-bold uppercase text-cyan-300">
              {traceStats.level} risk
            </span>
          </div>

          <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4">
              <p className="text-[10px] uppercase tracking-wider text-slate-500">Risk score</p>
              <p className="mt-2 text-2xl font-black text-white">{traceStats.risk}</p>
            </div>
            <div className="rounded-2xl border border-red-500/20 bg-red-950/20 p-4">
              <p className="text-[10px] uppercase tracking-wider text-red-400">Critical</p>
              <p className="mt-2 text-2xl font-black text-red-300">{traceStats.critical}</p>
            </div>
            <div className="rounded-2xl border border-amber-500/20 bg-amber-950/20 p-4">
              <p className="text-[10px] uppercase tracking-wider text-amber-400">High</p>
              <p className="mt-2 text-2xl font-black text-amber-300">{traceStats.high}</p>
            </div>
            <div className="rounded-2xl border border-slate-700 bg-slate-950/80 p-4">
              <p className="text-[10px] uppercase tracking-wider text-slate-500">Total findings</p>
              <p className="mt-2 text-2xl font-black text-white">{traceStats.total}</p>
            </div>
          </div>

          {scanResult.risk?.ml_engine && (
            <div className="mt-4 rounded-2xl border border-purple-500/30 bg-purple-950/20 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-purple-300" />
                  <div>
                    <p className="text-[10px] font-bold uppercase tracking-wider text-purple-300">
                      Drishti AI Risk Engine
                    </p>
                    <p className="mt-1 text-xs text-slate-300">
                      {scanResult.risk.ml_engine.model ?? "Local security model"} · {scanResult.risk.ml_engine.inference ?? "local inference"}
                    </p>
                  </div>
                </div>
                <span className="rounded-full border border-emerald-500/30 bg-emerald-950/40 px-2.5 py-1 text-[9px] font-bold uppercase text-emerald-300">
                  {scanResult.risk.ml_engine.enabled === false ? "DISABLED" : "ACTIVE"}
                </span>
              </div>
              <div className="mt-3 grid gap-2 sm:grid-cols-3 text-[10px]">
                <div className="rounded-lg border border-purple-500/15 bg-slate-950/50 p-2">
                  <span className="block uppercase tracking-wider text-slate-500">Training samples</span>
                  <strong className="mt-1 block font-mono text-slate-200">{scanResult.risk.ml_engine.training_samples ?? "-"}</strong>
                </div>
                <div className="rounded-lg border border-purple-500/15 bg-slate-950/50 p-2">
                  <span className="block uppercase tracking-wider text-slate-500">Confidence</span>
                  <strong className="mt-1 block font-mono text-cyan-300">{Math.round((scanResult.risk.confidence ?? 0) * 100)}%</strong>
                </div>
                <div className="rounded-lg border border-purple-500/15 bg-slate-950/50 p-2">
                  <span className="block uppercase tracking-wider text-slate-500">Anomaly signal</span>
                  <strong className="mt-1 block font-mono text-amber-300">{Math.round((scanResult.risk.anomaly_score ?? 0) * 100)}%</strong>
                </div>
              </div>
            </div>
          )}

          <div className="mt-6 grid gap-4 lg:grid-cols-[1.25fr_0.75fr]">
            <div className="space-y-3">
              {advancedTrace.map((item) => (
                <div key={item.id} className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-[10px] font-bold uppercase tracking-wider text-cyan-300">{item.step}</p>
                      <h4 className="mt-1 text-base font-bold text-white">{item.title}</h4>
                    </div>
                    <span className={`rounded-full border px-2 py-1 text-[9px] font-bold uppercase ${
                      item.severity.toLowerCase() === "critical"
                        ? "border-red-500/30 bg-red-500/20 text-red-300"
                        : item.severity.toLowerCase() === "high"
                          ? "border-amber-500/30 bg-amber-500/20 text-amber-300"
                          : "border-slate-600 bg-slate-800 text-slate-300"
                    }`}>
                      {item.severity}
                    </span>
                  </div>

                  <div className="mt-3 flex flex-wrap gap-2 text-[10px] text-slate-300">
                    <span className="rounded border border-slate-700 bg-slate-900 px-2 py-1 font-mono">{item.method}</span>
                    <span className="rounded border border-slate-700 bg-slate-900 px-2 py-1 font-mono truncate max-w-[220px]">{item.endpoint}</span>
                  </div>

                  <p className="mt-3 text-sm text-slate-300 leading-relaxed">{item.reasoning}</p>
                  <p className="mt-2 text-[11px] text-slate-400">Impact: {item.impact}</p>
                </div>
              ))}
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4">
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Threat storyline</p>
              <div className="mt-4 space-y-3">
                {advancedTrace.length ? advancedTrace.map((item, idx) => (
                  <div key={`story-${item.id}`} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="flex h-6 w-6 items-center justify-center rounded-full border border-cyan-500/40 bg-cyan-950/50 text-[9px] font-bold text-cyan-300">
                        {idx + 1}
                      </div>
                      {idx !== advancedTrace.length - 1 && <div className="mt-1 h-10 w-px bg-slate-700" />}
                    </div>
                    <div className="flex-1 rounded-xl border border-slate-800 bg-slate-900/90 p-2.5">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{item.step}</p>
                      <p className="mt-1 text-xs text-slate-200">{item.title}</p>
                    </div>
                  </div>
                )) : (
                  <p className="text-sm text-slate-400">No trace events available yet.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Completed Scan Notification Card */}
      {scanResult && !scanning && (
        <div className="rounded-3xl border border-cyan-500/30 bg-gradient-to-r from-[#0f172a] to-[#131d36] p-6 shadow-2xl backdrop-blur-xl animate-fadeIn">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <ShieldAlert className="h-6 w-6 text-red-400" />
                <h3 className="text-xl font-bold text-white">
                  Zero-Trust Scan Completed: {scanResult.summary.vulnerabilities} Finding(s) Verified
                </h3>
              </div>
              <p className="mt-1 text-sm text-slate-300">
                Deterministic BOLA authorization boundaries tested across {scanResult.scan_metadata?.authentication_profiles || 2} identities.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="rounded-xl border border-red-900/50 bg-red-950/40 px-4 py-2 text-center">
                <p className="text-[10px] font-bold text-red-400 uppercase">RISK SCORE</p>
                <p className="text-2xl font-black text-red-300">{scanResult.risk?.score ?? 100}</p>
              </div>

              {onNavigateToDashboard && (
                <button
                  type="button"
                  onClick={onNavigateToDashboard}
                  className="flex items-center gap-2 rounded-xl bg-cyan-500 px-5 py-3 text-xs font-bold text-slate-950 transition hover:bg-cyan-400 shadow-lg shadow-cyan-500/30"
                >
                  VIEW EXECUTIVE DASHBOARD
                  <ChevronRight size={16} />
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
