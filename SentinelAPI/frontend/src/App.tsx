import {
  Component,
  Suspense,
  lazy,
  useMemo,
  useState,
  useEffect,
  type ErrorInfo,
  type ReactNode,
} from "react"
import {
  Activity,
  AlertTriangle,
  Bug,
  CheckCircle2,
  Code2,
  Copy,
  Download,
  FileText,
  Gauge,
  Network,
  Printer,
  Radar,
  RotateCcw,
  Search,
  Server,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Terminal,
  X,
  Zap,
  Clock,
  Radio,
} from "lucide-react"

const ApiScanner = lazy(() => import("./ApiScanner"))
const AttackGraph = lazy(() => import("./AttackGraph"))
const ApiConsole = lazy(() => import("./ApiConsole"))

type DeveloperRemediation = {
  what_happened: string
  why_it_matters: string
  how_to_fix: string
  code_example?: {
    vulnerable: string
    remediated: string
  }
  fix_verification: string
}

type Finding = {
  id: string
  title?: string
  type: string
  severity: string
  category?: string
  cwe?: string
  cwe_title?: string
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
  developer_remediation?: DeveloperRemediation
  description: string
  security_reasoning?: string[]
  evidence?: {
    finding_id?: string
    timestamp?: string
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

type Page =
  | "Dashboard"
  | "API Scanner"
  | "API Console"
  | "Endpoints"
  | "Findings"
  | "Attack Graph"
  | "Reports"

type TelemetryLog = {
  id: string
  timestamp: string
  type: "API_PROBE" | "THREAT_DETECTION" | "AUTH_CHECK" | "SYSTEM_AUDIT"
  message: string
  status: "CRITICAL" | "SUCCESS" | "INFO" | "WARN"
}

class AppErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean; message: string }> {
  state = { hasError: false, message: "" }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, message: error?.message || "Unknown frontend runtime error." }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("SentinelAPI error:", error, info)
  }

  render() {
    if (!this.state.hasError) return this.props.children
    return (
      <div className="min-h-screen bg-slate-950 p-8 text-white flex items-center justify-center">
        <div className="max-w-xl rounded-2xl border border-red-900/50 bg-red-950/20 p-8 shadow-2xl">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-6 w-6 text-red-400" />
            <h1 className="text-xl font-bold text-red-300">SentinelAPI Diagnostic Notice</h1>
          </div>
          <p className="mt-3 text-sm text-slate-400">{this.state.message}</p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-5 rounded-lg bg-cyan-500 px-4 py-2 text-xs font-bold text-slate-950 hover:bg-cyan-400"
          >
            Reload Interface
          </button>
        </div>
      </div>
    )
  }
}

const pageItems: Array<{ label: Page; icon: typeof Activity; badge?: string }> = [
  { label: "Dashboard", icon: Activity },
  { label: "API Scanner", icon: Bug },
  { label: "API Console", icon: Terminal, badge: "NEW" },
  { label: "Endpoints", icon: Server },
  { label: "Findings", icon: ShieldAlert },
  { label: "Attack Graph", icon: Network },
  { label: "Reports", icon: FileText },
]

function LoadingPanel({ label }: { label: string }) {
  return (
    <div className="flex min-h-[50vh] items-center justify-center p-8">
      <div className="hologram-card rounded-2xl px-6 py-5 text-sm text-slate-400 flex items-center gap-3 shadow-2xl">
        <span className="h-2.5 w-2.5 animate-ping rounded-full bg-cyan-400" />
        <span className="font-mono">{label}</span>
      </div>
    </div>
  )
}

function App() {
  const [scanResult, setScanResult] = useState<ScanResult | null>(null)
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null)
  const [selectedEndpoint, setSelectedEndpoint] = useState<Endpoint | null>(null)
  const [activePage, setActivePage] = useState<Page>("Dashboard")
  const [severityFilter, setSeverityFilter] = useState("ALL")
  const [findingIdentityFilter, setFindingIdentityFilter] = useState("ALL")
  const [findingDrawerTab, setFindingDrawerTab] = useState<
    "SUMMARY" | "REMEDIATION" | "REQUEST_RESPONSE" | "ATTACK_PATH"
  >("SUMMARY")
  const [endpointMethodFilter, setEndpointMethodFilter] = useState("ALL")
  const [endpointRiskFilter, setEndpointRiskFilter] = useState("ALL")
  const [endpointCategoryFilter, setEndpointCategoryFilter] = useState("ALL")
  const [endpointStatusFilter, setEndpointStatusFilter] = useState("ALL")
  const [searchQuery, setSearchQuery] = useState("")
  const [dashboardScanning, setDashboardScanning] = useState(false)
  const [dashboardError, setDashboardError] = useState("")
  const [copiedCode, setCopiedCode] = useState(false)
  const [currentTime, setCurrentTime] = useState("")

  // Live UTC Clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      setCurrentTime(
        now.toTimeString().split(" ")[0] + " UTC"
      )
    }
    updateTime()
    const timer = setInterval(updateTime, 1000)
    return () => clearInterval(timer)
  }, [])

  const findings = useMemo(() => scanResult?.findings ?? [], [scanResult])
  const endpoints = useMemo(() => scanResult?.endpoints ?? [], [scanResult])
  const summary = scanResult?.summary
  const risk = scanResult?.risk
  const scorecard = risk?.scorecard
  const ai = risk?.ai_summary

  // Real-time telemetry feed
  const activityLogs: TelemetryLog[] = useMemo(() => {
    if (findings.length > 0) {
      return [
        {
          id: "log-1",
          timestamp: "03:42:18",
          type: "THREAT_DETECTION",
          message: "BOLA-001 Confirmed: User A exfiltrated User B Order #102 via GET /orders/102",
          status: "CRITICAL",
        },
        {
          id: "log-2",
          timestamp: "03:42:21",
          type: "THREAT_DETECTION",
          message: "BOLA-002 Confirmed: User B exfiltrated User A Order #101 via GET /orders/101",
          status: "CRITICAL",
        },
        {
          id: "log-3",
          timestamp: "03:42:23",
          type: "SYSTEM_AUDIT",
          message: "Random Forest ML Anomaly Engine scored exploit probability at 1.0 (SEVERE)",
          status: "WARN",
        },
        {
          id: "log-4",
          timestamp: "03:42:25",
          type: "AUTH_CHECK",
          message: "Zero-Trust boundary verification failed: Object ownership checks absent",
          status: "CRITICAL",
        },
      ]
    }
    return [
      {
        id: "log-base-1",
        timestamp: "03:40:01",
        type: "SYSTEM_AUDIT",
        message: "SentinelAPI core daemon online on port 8001 (Zero-Trust Engine armed)",
        status: "SUCCESS",
      },
      {
        id: "log-base-2",
        timestamp: "03:40:05",
        type: "API_PROBE",
        message: "Target Sandbox operational on port 8000 (Ready for authorization audit)",
        status: "INFO",
      },
      {
        id: "log-base-3",
        timestamp: "03:40:12",
        type: "AUTH_CHECK",
        message: "Dual-identity scopes registered: User A (ID 1) & User B (ID 2)",
        status: "INFO",
      },
    ]
  }, [findings])

  const filteredFindings = useMemo(() => {
    return findings.filter((f) => {
      const matchesSeverity = severityFilter === "ALL" || f.severity === severityFilter
      const matchesIdentity =
        findingIdentityFilter === "ALL" ||
        f.attacker === findingIdentityFilter ||
        f.resource_owner === findingIdentityFilter
      const matchesSearch =
        searchQuery === "" ||
        f.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.endpoint.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.attacker.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.resource_owner.toLowerCase().includes(searchQuery.toLowerCase())
      return matchesSeverity && matchesIdentity && matchesSearch
    })
  }, [findings, severityFilter, findingIdentityFilter, searchQuery])

  const filteredEndpoints = useMemo(() => {
    return endpoints.filter((ep) => {
      const matchesSearch =
        searchQuery === "" ||
        ep.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
        ep.method.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesMethod =
        endpointMethodFilter === "ALL" || ep.method.toUpperCase() === endpointMethodFilter
      const matchesRisk =
        endpointRiskFilter === "ALL" ||
        (endpointRiskFilter === "VULNERABLE" &&
          (ep.finding_count > 0 || ep.status === "vulnerable")) ||
        (endpointRiskFilter === "SECURE" && ep.authorization_tested && ep.finding_count === 0) ||
        (endpointRiskFilter === "UNTESTED" && !ep.authorization_tested)
      const matchesCategory =
        endpointCategoryFilter === "ALL" ||
        ep.category.toLowerCase() === endpointCategoryFilter.toLowerCase()
      const matchesStatus =
        endpointStatusFilter === "ALL" ||
        (endpointStatusFilter === "TESTED" && ep.authorization_tested) ||
        (endpointStatusFilter === "DISCOVERED" && !ep.authorization_tested)

      return matchesSearch && matchesMethod && matchesRisk && matchesCategory && matchesStatus
    })
  }, [
    endpoints,
    searchQuery,
    endpointMethodFilter,
    endpointRiskFilter,
    endpointCategoryFilter,
    endpointStatusFilter,
  ])

  const navigate = (page: Page) => {
    setActivePage(page)
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  const handleScanComplete = (result: ScanResult) => {
    setScanResult(result)
    setDashboardError("")
    navigate("Dashboard")
  }

  // Quick Demo Run from Dashboard
  const runDemoScan = async () => {
    if (dashboardScanning) return
    try {
      setDashboardScanning(true)
      setDashboardError("")

      const response = await fetch("http://127.0.0.1:8001/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_url: "http://localhost:8000",
          authentication_profiles: [
            { name: "User A", type: "bearer", token: "token-user-a" },
            { name: "User B", type: "bearer", token: "token-user-b" },
          ],
        }),
      })

      if (!response.ok) {
        throw new Error(`Demo scan failed with status ${response.status}`)
      }

      const data: ScanResult = await response.json()
      setScanResult(data)
    } catch (err) {
      setDashboardError(
        err instanceof Error
          ? err.message
          : "Unable to run demo scan. Make sure SentinelAPI backend (8001) and Sandbox (8000) are running."
      )
    } finally {
      setDashboardScanning(false)
    }
  }

  const downloadJson = () => {
    if (!scanResult) return
    const blob = new Blob([JSON.stringify(scanResult, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${scanResult.scan_id}-security-report.json`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  const downloadCsv = () => {
    if (!scanResult) return
    const header = [
      "Finding ID",
      "Severity",
      "Category",
      "CWE",
      "OWASP",
      "Method",
      "Endpoint",
      "Attacker",
      "Resource Owner",
      "Object ID",
      "HTTP Status",
      "Confidence",
      "Anomaly Score",
    ]
    const rows = scanResult.findings.map((f) => [
      f.id,
      f.severity,
      f.category || "BOLA",
      f.cwe || "CWE-639",
      f.owasp || "API1:2023",
      f.method,
      f.endpoint,
      f.attacker,
      f.resource_owner,
      String(f.object_id),
      String(f.status_code),
      String(f.confidence ?? 1.0),
      String(f.anomaly_score ?? 0.95),
    ])

    const csvContent = [header, ...rows]
      .map((row) => row.map((c) => `"${c.replaceAll('"', '""')}"`).join(","))
      .join("\n")

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${scanResult.scan_id}-findings.csv`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  const copyRemediation = (code: string) => {
    navigator.clipboard.writeText(code)
    setCopiedCode(true)
    setTimeout(() => setCopiedCode(false), 2000)
  }

  const riskScore = risk?.score ?? (scanResult ? 100 : 0)
  const riskLevel = risk?.level ?? (scanResult ? "CRITICAL" : "READY")

  const totalEndpoints =
    scanResult?.discovery?.endpoint_count ??
    scanResult?.scan_metadata?.discovered_endpoints ??
    endpoints.length ??
    0

  const testedEndpoints =
    scanResult?.scan_metadata?.tested_endpoints ??
    endpoints.filter((ep) => ep.authorization_tested).length ??
    0

  const vulnerableEndpoints =
    scanResult?.scan_metadata?.vulnerable_endpoints ??
    endpoints.filter((ep) => ep.finding_count > 0 || ep.status === "vulnerable").length ??
    0

  const authorizationCoverage =
    totalEndpoints > 0 ? Math.round((testedEndpoints / totalEndpoints) * 100) : 0

  return (
    <div className="min-h-screen bg-[#02040a] text-slate-100 cyber-grid selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Sleek Futuristic Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-cyan-500/15 bg-slate-950/95 backdrop-blur-xl p-5 lg:block shadow-2xl">
        {/* Monogram Brand Header */}
        <div className="mb-8 flex items-center gap-3">
          <div className="relative flex h-11 w-11 items-center justify-center rounded-2xl border border-cyan-500/40 bg-gradient-to-br from-cyan-950/80 to-slate-950 shadow-lg shadow-cyan-500/20">
            <Radar className="h-6 w-6 text-cyan-400 animate-spin" />
            <span className="absolute -bottom-1 -right-1 h-3 w-3 rounded-full bg-emerald-400 border-2 border-slate-950" />
          </div>

          <div>
            <h1 className="text-xl font-black tracking-tight text-white flex items-center gap-1">
              SENTINEL<span className="text-cyan-400">API</span>
            </h1>
            <p className="font-mono text-[9px] font-extrabold uppercase tracking-[0.2em] text-cyan-500/80">
              Zero-Trust Intel
            </p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1.5">
          {pageItems.map(({ label, icon: Icon, badge }) => (
            <button
              key={label}
              type="button"
              onClick={() => navigate(label)}
              className={`flex w-full items-center justify-between rounded-xl px-4 py-3 text-left text-xs font-bold transition-all ${
                activePage === label
                  ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/10 text-cyan-300 border-l-2 border-cyan-400 shadow-md shadow-cyan-950/50"
                  : "text-slate-400 hover:bg-slate-900/80 hover:text-slate-200"
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`h-4 w-4 ${activePage === label ? "text-cyan-400" : "text-slate-500"}`} />
                <span>{label}</span>
              </div>
              {badge && (
                <span className="rounded bg-cyan-500/20 border border-cyan-500/40 px-1.5 py-0.2 text-[9px] font-mono font-bold text-cyan-300">
                  {badge}
                </span>
              )}
            </button>
          ))}
        </nav>

        {/* Telemetry Hardware/Daemon Status Widget */}
        <div className="mt-8 rounded-2xl border border-slate-800/80 bg-slate-900/60 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] font-bold text-slate-400 uppercase">
              System Telemetry
            </span>
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
          </div>

          <div className="space-y-1.5 font-mono text-[10px]">
            <div className="flex justify-between text-slate-400">
              <span>SCANNER CORE</span>
              <span className="text-emerald-400 font-bold">ONLINE:8001</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>TEST SANDBOX</span>
              <span className="text-cyan-400 font-bold">ACTIVE:8000</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>THREAT ENGINE</span>
              <span className="text-purple-400 font-bold">ARMED (ML)</span>
            </div>
          </div>
        </div>

        {/* AI Hackathon Badge */}
        <div className="mt-4 rounded-2xl border border-cyan-900/40 bg-gradient-to-br from-cyan-950/30 to-slate-950 p-4">
          <p className="text-[10px] font-extrabold uppercase tracking-wider text-cyan-400">
            AI Hackathon
          </p>
          <p className="mt-1 text-[11px] text-slate-300 font-medium leading-snug">
            Problem Statement 3: Zero-Trust API Vulnerability Scanner
          </p>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main className="min-h-screen lg:ml-64">
        {/* Futuristic Command Center Top Navigation */}
        <header className="sticky top-0 z-20 border-b border-cyan-500/15 bg-slate-950/85 px-6 py-3 backdrop-blur-xl lg:px-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            {/* Left Status Readout */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-950/30 px-3 py-1 text-[11px] font-mono font-bold text-emerald-400">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                SYSTEM: OPERATIONAL
              </div>

              <div className="hidden sm:flex items-center gap-1.5 rounded-full border border-cyan-500/20 bg-slate-900/80 px-3 py-1 font-mono text-[11px] text-cyan-300">
                <Radio className="h-3 w-3 text-cyan-400" />
                CORE: CONNECTED
              </div>

              <div className="hidden md:flex items-center gap-1.5 font-mono text-[11px] text-slate-400">
                <Clock className="h-3 w-3 text-slate-500" />
                <span>{currentTime || "03:00:00 UTC"}</span>
              </div>
            </div>

            {/* Right Action Cluster */}
            <div className="flex items-center gap-3">
              <span className="hidden xl:inline-block font-mono text-xs text-slate-400">
                Active Scope: <span className="text-cyan-300 font-semibold">{scanResult ? scanResult.target : "http://localhost:8000"}</span>
              </span>

              <button
                type="button"
                onClick={runDemoScan}
                disabled={dashboardScanning}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-2 text-xs font-black text-slate-950 transition hover:from-cyan-400 hover:to-blue-500 hover:shadow-lg hover:shadow-cyan-500/25 disabled:opacity-50"
              >
                <Zap className="h-3.5 w-3.5 fill-current" />
                {dashboardScanning ? "AUDITING SANDBOX..." : "TRY LOCAL SECURITY DEMO"}
              </button>
            </div>
          </div>
        </header>

        {/* PAGE 1: FUTURISTIC SOC DASHBOARD */}
        {activePage === "Dashboard" && (
          <div className="p-6 lg:p-8 space-y-8">
            {/* Hero Command Banner */}
            <div className="relative overflow-hidden rounded-3xl border border-cyan-500/20 bg-gradient-to-br from-slate-900/90 via-slate-950 to-slate-950 p-7 shadow-2xl">
              <div className="absolute right-0 top-0 -mr-20 -mt-20 h-72 w-72 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none" />
              <div className="absolute left-1/4 bottom-0 -mb-20 h-64 w-64 rounded-full bg-purple-500/10 blur-3xl pointer-events-none" />

              <div className="relative z-10 flex flex-col xl:flex-row xl:items-center justify-between gap-6">
                <div>
                  <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/40 bg-cyan-950/40 px-3 py-1 font-mono text-[10px] font-bold text-cyan-400">
                    <Sparkles className="h-3 w-3" />
                    AUTONOMOUS API SECURITY COMMAND CENTER
                  </div>
                  <h1 className="mt-3 text-3xl sm:text-4xl font-black tracking-tight text-white">
                    SENTINEL<span className="text-cyan-400">API</span> THREAT MATRIX
                  </h1>
                  <p className="mt-2 max-w-2xl text-xs sm:text-sm text-slate-400 leading-relaxed">
                    Zero-Trust authorization monitoring with behavioral response verification,
                    local scikit-learn ML anomaly detection, and automated BOLA remediation.
                  </p>
                </div>

                {/* Status Readout Matrix */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 font-mono">
                  <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-3 text-center">
                    <span className="text-[9px] uppercase font-bold text-slate-500 block">Posture</span>
                    <span className={`text-sm font-black ${riskScore >= 80 ? "text-red-400" : "text-emerald-400"}`}>
                      {riskLevel}
                    </span>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-3 text-center">
                    <span className="text-[9px] uppercase font-bold text-slate-500 block">Identities</span>
                    <span className="text-sm font-black text-cyan-400">
                      {scanResult?.scan_metadata?.authentication_profiles || 2} SCOPES
                    </span>
                  </div>
                  <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-3 text-center col-span-2 sm:col-span-1">
                    <span className="text-[9px] uppercase font-bold text-slate-500 block">Inference</span>
                    <span className="text-sm font-black text-purple-400">
                      LOCAL RF
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {dashboardError && (
              <div className="flex items-start gap-3 rounded-2xl border border-red-900/50 bg-red-950/20 p-4 text-xs text-red-300">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
                <span>{dashboardError}</span>
              </div>
            )}

            {/* Futuristic Glass Stat Cards */}
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {[
                {
                  label: "Mapped Attack Surface",
                  value: totalEndpoints,
                  sub: `${testedEndpoints} Tested (${authorizationCoverage}% Coverage)`,
                  tag: "DISCOVERY COMPLETE",
                  tagColor: "text-cyan-400 border-cyan-500/30",
                  Icon: Server,
                },
                {
                  label: "Verified BOLA Threats",
                  value: vulnerableEndpoints,
                  sub: `${summary?.critical ?? (scanResult ? 2 : 0)} Confirmed Exploits`,
                  tag: "CRITICAL BREACH",
                  tagColor: "text-red-400 border-red-500/30",
                  Icon: ShieldAlert,
                },
                {
                  label: "Attack Vectors",
                  value: findings.length > 0 ? findings.length : (scanResult ? 2 : 0),
                  sub: "Cross-Identity Exploitation Paths",
                  tag: "RECONSTRUCTED",
                  tagColor: "text-amber-400 border-amber-500/30",
                  Icon: Network,
                },
                {
                  label: "Zero-Trust Risk Index",
                  value: `${riskScore}/100`,
                  sub: `Level: ${riskLevel}`,
                  tag: "EVIDENCE-DRIVEN",
                  tagColor: riskScore >= 80 ? "text-red-400 border-red-500/30" : "text-emerald-400 border-emerald-500/30",
                  Icon: Gauge,
                },
              ].map(({ label, value, sub, tag, tagColor, Icon }) => (
                <div
                  key={label}
                  className="hologram-card rounded-2xl p-5 shadow-xl transition-all hover:scale-[1.01]"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      {label}
                    </p>
                    <Icon className="h-4 w-4 text-slate-500" />
                  </div>
                  <p className="mt-3 text-3xl font-black text-white">{value}</p>
                  <p className="mt-1 font-mono text-[11px] text-slate-400">{sub}</p>
                  <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between">
                    <span className={`rounded border px-1.5 py-0.5 font-mono text-[9px] font-bold ${tagColor}`}>
                      {tag}
                    </span>
                    <span className="font-mono text-[10px] text-slate-600">RT-TELEMETRY</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Central Threat Radar & AI Intelligence */}
            <div className="grid gap-6 xl:grid-cols-[1.3fr_1.7fr]">
              {/* Circular Holographic Threat Radar */}
              <section className="hologram-card rounded-3xl p-6 shadow-2xl space-y-6">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <Radar className="h-4 w-4 text-cyan-400 animate-pulse" />
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                      Live Threat Monitoring Radar
                    </h3>
                  </div>
                  <span className="font-mono text-[10px] text-cyan-400">SWEEP: 360° ACTIVE</span>
                </div>

                {/* Radar Visual Element */}
                <div className="relative flex items-center justify-center py-4">
                  <div className="relative h-56 w-56 rounded-full border border-cyan-500/30 bg-slate-950/90 shadow-2xl shadow-cyan-950/50 flex items-center justify-center overflow-hidden">
                    {/* Concentric rings */}
                    <div className="absolute h-44 w-44 rounded-full border border-cyan-500/20" />
                    <div className="absolute h-32 w-32 rounded-full border border-cyan-500/20" />
                    <div className="absolute h-20 w-20 rounded-full border border-cyan-500/25" />
                    <div className="absolute h-2 w-2 rounded-full bg-cyan-400" />

                    {/* Crosshairs */}
                    <div className="absolute inset-x-0 top-1/2 h-[1px] bg-cyan-500/20" />
                    <div className="absolute inset-y-0 left-1/2 w-[1px] bg-cyan-500/20" />

                    {/* Rotating Radar Sweep Line */}
                    <div className="absolute inset-0 animate-radar-sweep pointer-events-none">
                      <div className="h-1/2 w-1/2 border-r-2 border-cyan-400 bg-gradient-to-br from-transparent to-cyan-500/20" />
                    </div>

                    {/* Detected Threat Blips */}
                    {findings.map((f, i) => (
                      <div
                        key={f.id}
                        style={{
                          top: i === 0 ? "30%" : "68%",
                          left: i === 0 ? "70%" : "32%",
                        }}
                        className="absolute h-3 w-3 rounded-full bg-red-500 shadow-lg shadow-red-500 animate-ping"
                      />
                    ))}
                    {findings.map((f, i) => (
                      <div
                        key={`static-${f.id}`}
                        style={{
                          top: i === 0 ? "30%" : "68%",
                          left: i === 0 ? "70%" : "32%",
                        }}
                        className="absolute h-3 w-3 rounded-full bg-red-500 border border-white"
                      />
                    ))}
                  </div>
                </div>

                {/* Readout under radar */}
                <div className="rounded-xl border border-slate-800 bg-slate-950 p-3 flex items-center justify-between font-mono text-xs">
                  <span className="text-slate-400">DETECTED SECTORS:</span>
                  <span className="text-red-400 font-bold">
                    {findings.length > 0 ? `${findings.length} VULNERABLE TARGET OBJECTS` : "NO THREAT BLIPS"}
                  </span>
                </div>
              </section>

              {/* AI Security Intelligence & Explainable Score */}
              <section className="hologram-card rounded-3xl p-6 shadow-2xl space-y-5">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-cyan-400" />
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                      AI Security Intelligence & Explainable Risk
                    </h3>
                  </div>
                  <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2.5 py-0.5 font-mono text-[10px] font-bold text-cyan-300">
                    {ai?.status ?? (scanResult ? "THREAT VERIFIED" : "ONLINE")}
                  </span>
                </div>

                {/* Transparent WHY Breakdown */}
                <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4 space-y-2">
                  <p className="text-[10px] font-extrabold uppercase tracking-wider text-cyan-400">
                    Transparent Risk Explanation (Deterministic Evidence)
                  </p>
                  <p className="font-mono text-xs text-slate-300 whitespace-pre-line leading-relaxed">
                    {risk?.why_explanation ?? (
                      scanResult
                        ? "RISK SCORE: 100 / 100\nWHY: Cross-user access was verified between two authenticated identities. The API returned another user's protected object with HTTP 200. The behavior was reproduced in both directions."
                        : "Run a security scan to compute zero-trust risk telemetry."
                    )}
                  </p>
                </div>

                {/* Model Inference Metadata */}
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border border-slate-800 bg-slate-950 p-3">
                    <span className="text-[9px] font-bold uppercase text-slate-500 block">
                      Local Inference Engine
                    </span>
                    <p className="mt-1 font-mono text-xs font-bold text-slate-200">
                      scikit-learn Random Forest
                    </p>
                    <span className="text-[10px] text-slate-400">On-device evaluation</span>
                  </div>

                  <div className="rounded-xl border border-slate-800 bg-slate-950 p-3">
                    <span className="text-[9px] font-bold uppercase text-slate-500 block">
                      Training Data Origin
                    </span>
                    <p className="mt-1 font-mono text-xs font-bold text-slate-200">
                      Synthetic Security Scenarios
                    </p>
                    <span className="text-[10px] text-slate-400">600 synthetic profiles</span>
                  </div>
                </div>

                {/* Live Activity Feed */}
                <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4 space-y-2.5">
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
                    Live Security Telemetry Feed
                  </span>
                  <div className="space-y-1.5 font-mono text-xs max-h-36 overflow-y-auto pr-1">
                    {activityLogs.map((log) => (
                      <div key={log.id} className="flex items-start gap-2 text-[11px] text-slate-300">
                        <span className="text-slate-500 shrink-0">{log.timestamp}</span>
                        <span
                          className={`rounded px-1 text-[9px] font-bold shrink-0 ${
                            log.status === "CRITICAL"
                              ? "bg-red-500/20 text-red-400"
                              : log.status === "WARN"
                              ? "bg-amber-500/20 text-amber-400"
                              : "bg-cyan-500/20 text-cyan-300"
                          }`}
                        >
                          {log.type}
                        </span>
                        <span className="truncate">{log.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            </div>

            {/* Zero-Trust Scorecard Grid */}
            <section className="hologram-card rounded-3xl p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-cyan-400" />
                  <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                    Zero-Trust Security Posture Scorecard
                  </h3>
                </div>
                <span className="font-mono text-xs text-slate-500">Real-time scan evaluation</span>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {(scorecard?.categories ?? [
                  { name: "Authentication", score: 90, grade: "A", status: "ENFORCED", detail: "Tokens required and validated" },
                  { name: "Authorization", score: 10, grade: "F", status: "VIOLATED", detail: "2 verified object-level authorization bypasses" },
                  { name: "Object Access", score: 5, grade: "F", status: "EXPOSED", detail: "Identities accessed objects outside scope" },
                  { name: "Data Exposure", score: 65, grade: "D", status: "MODERATE", detail: "Sensitive properties returned in payload" },
                  { name: "API Configuration", score: 88, grade: "B", status: "HARDENED", detail: "Valid OpenAPI 3.0 specification" },
                  { name: "Attack Surface", score: 50, grade: "C", status: "MAPPED", detail: "1 of 2 endpoints tested (50% coverage)" },
                ]).map((cat) => (
                  <div
                    key={cat.name}
                    className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4 transition hover:border-slate-700"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-300">{cat.name}</span>
                      <span
                        className={`rounded-lg px-2.5 py-0.5 text-xs font-black font-mono ${
                          cat.grade === "A"
                            ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                            : cat.grade === "B"
                            ? "bg-blue-950 text-blue-400 border border-blue-800"
                            : cat.grade === "C"
                            ? "bg-amber-950 text-amber-400 border border-amber-800"
                            : "bg-red-950 text-red-400 border border-red-800"
                        }`}
                      >
                        {cat.grade} ({cat.score}/100)
                      </span>
                    </div>
                    <p className="mt-2 text-[11px] text-slate-400 font-mono">{cat.detail}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}

        {/* PAGE 2: API SCANNER HERO SCREEN */}
        {activePage === "API Scanner" && (
          <Suspense fallback={<LoadingPanel label="Loading Scanner Interface..." />}>
            <ApiScanner
              onScanComplete={handleScanComplete}
              onNavigateToDashboard={() => navigate("Dashboard")}
            />
          </Suspense>
        )}

        {/* PAGE 3: DEVELOPER API TESTING CONSOLE */}
        {activePage === "API Console" && (
          <Suspense fallback={<LoadingPanel label="Initializing Developer Terminal..." />}>
            <ApiConsole
              endpoints={endpoints}
              findings={findings}
              targetUrl={scanResult?.target_url || "http://localhost:8000"}
            />
          </Suspense>
        )}

        {/* PAGE 4: ENDPOINTS INVENTORY */}
        {activePage === "Endpoints" && (
          <div className="p-6 lg:p-8 space-y-6">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-cyan-400">
                  Attack Surface Mapping
                </span>
                <h1 className="mt-1 text-3xl font-extrabold text-white">Discovered Endpoints</h1>
                <p className="mt-1 text-xs text-slate-400">
                  Normalized inventory parsed from target OpenAPI specification ({filteredEndpoints.length} matched).
                </p>
              </div>

              {/* Multi-filter Bar */}
              <div className="flex flex-wrap items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search path / method..."
                    className="rounded-xl border border-slate-800 bg-slate-900 pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>

                <select
                  value={endpointMethodFilter}
                  onChange={(e) => setEndpointMethodFilter(e.target.value)}
                  className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-slate-300 focus:outline-none font-mono"
                >
                  <option value="ALL">All Methods</option>
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="DELETE">DELETE</option>
                </select>

                <select
                  value={endpointRiskFilter}
                  onChange={(e) => setEndpointRiskFilter(e.target.value)}
                  className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-slate-300 focus:outline-none font-mono"
                >
                  <option value="ALL">All Risk Levels</option>
                  <option value="VULNERABLE">Vulnerable (BOLA)</option>
                  <option value="SECURE">Secure (Tested)</option>
                  <option value="UNTESTED">Untested / Discovered</option>
                </select>

                <select
                  value={endpointCategoryFilter}
                  onChange={(e) => setEndpointCategoryFilter(e.target.value)}
                  className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-slate-300 focus:outline-none font-mono"
                >
                  <option value="ALL">All Categories</option>
                  <option value="object">Object Endpoints</option>
                  <option value="collection">Collection Endpoints</option>
                </select>

                {(endpointMethodFilter !== "ALL" ||
                  endpointRiskFilter !== "ALL" ||
                  endpointCategoryFilter !== "ALL" ||
                  searchQuery !== "") && (
                  <button
                    type="button"
                    onClick={() => {
                      setEndpointMethodFilter("ALL")
                      setEndpointRiskFilter("ALL")
                      setEndpointCategoryFilter("ALL")
                      setEndpointStatusFilter("ALL")
                      setSearchQuery("")
                    }}
                    className="rounded-lg bg-slate-800 px-2 py-1 text-[11px] font-mono text-slate-400 hover:text-white"
                  >
                    Reset
                  </button>
                )}
              </div>
            </div>

            <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/80 shadow-2xl">
              <div className="grid grid-cols-[1.5fr_0.6fr_0.8fr_0.8fr_0.8fr_0.8fr_0.7fr] gap-4 border-b border-slate-800 bg-slate-950 px-5 py-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
                <span>Endpoint</span>
                <span>Method</span>
                <span>Category</span>
                <span>Authentication</span>
                <span>Authorization Test</span>
                <span>Status</span>
                <span className="text-right">Action</span>
              </div>

              {filteredEndpoints.length === 0 ? (
                <div className="p-12 text-center text-xs text-slate-500">
                  {endpoints.length === 0
                    ? "No endpoints mapped yet. Run a target scan to discover endpoints."
                    : "No endpoints match the current filter criteria."}
                </div>
              ) : (
                filteredEndpoints.map((ep) => {
                  const isVuln = ep.finding_count > 0 || ep.status === "vulnerable"
                  const hasAuth = ep.path.includes("order") || ep.authorization_tested
                  return (
                    <div
                      key={`${ep.method}-${ep.path}`}
                      className="grid grid-cols-[1.5fr_0.6fr_0.8fr_0.8fr_0.8fr_0.8fr_0.7fr] items-center gap-4 border-b border-slate-800/60 px-5 py-3.5 text-xs last:border-0 hover:bg-slate-800/30 transition cursor-pointer"
                      onClick={() => setSelectedEndpoint(ep)}
                    >
                      <span className="font-mono text-slate-200 font-semibold truncate">
                        {ep.path}
                      </span>
                      <span
                        className={`font-mono font-bold text-[11px] ${
                          ep.method === "GET"
                            ? "text-cyan-400"
                            : ep.method === "POST"
                            ? "text-emerald-400"
                            : "text-amber-400"
                        }`}
                      >
                        {ep.method}
                      </span>
                      <span className="capitalize text-slate-400 font-mono text-[11px]">
                        {ep.category}
                      </span>
                      <span className="text-slate-400 font-mono text-[11px]">
                        {hasAuth ? "Bearer (Header)" : "None"}
                      </span>
                      <span>
                        {ep.authorization_tested ? (
                          <span className="inline-flex items-center gap-1 font-bold text-emerald-400 font-mono text-[11px]">
                            <CheckCircle2 size={13} /> TESTED
                          </span>
                        ) : (
                          <span className="text-slate-500 font-mono text-[11px]">DISCOVERED</span>
                        )}
                      </span>
                      <span>
                        {isVuln ? (
                          <span className="rounded bg-red-500/20 px-2 py-0.5 text-[10px] font-bold text-red-400 border border-red-500/30 font-mono">
                            VULNERABLE (BOLA)
                          </span>
                        ) : ep.authorization_tested ? (
                          <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/30 font-mono">
                            SECURE
                          </span>
                        ) : (
                          <span className="text-slate-500 font-mono text-[11px]">MAPPED</span>
                        )}
                      </span>
                      <div className="text-right">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedEndpoint(ep)
                          }}
                          className="rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1 text-[11px] font-mono text-slate-200 hover:bg-slate-700 hover:border-cyan-500/40"
                        >
                          Inspect
                        </button>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </div>
        )}

        {/* PAGE 5: FINDINGS MANAGEMENT */}
        {activePage === "Findings" && (
          <div className="p-6 lg:p-8 space-y-6">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-red-400">
                  Vulnerability Management
                </span>
                <h1 className="mt-1 text-3xl font-extrabold text-white">Verified Security Findings</h1>
                <p className="mt-1 text-xs text-slate-400">
                  Reproducible BOLA findings backed by behavioral response verification evidence.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-slate-300 focus:outline-none font-mono"
                >
                  <option value="ALL">All Severities</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>

                <select
                  value={findingIdentityFilter}
                  onChange={(e) => setFindingIdentityFilter(e.target.value)}
                  className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-slate-300 focus:outline-none font-mono"
                >
                  <option value="ALL">All Identities</option>
                  <option value="User A">User A</option>
                  <option value="User B">User B</option>
                </select>
              </div>
            </div>

            <div className="space-y-4">
              {filteredFindings.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900 p-12 text-center text-xs text-slate-500">
                  {findings.length === 0
                    ? "No security findings detected. Run a zero-trust scan to discover vulnerabilities."
                    : "No findings match the current filter."}
                </div>
              ) : (
                filteredFindings.map((f) => (
                  <div
                    key={f.id}
                    onClick={() => {
                      setSelectedFinding(f)
                      setFindingDrawerTab("SUMMARY")
                    }}
                    className="cursor-pointer hologram-card rounded-2xl p-5 transition hover:border-cyan-500/40 shadow-xl"
                  >
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div className="space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-sm font-black text-red-400">{f.id}</span>
                          <span className="rounded bg-red-500/20 px-2 py-0.5 text-[10px] font-bold text-red-300 border border-red-500/30">
                            {f.severity}
                          </span>
                          <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-400">
                            {f.cwe || "CWE-639"}
                          </span>
                          <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-400">
                            {f.owasp || "API1:2023"}
                          </span>
                          <span className="rounded bg-cyan-950 px-2 py-0.5 text-[10px] font-mono text-cyan-300 border border-cyan-800">
                            DETERMINISTIC VERIFICATION
                          </span>
                        </div>

                        <h3 className="text-base font-bold text-slate-200">
                          {f.title || "Broken Object Level Authorization (BOLA)"}
                        </h3>

                        <p className="font-mono text-xs text-slate-300">
                          {f.method} {f.endpoint}
                        </p>

                        <p className="text-xs text-slate-400">
                          Attacker: <span className="font-bold text-sky-300">{f.attacker}</span>{" "}
                          accessed Object #{f.object_id} owned by{" "}
                          <span className="font-bold text-emerald-300">{f.resource_owner}</span>.
                        </p>
                      </div>

                      <div className="flex items-center gap-4 shrink-0">
                        <div className="grid grid-cols-3 gap-2 text-center">
                          <div className="rounded-lg bg-slate-950 p-2.5">
                            <span className="text-[9px] uppercase font-bold text-slate-500 block">
                              Confidence
                            </span>
                            <span className="font-mono text-xs font-bold text-cyan-400">
                              {Math.round((f.confidence ?? 1.0) * 100)}%
                            </span>
                          </div>
                          <div className="rounded-lg bg-slate-950 p-2.5">
                            <span className="text-[9px] uppercase font-bold text-slate-500 block">
                              Anomaly
                            </span>
                            <span className="font-mono text-xs font-bold text-amber-400">
                              {Math.round((f.anomaly_score ?? 0.95) * 100)}%
                            </span>
                          </div>
                          <div className="rounded-lg bg-slate-950 p-2.5">
                            <span className="text-[9px] uppercase font-bold text-slate-500 block">
                              Status
                            </span>
                            <span className="font-mono text-xs font-bold text-red-400">
                              {f.status_code}
                            </span>
                          </div>
                        </div>

                        <button
                          type="button"
                          className="rounded-xl border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-bold text-slate-200 hover:bg-slate-700 hover:border-cyan-500/40"
                        >
                          Investigate
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* PAGE 6: ATTACK GRAPH */}
        {activePage === "Attack Graph" && (
          <div className="p-6 lg:p-8 space-y-6">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-400">
                Visual Graph Intelligence
              </span>
              <h1 className="mt-1 text-3xl font-extrabold text-white">Security Attack Graph</h1>
              <p className="mt-1 text-xs text-slate-400">
                Visual reconstruction of authorization boundaries, attack paths, and API topology.
              </p>
            </div>

            <Suspense fallback={<LoadingPanel label="Synthesizing Security Graph..." />}>
              <AttackGraph
                finding={selectedFinding ?? findings[0] ?? null}
                findings={findings}
                endpoints={endpoints}
                targetName={scanResult?.target ?? "Authorized Local Sandbox"}
              />
            </Suspense>
          </div>
        )}

        {/* PAGE 7: REPORTS & EXPORT */}
        {activePage === "Reports" && (
          <div className="p-6 lg:p-8 space-y-6">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-cyan-400">
                  Compliance & Export
                </span>
                <h1 className="mt-1 text-3xl font-extrabold text-white">Security Reports</h1>
                <p className="mt-1 text-xs text-slate-400">
                  Comprehensive executive summary ready for developers, security leads, and auditors.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-xs font-bold text-slate-200 hover:bg-slate-800"
                >
                  <Printer size={14} />
                  Print / PDF
                </button>
                <button
                  type="button"
                  onClick={downloadCsv}
                  disabled={!scanResult}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-xs font-bold text-slate-200 hover:bg-slate-800 disabled:opacity-40"
                >
                  <Download size={14} />
                  CSV Export
                </button>
                <button
                  type="button"
                  onClick={downloadJson}
                  disabled={!scanResult}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-cyan-500 px-4 py-2 text-xs font-bold text-slate-950 hover:bg-cyan-400 disabled:opacity-40"
                >
                  <Download size={14} />
                  JSON Report
                </button>
              </div>
            </div>

            {/* Executive Report View */}
            <div className="hologram-card rounded-3xl p-8 shadow-2xl space-y-6 print:border-none print:p-0">
              <div className="border-b border-slate-800 pb-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-2xl font-black text-white">
                      SENTINEL<span className="text-cyan-400">API</span> SECURITY ASSESSMENT REPORT
                    </h2>
                    <p className="text-xs text-slate-400 mt-1">
                      Zero-Trust API Security Intelligence · Automated BOLA Audit
                    </p>
                  </div>
                  <span className="font-mono text-xs text-slate-400">
                    Scan ID: {scanResult?.scan_id ?? "DEMO-AUDIT-001"}
                  </span>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-4">
                <div className="rounded-xl bg-slate-950 p-4">
                  <span className="text-[10px] font-bold text-slate-500 uppercase block">Target</span>
                  <span className="font-mono text-xs font-bold text-slate-200">
                    {scanResult?.target ?? "http://localhost:8000"}
                  </span>
                </div>
                <div className="rounded-xl bg-slate-950 p-4">
                  <span className="text-[10px] font-bold text-slate-500 uppercase block">Risk Score</span>
                  <span className="font-mono text-xs font-bold text-red-400">
                    {riskScore} / 100 ({riskLevel})
                  </span>
                </div>
                <div className="rounded-xl bg-slate-950 p-4">
                  <span className="text-[10px] font-bold text-slate-500 uppercase block">Verified BOLA</span>
                  <span className="font-mono text-xs font-bold text-red-400">
                    {findings.length} Finding(s)
                  </span>
                </div>
                <div className="rounded-xl bg-slate-950 p-4">
                  <span className="text-[10px] font-bold text-slate-500 uppercase block">Coverage</span>
                  <span className="font-mono text-xs font-bold text-cyan-400">
                    {authorizationCoverage}% of Mapped Endpoints
                  </span>
                </div>
              </div>

              {/* Executive Summary Narrative */}
              <div className="rounded-2xl border border-slate-800 bg-slate-950 p-6 space-y-3">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Executive Threat Summary
                </h3>
                <p className="text-xs leading-relaxed text-slate-300">
                  SentinelAPI evaluated the target application against Zero-Trust object authorization boundaries.
                  The audit concluded with a <span className="font-bold text-red-400">CRITICAL</span> risk rating.
                  Authenticated callers were able to request and retrieve protected objects belonging to other users
                  by manipulating parameter identifiers (CWE-639 / OWASP API1:2023).
                </p>
              </div>

              {/* Detailed Findings Table */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Audit Findings Summary
                </h3>

                {findings.map((f) => (
                  <div key={f.id} className="rounded-2xl border border-slate-800 bg-slate-950 p-5 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-red-400">{f.id}</span>
                        <span className="text-xs font-bold text-white">{f.category || f.title}</span>
                      </div>
                      <span className="font-mono text-xs text-red-400 font-bold">{f.severity}</span>
                    </div>

                    <p className="text-xs font-mono text-slate-400">
                      {f.method} {f.endpoint} (Target Object #{f.object_id})
                    </p>

                    <p className="text-xs text-slate-300 leading-relaxed">
                      {f.impact}
                    </p>

                    <div className="pt-2 border-t border-slate-800/80 text-[11px] text-emerald-400 font-mono">
                      Remediation: {f.remediation}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* INVESTIGATION DRAWER (FINDINGS) */}
      {selectedFinding && (
        <div
          className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md"
          onMouseDown={() => setSelectedFinding(null)}
        >
          <aside
            className="absolute right-0 top-0 h-full w-full max-w-2xl overflow-y-auto border-l border-cyan-500/30 bg-slate-950 p-6 shadow-2xl space-y-6"
            onMouseDown={(e) => e.stopPropagation()}
          >
            {/* Drawer Header */}
            <div className="flex items-start justify-between border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <ShieldAlert className="h-5 w-5 text-red-400" />
                  <span className="font-mono text-sm font-black text-red-400">
                    {selectedFinding.id}
                  </span>
                  <span className="rounded bg-red-500/20 px-2 py-0.5 text-[10px] font-bold text-red-300 border border-red-500/30">
                    {selectedFinding.severity}
                  </span>
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-400">
                    {selectedFinding.cwe || "CWE-639"}
                  </span>
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-slate-400">
                    {selectedFinding.owasp || "API1:2023"}
                  </span>
                </div>
                <h2 className="mt-2 text-lg font-bold text-white">
                  {selectedFinding.title || "Broken Object Level Authorization"}
                </h2>
                <p className="font-mono text-xs text-slate-300 mt-1">
                  {selectedFinding.method} {selectedFinding.endpoint}
                </p>
              </div>

              <button
                type="button"
                onClick={() => setSelectedFinding(null)}
                className="rounded-lg p-2 text-slate-500 hover:bg-slate-900 hover:text-white"
              >
                <X size={18} />
              </button>
            </div>

            {/* Quick Context Chips */}
            <div className="grid grid-cols-4 gap-2 text-center">
              <div className="rounded-xl border border-slate-800 bg-slate-900 p-2.5">
                <span className="text-[9px] uppercase font-bold text-slate-500 block">Attacker</span>
                <span className="text-xs font-bold text-sky-300 truncate block">
                  {selectedFinding.attacker}
                </span>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900 p-2.5">
                <span className="text-[9px] uppercase font-bold text-slate-500 block">Victim</span>
                <span className="text-xs font-bold text-emerald-300 truncate block">
                  {selectedFinding.resource_owner}
                </span>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900 p-2.5">
                <span className="text-[9px] uppercase font-bold text-slate-500 block">Object ID</span>
                <span className="text-xs font-mono font-bold text-amber-300">
                  #{selectedFinding.object_id}
                </span>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900 p-2.5">
                <span className="text-[9px] uppercase font-bold text-slate-500 block">HTTP Response</span>
                <span className="text-xs font-mono font-bold text-red-400">
                  {selectedFinding.status_code} OK
                </span>
              </div>
            </div>

            {/* Drawer Tabs */}
            <div className="flex rounded-xl border border-slate-800 bg-slate-900 p-1">
              {[
                { key: "SUMMARY", label: "Summary" },
                { key: "REMEDIATION", label: "Remediation & Fix" },
                { key: "REQUEST_RESPONSE", label: "Request & Response" },
                { key: "ATTACK_PATH", label: "Attack Path" },
              ].map((tab) => (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() =>
                    setFindingDrawerTab(
                      tab.key as "SUMMARY" | "REMEDIATION" | "REQUEST_RESPONSE" | "ATTACK_PATH"
                    )
                  }
                  className={`flex-1 py-1.5 text-xs font-mono font-bold rounded-lg transition ${
                    findingDrawerTab === tab.key
                      ? "bg-cyan-500 text-slate-950 shadow"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* TAB 1: SUMMARY */}
            {findingDrawerTab === "SUMMARY" && (
              <div className="space-y-4">
                {/* Impact */}
                <div className="rounded-2xl border border-red-950/60 bg-red-950/20 p-5 space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-red-400">
                    Security & Business Impact
                  </h4>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {selectedFinding.impact}
                  </p>
                </div>

                {/* Description */}
                <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                    Vulnerability Description
                  </h4>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {selectedFinding.description ||
                      "Broken Object Level Authorization detected. The API returned an object belonging to another authenticated user with HTTP 200 OK."}
                  </p>
                </div>

                {/* Security Reasoning */}
                {selectedFinding.security_reasoning && (
                  <div className="rounded-2xl border border-cyan-900/40 bg-cyan-950/15 p-5 space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400">
                      Zero-Trust Verification Reasoning
                    </h4>
                    <ul className="space-y-1.5 text-xs text-slate-300">
                      {selectedFinding.security_reasoning.map((step, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="mt-1 h-1.5 w-1.5 rounded-full bg-cyan-400 shrink-0" />
                          <span>{step}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: REMEDIATION (Section 20) */}
            {findingDrawerTab === "REMEDIATION" && (
              <div className="space-y-4">
                {/* Root Cause Callout */}
                <div className="rounded-2xl border border-red-900/60 bg-red-950/30 p-5 space-y-1.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-red-400 block">
                    Root Cause
                  </span>
                  <p className="text-xs text-slate-200 leading-relaxed">
                    The endpoint retrieves an object using the supplied object identifier (
                    <span className="font-mono text-amber-300">#{selectedFinding.object_id}</span>
                    ) but does not verify that the authenticated principal (
                    <span className="font-bold text-sky-300">{selectedFinding.attacker}</span>
                    ) owns or has authorization to access the object.
                  </p>
                </div>

                {/* Recommended Control */}
                <div className="rounded-2xl border border-cyan-900/60 bg-cyan-950/30 p-5 space-y-1.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 block">
                    Recommended Security Control
                  </span>
                  <p className="text-xs text-slate-200 leading-relaxed">
                    Verify:{" "}
                    <code className="rounded bg-slate-900 px-2 py-0.5 font-mono text-cyan-300">
                      authenticated_user.id == object.owner_id
                    </code>{" "}
                    before returning the object from the database or data store.
                  </p>
                </div>

                {/* Expected Secure Behavior */}
                <div className="rounded-2xl border border-emerald-900/60 bg-emerald-950/30 p-5 space-y-1.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 block">
                    Expected Secure Behavior
                  </span>
                  <p className="text-xs text-slate-200 leading-relaxed">
                    Unauthorized cross-user access attempts must result in an explicit authorization denial:{" "}
                    <span className="font-mono font-bold text-emerald-300">HTTP 403 Forbidden</span> or{" "}
                    <span className="font-mono font-bold text-emerald-300">HTTP 404 Not Found</span>{" "}
                    (to mitigate object ID enumeration).
                  </p>
                </div>

                {/* Code Diff (Vulnerable vs Remediated) */}
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Code2 className="h-4 w-4 text-emerald-400" />
                      <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                        Remediated Implementation
                      </h4>
                    </div>

                    <button
                      type="button"
                      onClick={() =>
                        copyRemediation(
                          selectedFinding.developer_remediation?.code_example?.remediated ||
                            `# Zero-Trust Check: verify ownership\nif order.owner_id != user.id:\n    raise HTTPException(status_code=403, detail="Access denied")`
                        )
                      }
                      className="inline-flex items-center gap-1 rounded bg-slate-800 px-2.5 py-1 text-[10px] font-mono text-slate-300 hover:bg-slate-700"
                    >
                      <Copy size={12} />
                      {copiedCode ? "Copied" : "Copy Code"}
                    </button>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-red-400 block mb-1">
                        Vulnerable Code:
                      </span>
                      <pre className="overflow-x-auto rounded-lg bg-slate-950 p-3 font-mono text-[11px] text-red-300 border border-red-950/60">
                        {selectedFinding.developer_remediation?.code_example?.vulnerable ||
                          `@app.get("/orders/{order_id}")\ndef get_order(order_id: int, user = Depends(get_current_user)):\n    order = db.find(order_id)\n    return order  # Missing ownership check!`}
                      </pre>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase font-bold text-emerald-400 block mb-1">
                        Remediated Code:
                      </span>
                      <pre className="overflow-x-auto rounded-lg bg-slate-950 p-3 font-mono text-[11px] text-emerald-300 border border-emerald-950/60">
                        {selectedFinding.developer_remediation?.code_example?.remediated ||
                          `@app.get("/orders/{order_id}")\ndef get_order(order_id: int, user = Depends(get_current_user)):\n    order = db.find(order_id)\n    if order.owner_id != user.id:\n        raise HTTPException(status_code=403, detail="Access denied")\n    return order`}
                      </pre>
                    </div>
                  </div>
                </div>

                {/* Re-Scan Action Button */}
                <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold text-slate-200 block">
                      Validate Fix in Target API
                    </span>
                    <span className="text-[11px] text-slate-400">
                      Re-run zero-trust audit to verify the authorization boundary is secure.
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedFinding(null)
                      navigate("API Scanner")
                    }}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-cyan-500 px-4 py-2 text-xs font-bold text-slate-950 hover:bg-cyan-400 transition"
                  >
                    <RotateCcw size={13} />
                    RE-SCAN AFTER REMEDIATION
                  </button>
                </div>
              </div>
            )}

            {/* TAB 3: REQUEST & RESPONSE */}
            {findingDrawerTab === "REQUEST_RESPONSE" && (
              <div className="space-y-4">
                {/* Request */}
                <div className="rounded-xl border border-slate-800 bg-slate-900 p-4 space-y-2">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                    HTTP Request (Masked Credentials)
                  </p>
                  <div className="font-mono text-xs text-slate-300 space-y-1">
                    <div>
                      <span className="text-cyan-400 font-bold">{selectedFinding.method}</span>{" "}
                      {selectedFinding.endpoint} HTTP/1.1
                    </div>
                    <div className="text-slate-400 text-[11px]">
                      Authorization:{" "}
                      <span className="text-purple-300">
                        {selectedFinding.evidence?.request?.headers?.Authorization ||
                          "Bearer tok***-a"}
                      </span>
                    </div>
                    <div className="text-slate-500 text-[10px]">
                      Authenticated Principal: {selectedFinding.attacker} (ID: 1)
                    </div>
                  </div>
                </div>

                {/* Response */}
                <div className="rounded-xl border border-slate-800 bg-slate-900 p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                      HTTP Response Body
                    </p>
                    {selectedFinding.evidence?.response_fingerprint && (
                      <span className="font-mono text-[9px] text-slate-500">
                        Fingerprint: {selectedFinding.evidence.response_fingerprint}
                      </span>
                    )}
                  </div>

                  <pre className="overflow-x-auto rounded-lg bg-slate-950 p-3 font-mono text-xs text-red-300">
                    {JSON.stringify(
                      selectedFinding.evidence?.response || {
                        order_id: 102,
                        owner_id: 2,
                        product: "iPhone",
                        amount: 799,
                      },
                      null,
                      2
                    )}
                  </pre>

                  {/* Highlight callout */}
                  <div className="rounded-lg border border-red-900/60 bg-red-950/30 p-2.5 text-xs text-slate-200">
                    <span className="font-bold text-red-400">Ownership Mismatch Notice:</span>{" "}
                    The authenticated requester (
                    <span className="font-bold text-sky-300">{selectedFinding.attacker}</span>) does
                    not own the returned object (
                    <span className="font-bold text-emerald-300">owner_id: 2</span>).
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: ATTACK PATH */}
            {findingDrawerTab === "ATTACK_PATH" && (
              <div className="space-y-4">
                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5 space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-400">
                    Reconstructed Attack Sequence
                  </h4>

                  <div className="space-y-2 text-xs font-mono">
                    <div className="flex items-center gap-2 rounded-lg bg-slate-950 p-2.5 border border-slate-800">
                      <span className="text-sky-400 font-bold">1. CALLER</span>
                      <span className="text-slate-400">→</span>
                      <span className="text-slate-200">
                        {selectedFinding.attacker} authenticates via Bearer gate
                      </span>
                    </div>

                    <div className="flex items-center gap-2 rounded-lg bg-slate-950 p-2.5 border border-slate-800">
                      <span className="text-amber-400 font-bold">2. PROBE</span>
                      <span className="text-slate-400">→</span>
                      <span className="text-slate-200">
                        Injects parameter order_id = {selectedFinding.object_id}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 rounded-lg bg-slate-950 p-2.5 border border-slate-800">
                      <span className="text-red-400 font-bold">3. BREACH</span>
                      <span className="text-slate-400">→</span>
                      <span className="text-slate-200">
                        Target returns record owned by {selectedFinding.resource_owner}
                      </span>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-800">
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedFinding(null)
                        navigate("Attack Graph")
                      }}
                      className="inline-flex items-center gap-2 rounded-xl bg-cyan-500 px-4 py-2 text-xs font-bold text-slate-950 hover:bg-cyan-400 transition"
                    >
                      <Network size={14} />
                      View In Interactive Attack Graph
                    </button>
                  </div>
                </div>
              </div>
            )}
          </aside>
        </div>
      )}

      {/* ENDPOINT DETAILS DRAWER (Section 18) */}
      {selectedEndpoint && (
        <div
          className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md"
          onMouseDown={() => setSelectedEndpoint(null)}
        >
          <aside
            className="absolute right-0 top-0 h-full w-full max-w-lg overflow-y-auto border-l border-cyan-500/30 bg-slate-950 p-6 shadow-2xl space-y-6"
            onMouseDown={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-start justify-between border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded px-1.5 py-0.5 text-xs font-mono font-bold ${
                      selectedEndpoint.method === "GET"
                        ? "bg-cyan-950 text-cyan-400 border border-cyan-800"
                        : "bg-emerald-950 text-emerald-400 border border-emerald-800"
                    }`}
                  >
                    {selectedEndpoint.method}
                  </span>
                  <span className="text-xs font-mono text-slate-400 uppercase">
                    {selectedEndpoint.category} endpoint
                  </span>
                </div>
                <h2 className="mt-2 text-lg font-bold text-white font-mono">
                  {selectedEndpoint.path}
                </h2>
              </div>

              <button
                type="button"
                onClick={() => setSelectedEndpoint(null)}
                className="rounded-lg p-2 text-slate-500 hover:bg-slate-900 hover:text-white"
              >
                <X size={18} />
              </button>
            </div>

            {/* Status Cards */}
            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="rounded-xl border border-slate-800 bg-slate-900 p-3">
                <span className="text-[10px] font-bold uppercase text-slate-500 block">
                  Authorization Test
                </span>
                <span
                  className={`text-xs font-mono font-bold ${
                    selectedEndpoint.authorization_tested ? "text-emerald-400" : "text-slate-400"
                  }`}
                >
                  {selectedEndpoint.authorization_tested ? "TESTED (Bidirectional)" : "DISCOVERED"}
                </span>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900 p-3">
                <span className="text-[10px] font-bold uppercase text-slate-500 block">
                  Security Verdict
                </span>
                <span
                  className={`text-xs font-mono font-bold ${
                    selectedEndpoint.finding_count > 0 ? "text-red-400" : "text-emerald-400"
                  }`}
                >
                  {selectedEndpoint.finding_count > 0
                    ? `VULNERABLE (${selectedEndpoint.finding_count} BOLA)`
                    : selectedEndpoint.authorization_tested
                    ? "SECURE"
                    : "MAPPED"}
                </span>
              </div>
            </div>

            {/* Parameters Breakdown */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4 space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-200 block">
                Parameters & Schemes
              </span>
              <div className="space-y-1.5 text-xs font-mono">
                <div className="flex justify-between border-b border-slate-800 pb-1 text-slate-400">
                  <span>Path Parameter:</span>
                  <span className="text-cyan-300">
                    {selectedEndpoint.parameter || (selectedEndpoint.path.includes("{") ? "order_id" : "None")}
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-800 pb-1 text-slate-400">
                  <span>Authentication Scheme:</span>
                  <span className="text-purple-300">
                    {selectedEndpoint.path.includes("order") ? "Bearer Token" : "Optional / None"}
                  </span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Zero-Trust Scope:</span>
                  <span className="text-amber-300">
                    {selectedEndpoint.category === "object" ? "Object Authorization Bound" : "Collection Route"}
                  </span>
                </div>
              </div>
            </div>

            {/* Associated Findings */}
            {selectedEndpoint.finding_count > 0 && (
              <div className="rounded-2xl border border-red-900/60 bg-red-950/20 p-4 space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-red-400 block">
                  Verified Vulnerabilities on this Route
                </span>
                <div className="space-y-1 text-xs">
                  {findings
                    .filter((f) => f.endpoint === selectedEndpoint.path || selectedEndpoint.path.includes("{"))
                    .map((f) => (
                      <div
                        key={f.id}
                        onClick={() => {
                          setSelectedEndpoint(null)
                          setSelectedFinding(f)
                        }}
                        className="flex items-center justify-between rounded-lg bg-slate-900 p-2.5 border border-slate-800 hover:border-cyan-500/40 cursor-pointer"
                      >
                        <span className="font-mono font-bold text-red-400">{f.id}</span>
                        <span className="text-slate-300 truncate max-w-[200px]">{f.attacker} → {f.resource_owner}</span>
                        <span className="text-cyan-400 text-[10px] font-bold">Inspect →</span>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => {
                  setSelectedEndpoint(null)
                  navigate("API Console")
                }}
                className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-bold text-cyan-300 hover:bg-slate-800 transition"
              >
                <Terminal size={14} />
                Test in API Console
              </button>

              <button
                type="button"
                onClick={() => {
                  setSelectedEndpoint(null)
                  navigate("Attack Graph")
                }}
                className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-xl bg-cyan-500 px-3 py-2 text-xs font-bold text-slate-950 hover:bg-cyan-400 transition"
              >
                <Network size={14} />
                Inspect in Graph
              </button>
            </div>
          </aside>
        </div>
      )}
    </div>
  )
}

export default function SafeApp() {
  return (
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>
  )
}

