import { useState } from "react"
import {
  ShieldCheck,
  Target,
  KeyRound,
  Play,
  CheckCircle2,
  Circle,
  Loader2,
  Radar,
  AlertTriangle,
} from "lucide-react"

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
}

type ScanResult = {
  scan_id: string
  status: string
  target: string
  summary: {
    vulnerabilities: number
    critical: number
    high: number
    medium: number
    low: number
  }
  findings: Finding[]
}

type ApiScannerProps = {
  onScanComplete?: (result: ScanResult) => void
}

export default function ApiScanner({
  onScanComplete,
}: ApiScannerProps) {
  const [scanning, setScanning] = useState(false)

  const [progress, setProgress] = useState(
    "Ready to start security analysis."
  )

  const [completed, setCompleted] = useState(false)

  const [scanResult, setScanResult] =
    useState<ScanResult | null>(null)

  const [error, setError] = useState("")

  const runScan = async () => {
    if (scanning) {
      return
    }

    try {
      setScanning(true)
      setCompleted(false)
      setError("")
      setScanResult(null)

      setProgress(
        "Connecting to SentinelAPI scanning engine..."
      )

      const response = await fetch(
        "http://127.0.0.1:8001/scan",
        {
          method: "POST",
        }
      )

      if (!response.ok) {
        throw new Error(
          `Scanner request failed with status ${response.status}`
        )
      }

      setProgress(
        "Analyzing authentication boundaries..."
      )

      const data: ScanResult =
        await response.json()

      setScanResult(data)

      setProgress(
        `Scan completed. ${data.summary.vulnerabilities} vulnerability findings detected.`
      )

      setCompleted(true)

      onScanComplete?.(data)

    } catch (error) {
      console.error("Scan failed:", error)

      setError(
        "Scan failed. Make sure the SentinelAPI backend is running on port 8001."
      )

      setProgress(
        "Unable to complete security analysis."
      )

      setCompleted(false)

    } finally {
      setScanning(false)
    }
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

  return (
    <div className="min-h-full bg-slate-950 p-8 text-white">

      <div className="mx-auto max-w-6xl">

        <div className="mb-8">

          <div className="flex items-center gap-3">

            <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-cyan-500/30 bg-cyan-500/10">

              <Radar className="h-5 w-5 text-cyan-400" />

            </div>

            <div>

              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-400">
                SentinelAPI Scanner
              </p>

              <h1 className="mt-1 text-3xl font-bold">
                API Security Scanner
              </h1>

            </div>

          </div>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
            Perform zero-trust security analysis against the configured
            API sandbox and identify authorization vulnerabilities.
          </p>

        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">

          <div className="flex items-center gap-3">

            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-800">

              <Target className="h-5 w-5 text-cyan-400" />

            </div>

            <div>

              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Scan Target
              </p>

              <p className="mt-1 font-medium text-slate-200">
                Local Sandbox API
              </p>

            </div>

            <div className="ml-auto flex items-center gap-2 rounded-full border border-emerald-900/50 bg-emerald-950/30 px-3 py-1.5">

              <span className="h-2 w-2 rounded-full bg-emerald-400" />

              <span className="text-xs font-medium text-emerald-400">
                Connected
              </span>

            </div>

          </div>

          <div className="mt-5 rounded-lg border border-slate-800 bg-slate-950 px-4 py-3">

            <p className="font-mono text-sm text-slate-300">
              http://127.0.0.1:8000
            </p>

          </div>

        </div>

        <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900 p-6">

          <div className="flex items-center gap-3">

            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-800">

              <KeyRound className="h-5 w-5 text-violet-400" />

            </div>

            <div>

              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Authentication Profiles
              </p>

              <p className="mt-1 text-sm text-slate-400">
                Identities used for authorization boundary testing.
              </p>

            </div>

          </div>

          <div className="mt-5 grid grid-cols-2 gap-4">

            <div className="rounded-lg border border-slate-700 bg-slate-950 p-4">

              <div className="flex items-center justify-between">

                <div>

                  <p className="font-semibold text-slate-200">
                    User A
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    token-user-a
                  </p>

                </div>

                <CheckCircle2 className="h-5 w-5 text-emerald-400" />

              </div>

            </div>

            <div className="rounded-lg border border-slate-700 bg-slate-950 p-4">

              <div className="flex items-center justify-between">

                <div>

                  <p className="font-semibold text-slate-200">
                    User B
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    token-user-b
                  </p>

                </div>

                <CheckCircle2 className="h-5 w-5 text-emerald-400" />

              </div>

            </div>

          </div>

        </div>

        <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900 p-6">

          <div className="flex items-center gap-3">

            <ShieldCheck className="h-5 w-5 text-cyan-400" />

            <div>

              <h2 className="font-semibold">
                Security Modules
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Active vulnerability detection modules.
              </p>

            </div>

          </div>

          <div className="mt-5 grid grid-cols-2 gap-3">

            <div className="flex items-center gap-3 rounded-lg border border-cyan-900/50 bg-cyan-950/20 p-4">

              <CheckCircle2 className="h-5 w-5 text-cyan-400" />

              <div>

                <p className="text-sm font-semibold text-slate-200">
                  BOLA Detection
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  Broken Object Level Authorization
                </p>

              </div>

            </div>

            <div className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-950 p-4">

              <Circle className="h-5 w-5 text-slate-600" />

              <div>

                <p className="text-sm font-semibold text-slate-400">
                  Broken Authentication
                </p>

                <p className="mt-1 text-xs text-slate-600">
                  Module not enabled
                </p>

              </div>

            </div>

            <div className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-950 p-4">

              <Circle className="h-5 w-5 text-slate-600" />

              <div>

                <p className="text-sm font-semibold text-slate-400">
                  Excessive Data Exposure
                </p>

                <p className="mt-1 text-xs text-slate-600">
                  Module not enabled
                </p>

              </div>

            </div>

            <div className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-950 p-4">

              <Circle className="h-5 w-5 text-slate-600" />

              <div>

                <p className="text-sm font-semibold text-slate-400">
                  Security Misconfiguration
                </p>

                <p className="mt-1 text-xs text-slate-600">
                  Module not enabled
                </p>

              </div>

            </div>

          </div>

        </div>

        <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900 p-6">

          <div className="flex items-center justify-between gap-6">

            <div>

              <p className="text-sm font-semibold text-slate-200">
                {scanning
                  ? "Security analysis running"
                  : completed
                    ? "Security analysis completed"
                    : "Ready to scan"}
              </p>

              <p className="mt-1 text-sm text-slate-500">
                {scanning
                  ? "SentinelAPI is testing the configured authentication profiles."
                  : "SentinelAPI will test the configured authentication profiles against the target API."}
              </p>

            </div>

            <button
              type="button"
              onClick={runScan}
              disabled={scanning}
              className="
                flex
                shrink-0
                items-center
                gap-2
                rounded-lg
                bg-cyan-500
                px-6
                py-3
                text-sm
                font-bold
                text-slate-950
                transition
                hover:bg-cyan-400
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >

              {scanning ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Scanning...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Start Security Scan
                </>
              )}

            </button>

          </div>

        </div>

        {error && (

          <div className="mt-6 rounded-xl border border-red-900/50 bg-red-950/20 p-5">

            <div className="flex items-start gap-3">

              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />

              <div>

                <p className="font-medium text-red-400">
                  Scanner Error
                </p>

                <p className="mt-1 text-sm text-red-300/80">
                  {error}
                </p>

              </div>

            </div>

          </div>

        )}

        {(scanning || completed) && (

          <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900 p-6">

            <div className="flex items-center gap-3">

              {completed ? (
                <CheckCircle2 className="h-5 w-5 text-emerald-400" />
              ) : (
                <Loader2 className="h-5 w-5 animate-spin text-cyan-400" />
              )}

              <div>

                <p
                  className={
                    completed
                      ? "font-medium text-emerald-400"
                      : "font-medium text-cyan-400"
                  }
                >
                  {completed
                    ? "Security analysis completed"
                    : "Security analysis in progress"}
                </p>

                <p className="mt-1 text-sm text-slate-500">
                  {progress}
                </p>

              </div>

            </div>

            <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-slate-800">

              <div
                className={`
                  h-full
                  rounded-full
                  transition-all
                  duration-500
                  ${
                    completed
                      ? "w-full bg-emerald-400"
                      : "w-2/3 bg-cyan-400 animate-pulse"
                  }
                `}
              />

            </div>

          </div>

        )}

        {completed && scanResult && (

          <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900 p-6">

            <div className="mb-5 flex items-center justify-between">

              <div>

                <p className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
                  Scan Result
                </p>

                <h2 className="mt-1 text-lg font-semibold">
                  Security Findings
                </h2>

              </div>

              <span className="rounded-full border border-emerald-900/50 bg-emerald-950/30 px-3 py-1 text-xs font-medium text-emerald-400">
                {scanResult.status}
              </span>

            </div>

            <div className="grid grid-cols-4 gap-3">

              <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">

                <p className="text-xs text-slate-500">
                  TOTAL
                </p>

                <p className="mt-2 text-2xl font-bold">
                  {vulnerabilities}
                </p>

              </div>

              <div className="rounded-lg border border-red-900/40 bg-red-950/20 p-4">

                <p className="text-xs text-red-400">
                  CRITICAL
                </p>

                <p className="mt-2 text-2xl font-bold text-red-400">
                  {critical}
                </p>

              </div>

              <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">

                <p className="text-xs text-slate-500">
                  HIGH
                </p>

                <p className="mt-2 text-2xl font-bold">
                  {high}
                </p>

              </div>

              <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">

                <p className="text-xs text-slate-500">
                  MEDIUM
                </p>

                <p className="mt-2 text-2xl font-bold">
                  {medium}
                </p>

              </div>

            </div>

            {scanResult.findings.length > 0 && (

              <div className="mt-5 space-y-2">

                {scanResult.findings.map((finding) => (

                  <div
                    key={finding.id}
                    className="flex items-center justify-between rounded-lg border border-red-900/30 bg-red-950/10 p-4"
                  >

                    <div>

                      <p className="font-semibold text-red-400">
                        {finding.id} · {finding.type}
                      </p>

                      <p className="mt-1 text-sm text-slate-300">
                        {finding.method} {finding.endpoint}
                      </p>

                      <p className="mt-1 text-xs text-slate-500">
                        {finding.attacker} →{" "}
                        {finding.resource_owner}
                      </p>

                    </div>

                    <span className="rounded-full bg-red-500/10 px-3 py-1 text-xs font-semibold text-red-400">
                      {finding.severity}
                    </span>

                  </div>

                ))}

              </div>

            )}

          </div>

        )}

      </div>

    </div>
  )
}