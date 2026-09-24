import { useState } from "react"

import {
  ShieldAlert,
  Server,
  Bug,
  Activity,
  Network,
  FileText,
  ChevronRight,
  X,
  Terminal,
  LockKeyhole,
  Gauge,
  BrainCircuit,
  Clock3,
  Users,
} from "lucide-react"

import AttackGraph from "./AttackGraph"
import ApiScanner from "./ApiScanner"

type Finding = {
  id: string
  type: string
  severity: string
  endpoint: string
  method: string
  attacker: string
  resource_owner: string
  object_id: number
  status_code: number
  impact: string
  remediation: string
  description: string
  evidence?: {
    request?: {
      method: string
      url: string
      user: string
    }
    response?: Record<string, unknown>
  }
}

type ScanResult = {
  scan_id: string
  status: string
  target: string

  scan_metadata?: {
    scanner: string
    engine: string
    started_at: string
    authentication_profiles: number
    authorization_testing: boolean
  }

  risk?: {
    score: number
    level: string
    reasoning: {
      status: string
      reasoning: string[]
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
}

type Page =
  | "Dashboard"
  | "API Scanner"
  | "Attack Graph"

function App() {
  const [scanResult, setScanResult] =
    useState<ScanResult | null>(null)

  const [selectedFinding, setSelectedFinding] =
    useState<Finding | null>(null)

  const [activePage, setActivePage] =
    useState<Page>("Dashboard")

  const [dashboardScanning, setDashboardScanning] =
    useState(false)

  const [dashboardError, setDashboardError] =
    useState("")

  const handleScanComplete = (result: ScanResult) => {
    setScanResult(result)
  }

  const runDashboardScan = async () => {
    if (dashboardScanning) {
      return
    }

    try {
      setDashboardScanning(true)
      setDashboardError("")

      const response = await fetch(
        "http://127.0.0.1:8001/scan",
        {
          method: "POST",
        }
      )

      if (!response.ok) {
        throw new Error(
          `Scan failed with status ${response.status}`
        )
      }

      const data: ScanResult =
        await response.json()

      setScanResult(data)
    } catch (error) {
      console.error(
        "Dashboard scan failed:",
        error
      )

      setDashboardError(
        "Unable to connect to SentinelAPI scanner. Make sure the backend is running on port 8001."
      )
    } finally {
      setDashboardScanning(false)
    }
  }

  const goToDashboard = () => {
    setActivePage("Dashboard")

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    })
  }

  const goToScanner = () => {
    setActivePage("API Scanner")

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    })
  }

  const goToAttackGraph = () => {
    setActivePage("Attack Graph")

    setTimeout(() => {
      document
        .getElementById("attack-graph")
        ?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        })
    }, 50)
  }

  const vulnerabilities =
    scanResult?.summary.vulnerabilities ?? 0

  const critical =
    scanResult?.summary.critical ?? 0

  const high =
    scanResult?.summary.high ?? 0

  const medium =
    scanResult?.summary.medium ?? 0

  const low =
    scanResult?.summary.low ?? 0

  const riskScore =
    scanResult?.risk?.score ?? 0

  const riskLevel =
    scanResult?.risk?.level ?? "READY"

  const riskReasoning =
    scanResult?.risk?.reasoning

  const findings =
    scanResult?.findings ?? []

  const endpoints = new Set(
    findings.map(
      (finding) => finding.endpoint
    )
  ).size

  const riskBarWidth =
    Math.min(riskScore, 100)

  const riskColor =
    riskScore >= 80
      ? "text-red-400"
      : riskScore >= 50
        ? "text-orange-400"
        : riskScore >= 25
          ? "text-yellow-400"
          : "text-emerald-400"

  const riskBorder =
    riskScore >= 80
      ? "border-red-900/50"
      : riskScore >= 50
        ? "border-orange-900/50"
        : riskScore >= 25
          ? "border-yellow-900/50"
          : "border-emerald-900/50"

  const riskBackground =
    riskScore >= 80
      ? "bg-red-950/20"
      : riskScore >= 50
        ? "bg-orange-950/20"
        : riskScore >= 25
          ? "bg-yellow-950/20"
          : "bg-emerald-950/20"

  return (
    <div className="min-h-screen bg-slate-950 text-white">

      <div className="flex min-h-screen">

        <aside className="fixed left-0 top-0 z-30 h-screen w-64 border-r border-slate-800 bg-slate-950 p-5">

          <div className="mb-10">

            <div className="flex items-center gap-3">

              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10">

                <ShieldAlert
                  size={20}
                  className="text-cyan-400"
                />

              </div>

              <div>

                <h1 className="text-xl font-bold tracking-tight">
                  Sentinel<span className="text-cyan-400">API</span>
                </h1>

                <p className="text-xs text-slate-500">
                  Zero-Trust Security
                </p>

              </div>

            </div>

          </div>

          <nav className="space-y-2">

            <button
              type="button"
              onClick={goToDashboard}
              className={`flex w-full items-center gap-3 rounded-lg px-4 py-3 text-left text-sm font-medium transition ${
                activePage === "Dashboard"
                  ? "bg-cyan-500/10 text-cyan-400"
                  : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
              }`}
            >
              <Activity size={17} />
              Dashboard
            </button>

            <button
              type="button"
              onClick={goToScanner}
              className={`flex w-full items-center gap-3 rounded-lg px-4 py-3 text-left text-sm font-medium transition ${
                activePage === "API Scanner"
                  ? "bg-cyan-500/10 text-cyan-400"
                  : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
              }`}
            >
              <Bug size={17} />
              API Scanner
            </button>

            <button
              type="button"
              onClick={goToDashboard}
              className="flex w-full items-center gap-3 rounded-lg px-4 py-3 text-left text-sm text-slate-400 transition hover:bg-slate-900 hover:text-slate-200"
            >
              <Server size={17} />
              Endpoints
            </button>

            <button
              type="button"
              onClick={goToDashboard}
              className="flex w-full items-center gap-3 rounded-lg px-4 py-3 text-left text-sm text-slate-400 transition hover:bg-slate-900 hover:text-slate-200"
            >
              <ShieldAlert size={17} />
              Findings
            </button>

            <button
              type="button"
              onClick={goToAttackGraph}
              className={`flex w-full items-center gap-3 rounded-lg px-4 py-3 text-left text-sm font-medium transition ${
                activePage === "Attack Graph"
                  ? "bg-cyan-500/10 text-cyan-400"
                  : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
              }`}
            >
              <Network size={17} />
              Attack Graph
            </button>

            <button
              type="button"
              onClick={goToDashboard}
              className="flex w-full items-center gap-3 rounded-lg px-4 py-3 text-left text-sm text-slate-400 transition hover:bg-slate-900 hover:text-slate-200"
            >
              <FileText size={17} />
              Reports
            </button>

          </nav>

          <div className="mt-10 rounded-xl border border-slate-800 bg-slate-900 p-4">

            <div className="flex items-center gap-2">

              <div className="h-2 w-2 rounded-full bg-emerald-400" />

              <span className="text-xs font-medium text-emerald-400">
                Scanner Online
              </span>

            </div>

            <p className="mt-2 text-xs text-slate-500">
              SentinelAPI engine connected on port 8001.
            </p>

          </div>

        </aside>

        <main className="ml-64 flex-1">

          {activePage === "API Scanner" ? (

            <ApiScanner
              onScanComplete={handleScanComplete}
            />

          ) : (

            <div className="p-8">

              <div className="mb-8 flex items-start justify-between">

                <div>

                  <p className="text-sm font-medium tracking-wider text-cyan-400">
                    SECURITY OVERVIEW
                  </p>

                  <h2 className="mt-2 text-3xl font-bold">
                    API Security Dashboard
                  </h2>

                  <p className="mt-2 text-slate-400">
                    Continuous zero-trust analysis of your API attack surface.
                  </p>

                </div>

                <div className="rounded-lg border border-slate-800 bg-slate-900 px-4 py-3">

                  <p className="text-xs text-slate-500">
                    TARGET
                  </p>

                  <p className="mt-1 text-sm font-medium text-slate-200">
                    {scanResult?.target ?? "Local Sandbox API"}
                  </p>

                </div>

              </div>

              {dashboardError && (

                <div className="mb-6 rounded-xl border border-red-900/50 bg-red-950/30 p-4">

                  <p className="text-sm font-medium text-red-400">
                    Scanner Error
                  </p>

                  <p className="mt-1 text-sm text-red-300/80">
                    {dashboardError}
                  </p>

                </div>

              )}

              <div className="grid grid-cols-4 gap-4">

                <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">

                  <div className="flex items-center justify-between">

                    <p className="text-sm text-slate-400">
                      Vulnerabilities
                    </p>

                    <Bug
                      size={17}
                      className="text-slate-500"
                    />

                  </div>

                  <p className="mt-3 text-3xl font-bold">
                    {vulnerabilities}
                  </p>

                </div>

                <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-5">

                  <div className="flex items-center justify-between">

                    <p className="text-sm text-red-400">
                      Critical
                    </p>

                    <ShieldAlert
                      size={17}
                      className="text-red-400"
                    />

                  </div>

                  <p className="mt-3 text-3xl font-bold text-red-400">
                    {critical}
                  </p>

                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">

                  <div className="flex items-center justify-between">

                    <p className="text-sm text-slate-400">
                      Endpoints Tested
                    </p>

                    <Server
                      size={17}
                      className="text-slate-500"
                    />

                  </div>

                  <p className="mt-3 text-3xl font-bold">
                    {endpoints}
                  </p>

                </div>

                <div className="rounded-xl border border-emerald-900/50 bg-emerald-950/20 p-5">

                  <div className="flex items-center justify-between">

                    <p className="text-sm text-emerald-400">
                      Scan Status
                    </p>

                    <Activity
                      size={17}
                      className="text-emerald-400"
                    />

                  </div>

                  <p className="mt-3 text-lg font-semibold text-emerald-400">
                    {dashboardScanning
                      ? "Scanning..."
                      : scanResult?.status ?? "Ready"}
                  </p>

                </div>

              </div>

              <div className="mt-8 grid grid-cols-3 gap-6">

                <div className="col-span-2 rounded-xl border border-slate-800 bg-slate-900 p-6">

                  <div className="flex items-center justify-between">

                    <div>

                      <h3 className="text-lg font-semibold">
                        Latest Security Findings
                      </h3>

                      <p className="mt-1 text-sm text-slate-500">
                        Verified vulnerabilities detected during the latest scan.
                      </p>

                    </div>

                    <button
                      type="button"
                      onClick={runDashboardScan}
                      disabled={dashboardScanning}
                      className="rounded-lg bg-cyan-500 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {dashboardScanning
                        ? "Scanning..."
                        : "Run Scan"}
                    </button>

                  </div>

                  <div className="mt-6 space-y-3">

                    {dashboardScanning && (

                      <div className="rounded-lg border border-cyan-900/40 bg-cyan-950/20 p-5">

                        <div className="flex items-center gap-3">

                          <div className="h-4 w-4 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />

                          <div>

                            <p className="font-medium text-cyan-400">
                              Scanning API...
                            </p>

                            <p className="mt-1 text-xs text-slate-500">
                              Discovering endpoints and testing authorization boundaries.
                            </p>

                          </div>

                        </div>

                      </div>

                    )}

                    {!dashboardScanning &&
                      findings.length === 0 && (

                        <div className="rounded-lg border border-dashed border-slate-700 p-8 text-center">

                          <p className="font-medium text-slate-300">
                            No scan results yet
                          </p>

                          <p className="mt-2 text-sm text-slate-500">
                            Run a security scan to discover API vulnerabilities.
                          </p>

                        </div>

                      )}

                    {!dashboardScanning &&
                      findings.map((finding) => (

                        <button
                          type="button"
                          key={finding.id}
                          onClick={() =>
                            setSelectedFinding(finding)
                          }
                          className="group w-full rounded-lg border border-red-900/40 bg-red-950/20 p-4 text-left transition hover:border-red-700 hover:bg-red-950/30"
                        >

                          <div className="flex items-center justify-between">

                            <div className="flex items-center gap-4">

                              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-500/10">

                                <ShieldAlert
                                  size={20}
                                  className="text-red-400"
                                />

                              </div>

                              <div>

                                <p className="font-semibold text-red-400">
                                  {finding.type}
                                </p>

                                <p className="mt-1 text-sm text-slate-300">
                                  {finding.method}{" "}
                                  {finding.endpoint}
                                </p>

                                <p className="mt-1 text-xs text-slate-500">
                                  {finding.attacker} →{" "}
                                  {finding.resource_owner}
                                </p>

                              </div>

                            </div>

                            <div className="flex items-center gap-3">

                              <span className="rounded-full bg-red-500/10 px-3 py-1 text-xs font-semibold text-red-400">
                                {finding.severity}
                              </span>

                              <ChevronRight
                                size={18}
                                className="text-slate-600 transition group-hover:translate-x-1 group-hover:text-slate-300"
                              />

                            </div>

                          </div>

                        </button>

                      ))}

                  </div>

                </div>

                <div
                  className={`rounded-xl border ${riskBorder} ${riskBackground} p-6`}
                >

                  <div className="flex items-center justify-between">

                    <div>

                      <h3 className="text-lg font-semibold">
                        Security Posture
                      </h3>

                      <p className="mt-1 text-xs text-slate-500">
                        Zero-trust risk assessment
                      </p>

                    </div>

                    <Gauge
                      size={20}
                      className={riskColor}
                    />

                  </div>

                  <div className="mt-7 flex items-center justify-center">

                    <div
                      className={`flex h-40 w-40 items-center justify-center rounded-full border-8 ${
                        riskScore >= 80
                          ? "border-red-500/70"
                          : riskScore >= 50
                            ? "border-orange-500/70"
                            : riskScore >= 25
                              ? "border-yellow-500/70"
                              : "border-emerald-500/70"
                      }`}
                    >

                      <div className="text-center">

                        <p
                          className={`text-4xl font-bold ${riskColor}`}
                        >
                          {riskScore}
                        </p>

                        <p className="text-xs text-slate-500">
                          RISK / 100
                        </p>

                      </div>

                    </div>

                  </div>

                  <div className="mt-5">

                    <div className="flex items-center justify-between">

                      <span className="text-xs text-slate-500">
                        Risk Level
                      </span>

                      <span
                        className={`text-xs font-bold ${riskColor}`}
                      >
                        {riskLevel}
                      </span>

                    </div>

                    <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-800">

                      <div
                        className={`h-full rounded-full transition-all duration-700 ${
                          riskScore >= 80
                            ? "bg-red-500"
                            : riskScore >= 50
                              ? "bg-orange-500"
                              : riskScore >= 25
                                ? "bg-yellow-500"
                                : "bg-emerald-500"
                        }`}
                        style={{
                          width: `${riskBarWidth}%`,
                        }}
                      />

                    </div>

                  </div>

                  <p className="mt-5 text-center text-sm text-slate-400">

                    {scanResult
                      ? riskReasoning?.status ??
                        "Risk assessment completed."
                      : "Run a scan to evaluate security posture."}

                  </p>

                  <div className="mt-5 grid grid-cols-3 gap-2">

                    <div className="rounded-lg bg-slate-900/70 p-3 text-center">

                      <p className="text-xs text-slate-500">
                        HIGH
                      </p>

                      <p className="mt-1 font-semibold">
                        {high}
                      </p>

                    </div>

                    <div className="rounded-lg bg-slate-900/70 p-3 text-center">

                      <p className="text-xs text-slate-500">
                        MEDIUM
                      </p>

                      <p className="mt-1 font-semibold">
                        {medium}
                      </p>

                    </div>

                    <div className="rounded-lg bg-slate-900/70 p-3 text-center">

                      <p className="text-xs text-slate-500">
                        LOW
                      </p>

                      <p className="mt-1 font-semibold">
                        {low}
                      </p>

                    </div>

                  </div>

                </div>

              </div>

              {scanResult && (

                <div className="mt-6 grid grid-cols-3 gap-4">

                  <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">

                    <div className="flex items-center gap-3">

                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10">

                        <BrainCircuit
                          size={18}
                          className="text-cyan-400"
                        />

                      </div>

                      <div>

                        <p className="text-xs text-slate-500">
                          SECURITY ENGINE
                        </p>

                        <p className="mt-1 text-sm font-semibold text-slate-200">
                          {scanResult.scan_metadata?.engine ??
                            "BOLA Authorization Analyzer"}
                        </p>

                      </div>

                    </div>

                  </div>

                  <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">

                    <div className="flex items-center gap-3">

                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10">

                        <Users
                          size={18}
                          className="text-cyan-400"
                        />

                      </div>

                      <div>

                        <p className="text-xs text-slate-500">
                          AUTH PROFILES
                        </p>

                        <p className="mt-1 text-sm font-semibold text-slate-200">
                          {scanResult.scan_metadata?.authentication_profiles ?? 0}
                          {" "}identities tested
                        </p>

                      </div>

                    </div>

                  </div>

                  <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">

                    <div className="flex items-center gap-3">

                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-500/10">

                        <Clock3
                          size={18}
                          className="text-cyan-400"
                        />

                      </div>

                      <div>

                        <p className="text-xs text-slate-500">
                          SCAN ID
                        </p>

                        <p className="mt-1 font-mono text-sm font-semibold text-slate-200">
                          {scanResult.scan_id}
                        </p>

                      </div>

                    </div>

                  </div>

                </div>

              )}

              {scanResult?.risk?.reasoning && (

                <div className="mt-6 rounded-xl border border-cyan-900/40 bg-slate-900 p-6">

                  <div className="flex items-start gap-4">

                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10">

                      <BrainCircuit
                        size={20}
                        className="text-cyan-400"
                      />

                    </div>

                    <div className="flex-1">

                      <div className="flex items-center justify-between">

                        <div>

                          <h3 className="text-lg font-semibold">
                            Security Reasoning
                          </h3>

                          <p className="mt-1 text-sm text-slate-500">
                            Evidence-based explanation generated by the SentinelAPI risk engine.
                          </p>

                        </div>

                        <span className="rounded-full border border-cyan-900/50 bg-cyan-950/30 px-3 py-1 text-xs font-medium text-cyan-400">
                          EXPLAINABLE
                        </span>

                      </div>

                      <div className="mt-5 space-y-3">

                        {riskReasoning.reasoning.map(
                          (reason, index) => (

                            <div
                              key={index}
                              className="flex gap-3 rounded-lg border border-slate-800 bg-slate-950 p-4"
                            >

                              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-cyan-500/10 text-xs font-bold text-cyan-400">
                                {index + 1}
                              </div>

                              <p className="text-sm leading-6 text-slate-300">
                                {reason}
                              </p>

                            </div>

                          )
                        )}

                      </div>

                    </div>

                  </div>

                </div>

              )}

              <div
                id="attack-graph"
                className="mt-8 scroll-mt-8 rounded-xl border border-slate-800 bg-slate-900 p-6"
              >

                <div className="mb-5 flex items-center justify-between">

                  <div>

                    <div className="flex items-center gap-2">

                      <Network
                        size={18}
                        className="text-cyan-400"
                      />

                      <h3 className="text-lg font-semibold">
                        Attack Graph
                      </h3>

                    </div>

                    <p className="mt-1 text-sm text-slate-500">
                      Visual representation of the detected authorization attack path.
                    </p>

                  </div>

                  <div className="rounded-full border border-red-900/40 bg-red-950/20 px-3 py-1">

                    <span className="text-xs font-medium text-red-400">
                      BOLA DETECTED
                    </span>

                  </div>

                </div>

                <AttackGraph
                  finding={selectedFinding}
                />

              </div>

            </div>

          )}

        </main>

      </div>

      {selectedFinding && (

        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm">

          <div className="h-full w-[520px] overflow-y-auto border-l border-slate-800 bg-slate-950 shadow-2xl">

            <div className="sticky top-0 z-10 border-b border-slate-800 bg-slate-950/95 p-6 backdrop-blur">

              <div className="flex items-start justify-between">

                <div>

                  <div className="flex items-center gap-3">

                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-500/10">

                      <ShieldAlert
                        size={21}
                        className="text-red-400"
                      />

                    </div>

                    <div>

                      <p className="text-xs font-medium tracking-wider text-red-400">
                        {selectedFinding.id}
                      </p>

                      <h3 className="text-xl font-bold">
                        {selectedFinding.type}
                      </h3>

                    </div>

                  </div>

                </div>

                <button
                  type="button"
                  onClick={() =>
                    setSelectedFinding(null)
                  }
                  className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-800 hover:text-white"
                >
                  <X size={20} />
                </button>

              </div>

              <div className="mt-5 flex items-center justify-between">

                <span className="rounded-full bg-red-500/10 px-3 py-1 text-xs font-semibold text-red-400">
                  {selectedFinding.severity}
                </span>

                <span className="text-xs text-slate-500">
                  HTTP {selectedFinding.status_code}
                </span>

              </div>

            </div>

            <div className="space-y-6 p-6">

              <section>

                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Vulnerable Endpoint
                </p>

                <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">

                  <div className="flex items-center gap-3">

                    <span className="rounded bg-cyan-500/10 px-2 py-1 text-xs font-bold text-cyan-400">
                      {selectedFinding.method}
                    </span>

                    <code className="text-sm text-slate-200">
                      {selectedFinding.endpoint}
                    </code>

                  </div>

                </div>

              </section>

              <section>

                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Attack Path
                </p>

                <div className="grid grid-cols-3 items-center gap-2">

                  <div className="rounded-lg border border-slate-800 bg-slate-900 p-3 text-center">

                    <p className="text-xs text-slate-500">
                      ATTACKER
                    </p>

                    <p className="mt-1 text-sm font-semibold text-red-400">
                      {selectedFinding.attacker}
                    </p>

                  </div>

                  <div className="text-center text-slate-600">
                    →
                  </div>

                  <div className="rounded-lg border border-slate-800 bg-slate-900 p-3 text-center">

                    <p className="text-xs text-slate-500">
                      RESOURCE OWNER
                    </p>

                    <p className="mt-1 text-sm font-semibold text-amber-400">
                      {selectedFinding.resource_owner}
                    </p>

                  </div>

                </div>

              </section>

              <section>

                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Object
                </p>

                <div className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-900 p-4">

                  <LockKeyhole
                    size={18}
                    className="text-cyan-400"
                  />

                  <div>

                    <p className="text-xs text-slate-500">
                      Object ID
                    </p>

                    <p className="font-mono text-sm text-slate-200">
                      {selectedFinding.object_id}
                    </p>

                  </div>

                </div>

              </section>

              <section>

                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Description
                </p>

                <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">

                  <p className="text-sm leading-6 text-slate-300">
                    {selectedFinding.description}
                  </p>

                </div>

              </section>

              <section>

                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Evidence
                </p>

                <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">

                  <div className="mb-3 flex items-center gap-2">

                    <Terminal
                      size={16}
                      className="text-cyan-400"
                    />

                    <span className="text-sm font-medium">
                      Request
                    </span>

                  </div>

                  <pre className="overflow-x-auto rounded-lg bg-slate-950 p-4 text-xs leading-6 text-slate-300">
{JSON.stringify(
  selectedFinding.evidence?.request ?? {},
  null,
  2
)}
                  </pre>

                  <div className="mb-3 mt-5 flex items-center gap-2">

                    <Activity
                      size={16}
                      className="text-red-400"
                    />

                    <span className="text-sm font-medium">
                      Response
                    </span>

                  </div>

                  <pre className="overflow-x-auto rounded-lg bg-slate-950 p-4 text-xs leading-6 text-slate-300">
{JSON.stringify(
  selectedFinding.evidence?.response ?? {},
  null,
  2
)}
                  </pre>

                </div>

              </section>

              <section>

                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Impact
                </p>

                <div className="rounded-lg border border-red-900/40 bg-red-950/20 p-4">

                  <p className="text-sm leading-6 text-red-200">
                    {selectedFinding.impact}
                  </p>

                </div>

              </section>

              <section>

                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  Remediation
                </p>

                <div className="rounded-lg border border-emerald-900/40 bg-emerald-950/20 p-4">

                  <p className="text-sm leading-6 text-emerald-200">
                    {selectedFinding.remediation}
                  </p>

                </div>

              </section>

            </div>

          </div>

        </div>

      )}

    </div>
  )
}

export default App