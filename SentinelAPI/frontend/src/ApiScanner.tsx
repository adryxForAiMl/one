import { useState, useMemo } from "react"
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Eye,
  EyeOff,
  Globe2,
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

type PreflightCheckItem = {
  name: string
  label: string
  status: "pass" | "warn" | "fail"
  detail: string
}

type PreflightResponse = {
  status: string
  state_code: string
  target_url: string
  reachable: boolean
  response_time_ms: number
  root_status_code: number | null
  openapi_discovered: boolean
  openapi_url: string | null
  openapi_version: string | null
  api_title?: string
  auth_required: boolean
  detected_auth_schemes: string[]
  total_endpoints: number
  object_endpoints: number
  collection_endpoints: number
  endpoints?: Endpoint[]
  checklist: PreflightCheckItem[]
  message: string
  what_next: string
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
  "01 TARGET PREFLIGHT",
  "02 API DISCOVERY",
  "03 OPENAPI ANALYSIS",
  "04 AUTHENTICATION",
  "05 IDENTITY MAPPING",
  "06 AUTHORIZATION TESTING",
  "07 OBJECT ACCESS TESTING",
  "08 RESPONSE ANALYSIS",
  "09 VULNERABILITY VERIFICATION",
  "10 RISK INTELLIGENCE",
  "11 ATTACK PATH RECONSTRUCTION",
  "12 REMEDIATION",
  "13 REPORT GENERATION",
]

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
  const [targetUrl, setTargetUrl] = useState("http://localhost:8000")
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

  const normalizedTarget = useMemo(() => {
    return targetUrl.trim().replace(/\/+$/, "")
  }, [targetUrl])

  // Autofill local demo
  const loadLocalDemo = () => {
    setTargetUrl("http://localhost:8000")
    setProfiles([createDefaultProfile(1), createDefaultProfile(2)])
    setPreflightData(null)
    setPreflightError("")
    setScanResult(null)
    setScanError("")
  }

  // Preflight validation execution
  const executePreflight = async () => {
    if (preflightRunning || scanning) return
    if (!normalizedTarget) {
      setPreflightError("Enter a target API URL first.")
      return
    }

    try {
      setPreflightRunning(true)
      setPreflightError("")
      setPreflightData(null)

      const response = await fetch("http://127.0.0.1:8001/preflight", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_url: normalizedTarget }),
      })

      if (!response.ok) {
        throw new Error(`Preflight probe failed with HTTP ${response.status}.`)
      }

      const data: PreflightResponse = await response.json()
      setPreflightData(data)
    } catch (err) {
      setPreflightError(
        err instanceof Error
          ? err.message
          : "Unable to complete preflight check. Ensure SentinelAPI backend is running on port 8001."
      )
    } finally {
      setPreflightRunning(false)
    }
  }

  // Security scan execution
  const startSecurityScan = async () => {
    if (scanning || preflightRunning) return
    if (!preflightData || preflightData.status !== "SCAN_READY") {
      setScanError("Complete preflight validation before starting the zero-trust security scan.")
      return
    }

    try {
      setScanning(true)
      setScanError("")
      setScanResult(null)
      setCurrentStageIndex(0)

      // Simulate step progression smoothly for telemetry
      const interval = setInterval(() => {
        setCurrentStageIndex((prev) => {
          if (prev < PIPELINE_STAGES.length - 2) {
            return prev + 1
          }
          return prev
        })
      }, 350)

      const authPayload = profiles.map((p) => ({
        name: p.name.trim(),
        type: p.type,
        token: p.type === "bearer" ? p.credential.trim() : undefined,
        api_key: p.type === "api-key" ? p.credential.trim() : undefined,
        header: p.header.trim() || "Authorization",
      }))

      const response = await fetch("http://127.0.0.1:8001/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_url: normalizedTarget,
          authentication_profiles: authPayload,
        }),
      })

      clearInterval(interval)
      setCurrentStageIndex(PIPELINE_STAGES.length - 1)

      if (!response.ok) {
        let msg = `Scan failed with HTTP ${response.status}`
        try {
          const body = await response.json()
          if (body?.detail) msg = body.detail
        } catch {
          // ignore
        }
        throw new Error(msg)
      }

      const result: ScanResult = await response.json()
      setScanResult(result)
      if (onScanComplete) {
        onScanComplete(result)
      }
    } catch (err) {
      setScanError(
        err instanceof Error ? err.message : "Error executing zero-trust scan."
      )
    } finally {
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

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-3xl border border-cyan-500/20 bg-gradient-to-b from-slate-900/90 to-slate-950 p-8 shadow-2xl backdrop-blur-xl">
        <div className="absolute right-0 top-0 -mr-16 -mt-16 h-80 w-80 rounded-full bg-cyan-500/5 blur-3xl pointer-events-none" />
        <div className="absolute left-1/3 bottom-0 -mb-20 h-64 w-64 rounded-full bg-red-500/5 blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3.5 py-1 text-xs font-semibold text-cyan-400">
            <Radar className="h-3.5 w-3.5 animate-spin" />
            ZERO-TRUST API SECURITY INTELLIGENCE
          </div>

          <h1 className="mt-4 text-3xl font-extrabold tracking-tight sm:text-5xl text-white">
            Discover. Verify. <span className="text-cyan-400">Explain.</span> Remediate.
          </h1>

          <p className="mt-3 text-base text-slate-400 leading-relaxed">
            Deterministic Broken Object Level Authorization (BOLA) auditing. Reconstruct
            cross-user access paths, collect behavioral response verification evidence, and classify risk
            with local scikit-learn ML intelligence.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={loadLocalDemo}
              className="inline-flex items-center gap-2 rounded-xl border border-cyan-500/40 bg-cyan-950/40 px-4 py-2.5 text-xs font-bold text-cyan-300 transition hover:bg-cyan-900/60 hover:border-cyan-400"
            >
              <Zap className="h-4 w-4 text-cyan-400" />
              TRY LOCAL SECURITY DEMO
            </button>

            <span className="text-xs text-slate-500">
              Populates intentionally vulnerable sandbox at <span className="font-mono text-slate-300">http://localhost:8000</span>
            </span>
          </div>
        </div>
      </div>

      {/* Target API & Action Grid */}
      <div className="grid gap-6 lg:grid-cols-[1.8fr_1.2fr]">
        {/* Left Column: Target Input & Identity Management */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Globe2 className="h-5 w-5 text-cyan-400" />
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Target API Scope
                </h3>
              </div>
              <span className="rounded-full border border-slate-800 bg-slate-950 px-2.5 py-0.5 font-mono text-[10px] text-slate-400">
                Non-Destructive Testing
              </span>
            </div>

            <div className="mt-4">
              <label htmlFor="target-api-scope" className="block text-xs font-semibold text-slate-400 mb-1.5">
                Target Base URL
              </label>
              <div className="flex gap-2">
                <input
                  id="target-api-scope"
                  type="text"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  placeholder="http://localhost:8000 or https://api.target.com"
                  disabled={scanning || preflightRunning}
                  className="flex-1 rounded-xl border border-slate-700/80 bg-slate-950 px-4 py-3 font-mono text-sm text-slate-200 placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                />

                <button
                  type="button"
                  onClick={executePreflight}
                  disabled={preflightRunning || scanning}
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-800 border border-slate-700 px-5 py-3 text-xs font-bold text-slate-200 transition hover:bg-slate-700 hover:text-white disabled:opacity-50"
                >
                  {preflightRunning ? (
                    <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />
                  ) : (
                    <ShieldCheck className="h-4 w-4 text-cyan-400" />
                  )}
                  VALIDATE TARGET
                </button>
              </div>

              {preflightError && (
                <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-900/50 bg-red-950/20 p-3 text-xs text-red-300">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
                  <span>{preflightError}</span>
                </div>
              )}
            </div>
          </div>

          {/* Authentication Identities Section */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md">
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
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:bg-slate-700 hover:text-white disabled:opacity-40"
              >
                <Plus className="h-3.5 w-3.5" />
                Add Identity
              </button>
            </div>

            <div className="mt-4 space-y-3">
              {profiles.map((profile, idx) => (
                <div
                  key={profile.id}
                  className="rounded-xl border border-slate-800/90 bg-slate-950/80 p-4 transition-all hover:border-slate-700"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/60 pb-2.5">
                    <div className="flex items-center gap-2">
                      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-slate-800 text-[10px] font-bold text-cyan-300">
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
                          className="rounded p-1 text-slate-500 hover:text-red-400"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="mt-3 flex items-center gap-2">
                    <KeyRound className="h-4 w-4 shrink-0 text-slate-500" />
                    <input
                      type={profile.showSecret ? "text" : "password"}
                      value={profile.credential}
                      onChange={(e) => updateProfile(profile.id, "credential", e.target.value)}
                      placeholder={
                        profile.type === "bearer"
                          ? "Bearer Token (e.g. token-user-a)"
                          : "API Key Header Value"
                      }
                      disabled={scanning}
                      className="flex-1 rounded-lg border border-slate-800 bg-slate-900/90 px-3 py-1.5 font-mono text-xs text-slate-200 placeholder:text-slate-600 focus:border-cyan-500 focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => updateProfile(profile.id, "showSecret", !profile.showSecret)}
                      className="rounded p-1.5 text-slate-500 hover:text-slate-300"
                    >
                      {profile.showSecret ? <EyeOff size={14} /> : <Eye size={14} />}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Preflight Checklist & Scan Action */}
        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md">
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
                      : "bg-red-500/20 text-red-400 border border-red-500/30"
                  }`}
                >
                  {preflightData.status}
                </span>
              )}
            </div>

            {/* Checklist */}
            <div className="mt-4 space-y-2.5">
              {!preflightData && !preflightRunning && (
                <div className="rounded-xl border border-dashed border-slate-800 bg-slate-950 p-8 text-center text-xs text-slate-500">
                  <Radar className="mx-auto mb-2 h-7 w-7 text-slate-700" />
                  Click <span className="font-semibold text-slate-300">VALIDATE TARGET</span> above to run preflight inspection.
                </div>
              )}

              {preflightRunning && (
                <div className="rounded-xl border border-slate-800 bg-slate-950 p-8 text-center text-xs text-slate-400">
                  <Loader2 className="mx-auto mb-3 h-6 w-6 animate-spin text-cyan-400" />
                  Probing network reachability, OpenAPI endpoints, and authorization boundaries...
                </div>
              )}

              {preflightData &&
                preflightData.checklist.map((item) => (
                  <div
                    key={item.name}
                    className="flex items-start justify-between gap-3 rounded-xl border border-slate-800/80 bg-slate-950 px-3.5 py-2.5 text-xs"
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
                        <p className="font-bold uppercase tracking-wider text-slate-300">
                          {item.label}
                        </p>
                        <p className="mt-0.5 truncate text-[11px] text-slate-500">
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
            </div>

            {/* Scan Action Button */}
            <div className="mt-6 pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={startSecurityScan}
                disabled={!isScanReady || scanning || preflightRunning}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-6 py-4 text-sm font-extrabold text-slate-950 transition-all hover:from-cyan-400 hover:to-blue-500 hover:shadow-lg hover:shadow-cyan-500/25 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {scanning ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    EXECUTING ZERO-TRUST SCAN...
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5 fill-current" />
                    START SECURITY SCAN
                  </>
                )}
              </button>

              {scanError && (
                <div className="mt-3 rounded-lg border border-red-900/50 bg-red-950/20 p-3 text-xs text-red-300">
                  {scanError}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 13-Stage Scan Pipeline Tracker */}
      {scanning && (
        <div className="rounded-2xl border border-cyan-500/30 bg-slate-900/90 p-6 shadow-2xl backdrop-blur-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-cyan-400 animate-ping" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-cyan-300">
                Live Scan Execution Pipeline
              </h3>
            </div>
            <span className="font-mono text-xs text-slate-400">
              Stage {currentStageIndex + 1} of {PIPELINE_STAGES.length}
            </span>
          </div>

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
                      : "border-slate-800 bg-slate-950 text-slate-600"
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
        </div>
      )}

      {/* Completed Scan Notification Card */}
      {scanResult && !scanning && (
        <div className="rounded-3xl border border-red-500/30 bg-slate-900/90 p-6 shadow-2xl backdrop-blur-xl animate-fadeIn">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <ShieldAlert className="h-6 w-6 text-red-400" />
                <h3 className="text-xl font-bold text-white">
                  Zero-Trust Scan Completed: {scanResult.summary.vulnerabilities} Finding(s) Verified
                </h3>
              </div>
              <p className="mt-1 text-sm text-slate-400">
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
                  className="flex items-center gap-2 rounded-xl bg-cyan-500 px-5 py-3 text-xs font-bold text-slate-950 transition hover:bg-cyan-400"
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
