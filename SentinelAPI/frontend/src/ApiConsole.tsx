import { useState } from "react"
import {
  AlertTriangle,
  CheckCircle2,
  Copy,
  Loader2,
  Play,
  Send,
  Server,
  ShieldAlert,
  Terminal,
} from "lucide-react"

type HeaderRow = {
  key: string
  value: string
  enabled: boolean
}

type ResponseState = {
  status: number
  statusText: string
  timeMs: number
  sizeBytes: number
  headers: Record<string, string>
  body: unknown
  isBolaViolation?: boolean
  violationMessage?: string
}

export type ConsoleEndpoint = {
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

export type ConsoleFinding = {
  id: string
  title?: string
  endpoint: string
  method: string
  attacker: string
  resource_owner: string
  object_id: number | string
  status_code: number
}

type ApiConsoleProps = {
  endpoints?: ConsoleEndpoint[]
  findings?: ConsoleFinding[]
  targetUrl?: string
}

const PRESET_PAYLOADS = [
  {
    name: "PROBE: User A → Order #102 (BOLA Attack)",
    description: "User A attempts to access User B's order 102",
    method: "GET",
    url: "http://localhost:8000/orders/102",
    headers: [{ key: "Authorization", value: "token-user-a", enabled: true }],
    body: "",
  },
  {
    name: "PROBE: User B → Order #101 (BOLA Attack)",
    description: "User B attempts to access User A's order 101",
    method: "GET",
    url: "http://localhost:8000/orders/101",
    headers: [{ key: "Authorization", value: "token-user-b", enabled: true }],
    body: "",
  },
  {
    name: "BENCHMARK: User A → Own Order #101",
    description: "Legitimate request to self-owned object",
    method: "GET",
    url: "http://localhost:8000/orders/101",
    headers: [{ key: "Authorization", value: "token-user-a", enabled: true }],
    body: "",
  },
  {
    name: "UNAUTHENTICATED: Direct Query (No Token)",
    description: "Probes authentication boundary without headers",
    method: "GET",
    url: "http://localhost:8000/orders/102",
    headers: [],
    body: "",
  },
]

export default function ApiConsole({
  endpoints = [],
  findings = [],
  targetUrl = "http://localhost:8000",
}: ApiConsoleProps) {
  const [method, setMethod] = useState("GET")
  const [url, setUrl] = useState("http://localhost:8000/orders/102")
  const [headers, setHeaders] = useState<HeaderRow[]>([
    { key: "Authorization", value: "token-user-a", enabled: true },
    { key: "Accept", value: "application/json", enabled: true },
  ])
  const [requestBody, setRequestBody] = useState("")
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<ResponseState | null>(null)
  const [error, setError] = useState("")
  const [copied, setCopied] = useState(false)

  const applyPreset = (preset: typeof PRESET_PAYLOADS[0]) => {
    setMethod(preset.method)
    setUrl(preset.url)
    setHeaders(
      preset.headers.length > 0
        ? preset.headers
        : [{ key: "Accept", value: "application/json", enabled: true }]
    )
    setRequestBody(preset.body)
    setError("")
    setResponse(null)
  }

  const addHeader = () => {
    setHeaders([...headers, { key: "", value: "", enabled: true }])
  }

  const updateHeader = (index: number, field: keyof HeaderRow, val: unknown) => {
    const updated = [...headers]
    updated[index] = { ...updated[index], [field]: val }
    setHeaders(updated)
  }

  const removeHeader = (index: number) => {
    setHeaders(headers.filter((_, i) => i !== index))
  }

  const loadEndpointIntoConsole = (ep: ConsoleEndpoint) => {
    setMethod(ep.method)
    const base = targetUrl.replace(/\/+$/, "")
    const concretePath = ep.path.replace("{order_id}", "102")
    setUrl(`${base}${concretePath}`)
    setHeaders([
      { key: "Authorization", value: "token-user-a", enabled: true },
      { key: "Accept", value: "application/json", enabled: true },
    ])
    setRequestBody("")
    setError("")
    setResponse(null)
  }

  const sendRequest = async () => {
    if (loading) return
    setError("")
    setLoading(true)
    const startTime = performance.now()

    try {
      const headerObj: Record<string, string> = {}
      headers.forEach((h) => {
        if (h.enabled && h.key.trim()) {
          headerObj[h.key.trim()] = h.value.trim()
        }
      })

      const reqInit: RequestInit = {
        method,
        headers: headerObj,
      }

      if (["POST", "PUT", "PATCH"].includes(method) && requestBody.trim()) {
        reqInit.body = requestBody
      }

      const res = await fetch(url, reqInit)
      const durationMs = Math.round(performance.now() - startTime)

      const resHeaders: Record<string, string> = {}
      res.headers.forEach((v, k) => {
        resHeaders[k] = v
      })

      const text = await res.text()
      let parsedJson: unknown = null
      try {
        parsedJson = JSON.parse(text)
      } catch {
        parsedJson = text
      }

      // Check if this response indicates a BOLA breach
      // If token is user-a and returned order has owner_id: 2, or vice versa
      let isBola = false
      let msg = ""
      const token = headerObj["Authorization"] || headerObj["authorization"]

      if (res.status === 200 && parsedJson && typeof parsedJson === "object") {
        const obj = parsedJson as Record<string, unknown>
        if (token === "token-user-a" && obj.owner_id === 2) {
          isBola = true
          msg = "BOLA EXPLOIT VERIFIED: User A accessed User B's Order (owner_id: 2)!"
        } else if (token === "token-user-b" && obj.owner_id === 1) {
          isBola = true
          msg = "BOLA EXPLOIT VERIFIED: User B accessed User A's Order (owner_id: 1)!"
        }
      }

      setResponse({
        status: res.status,
        statusText: res.statusText || (res.status === 200 ? "OK" : "RESPONSE"),
        timeMs: durationMs,
        sizeBytes: new Blob([text]).size,
        headers: resHeaders,
        body: parsedJson,
        isBolaViolation: isBola,
        violationMessage: msg,
      })
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Network request failed. Ensure target API server is online."
      )
    } finally {
      setLoading(false)
    }
  }

  const copyResponse = async () => {
    if (!response) return
    const payload = JSON.stringify(response.body, null, 2)

    try {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(payload)
      } else {
        const area = document.createElement("textarea")
        area.value = payload
        document.body.appendChild(area)
        area.select()
        document.execCommand("copy")
        document.body.removeChild(area)
      }
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setError("Clipboard access was blocked. Copy manually from the response panel.")
    }
  }

  const responseSignal = response?.isBolaViolation
    ? "Boundary violation confirmed"
    : response
    ? "Evidence collected"
    : "Awaiting request"

  // Display discovered endpoints list
  const displayEndpoints =
    endpoints.length > 0
      ? endpoints
      : [
          {
            path: "/",
            method: "GET",
            category: "collection",
            authorization_tested: false,
            finding_count: 0,
            status: "discovered",
          },
          {
            path: "/orders",
            method: "GET",
            category: "collection",
            authorization_tested: false,
            finding_count: 0,
            status: "discovered",
          },
          {
            path: "/orders/{order_id}",
            method: "GET",
            category: "object",
            parameter: "order_id",
            authorization_tested: true,
            finding_count: 2,
            status: "vulnerable",
          },
        ]

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Title & Presets Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 font-mono text-[10px] font-bold text-cyan-400">
            <Terminal className="h-3.5 w-3.5" />
            KAVACH LAB · CONTROLLED SECURITY SANDBOX
          </div>
          <h1 className="mt-2 text-3xl font-extrabold text-white tracking-tight">
            KAVACH LAB
          </h1>
          <p className="mt-1 text-sm font-semibold text-cyan-300">
            Controlled Vulnerability Demonstration Environment
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <div className="inline-flex items-center gap-2 rounded-lg border border-red-500/40 bg-red-950/30 px-3 py-1 text-[11px] font-mono font-bold text-red-400">
              <ShieldAlert className="h-3.5 w-3.5" />
              INTENTIONALLY VULNERABLE · CONTROLLED TEST ENVIRONMENT
            </div>
            <div className="status-pill rounded-full px-2.5 py-1 text-[10px] font-mono font-bold text-cyan-300">
              {responseSignal}
            </div>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Dispatch authenticated test requests across multiple identity profiles to verify zero-trust object authorization boundaries in real time.
          </p>
        </div>

        {/* Preset Payload Chips */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] uppercase font-bold text-slate-500">Attack Presets:</span>
          <div className="flex flex-wrap gap-1.5">
            {PRESET_PAYLOADS.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => applyPreset(preset)}
                className="rounded-lg border border-slate-700/80 bg-slate-900/90 px-2.5 py-1 text-[11px] font-mono text-slate-300 hover:border-cyan-500/50 hover:bg-slate-800 transition"
              >
                {preset.name.split(":")[0]}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Console Split View: REQUEST -> RESPONSE */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* REQUEST PANEL */}
        <div className="hologram-card rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-300">
                Outbound Request Spec
              </h3>
            </div>
            <span className="font-mono text-[10px] text-slate-500">HTTP/1.1</span>
          </div>

          {/* URL & Method Bar */}
          <div className="flex gap-2">
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value)}
              className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-xs font-bold font-mono text-cyan-400 focus:outline-none focus:border-cyan-500"
            >
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="PATCH">PATCH</option>
              <option value="DELETE">DELETE</option>
            </select>

            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="http://localhost:8000/orders/102"
              className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2 font-mono text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            />

            <button
              type="button"
              onClick={sendRequest}
              disabled={loading}
              className="inline-flex items-center gap-1.5 rounded-xl bg-cyan-500 px-4 py-2 text-xs font-bold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
              Send
            </button>
          </div>

          {/* Headers Editor */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                HTTP Headers ({headers.filter((h) => h.enabled).length})
              </span>
              <button
                type="button"
                onClick={addHeader}
                className="text-[10px] font-mono text-cyan-400 hover:text-cyan-300"
              >
                + Add Header
              </button>
            </div>

            <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
              {headers.map((h, i) => (
                <div key={i} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={h.enabled}
                    onChange={(e) => updateHeader(i, "enabled", e.target.checked)}
                    className="rounded border-slate-700 bg-slate-900 text-cyan-500"
                  />
                  <input
                    type="text"
                    value={h.key}
                    onChange={(e) => updateHeader(i, "key", e.target.value)}
                    placeholder="Key"
                    className="flex-1 rounded-lg border border-slate-800 bg-slate-950 px-2 py-1 font-mono text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                  <input
                    type="text"
                    value={h.value}
                    onChange={(e) => updateHeader(i, "value", e.target.value)}
                    placeholder="Value"
                    className="flex-1 rounded-lg border border-slate-800 bg-slate-950 px-2 py-1 font-mono text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                  <button
                    type="button"
                    onClick={() => removeHeader(i)}
                    className="text-xs text-slate-500 hover:text-red-400 px-1"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Request Body (for POST/PUT/PATCH) */}
          {["POST", "PUT", "PATCH"].includes(method) && (
            <div className="space-y-1.5">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                JSON Request Body
              </span>
              <textarea
                value={requestBody}
                onChange={(e) => setRequestBody(e.target.value)}
                placeholder='{ "product": "iPhone", "amount": 799 }'
                rows={4}
                className="w-full rounded-xl border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>
          )}

          {error && (
            <div className="rounded-xl border border-red-900/60 bg-red-950/40 p-3 text-xs text-red-300 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* RESPONSE PANEL */}
        <div className="hologram-card rounded-2xl p-5 space-y-4 flex flex-col">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Inbound Response Telemetry
              </h3>
            </div>
            {response && (
              <div className="flex items-center gap-3 font-mono text-[10px] text-slate-400">
                <span>{response.timeMs} ms</span>
                <span>{response.sizeBytes} bytes</span>
              </div>
            )}
          </div>

          {/* BOLA Alert Banner */}
          {response?.isBolaViolation && (
            <div className="rounded-xl border border-red-500/60 bg-red-950/40 p-3.5 text-xs text-red-200 flex items-start gap-3 shadow-lg shadow-red-950/50 animate-pulse">
              <ShieldAlert className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
              <div>
                <p className="font-extrabold uppercase tracking-wide text-red-300">
                  CRITICAL: ZERO-TRUST BOUNDARY VIOLATION DETECTED
                </p>
                <p className="mt-0.5 text-[11px] text-red-200 font-mono">
                  {response.violationMessage}
                </p>
              </div>
            </div>
          )}

          {/* Response Viewer */}
          {!response && !loading && (
            <div className="flex-1 flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-800 bg-slate-950/60 p-12 text-center text-xs text-slate-500">
              <Terminal className="h-8 w-8 text-slate-700 mb-2" />
              Ready for transmission. Select an attack preset or load a discovered endpoint below.
            </div>
          )}

          {loading && (
            <div className="flex-1 flex flex-col items-center justify-center rounded-xl border border-slate-800 bg-slate-950 p-12 text-center text-xs text-slate-400">
              <Loader2 className="h-6 w-6 animate-spin text-cyan-400 mb-3" />
              Awaiting target response stream...
            </div>
          )}

          {response && (
            <div className="flex-1 flex flex-col space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-lg px-2.5 py-1 text-xs font-mono font-bold ${
                      response.status === 200
                        ? "bg-emerald-950/80 text-emerald-300 border border-emerald-800"
                        : response.status === 401 || response.status === 403
                        ? "bg-amber-950/80 text-amber-300 border border-amber-800"
                        : "bg-red-950/80 text-red-300 border border-red-800"
                    }`}
                  >
                    HTTP {response.status} {response.statusText}
                  </span>
                </div>

                <button
                  type="button"
                  onClick={copyResponse}
                  className="inline-flex items-center gap-1 rounded bg-slate-800 px-2 py-1 text-[10px] font-mono text-slate-300 hover:bg-slate-700"
                >
                  <Copy size={12} />
                  {copied ? "Copied" : "Copy JSON"}
                </button>
              </div>

              {/* JSON Code Viewer */}
              <pre className="flex-1 overflow-x-auto rounded-xl border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-cyan-300 shadow-inner max-h-[360px]">
                {JSON.stringify(response.body, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>

      {/* DISCOVERED ENDPOINTS INVENTORY (Section 17) */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Server className="h-4 w-4 text-cyan-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Discovered Endpoint Telemetry & Security Status
            </h3>
          </div>
          <span className="text-[10px] font-mono text-slate-500">
            Mapped from target OpenAPI specification
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-[10px] uppercase text-slate-500">
                <th className="pb-2">Method</th>
                <th className="pb-2">Path</th>
                <th className="pb-2">Authentication</th>
                <th className="pb-2">Parameters</th>
                <th className="pb-2">Authorization Test</th>
                <th className="pb-2">Security Status</th>
                <th className="pb-2 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {displayEndpoints.map((ep, idx) => {
                const isVuln = ep.finding_count > 0 || ep.status === "vulnerable"
                const matchedFinding = findings.find(
                  (f) => f.endpoint === ep.path || ep.path.includes("{")
                )
                return (
                  <tr key={idx} className="hover:bg-slate-800/30 transition">
                    <td className="py-2.5">
                      <span
                        className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                          ep.method === "GET"
                            ? "bg-cyan-950 text-cyan-400 border border-cyan-800"
                            : "bg-emerald-950 text-emerald-400 border border-emerald-800"
                        }`}
                      >
                        {ep.method}
                      </span>
                    </td>
                    <td className="py-2.5 font-bold text-slate-200">{ep.path}</td>
                    <td className="py-2.5 text-slate-400">
                      {ep.path.includes("order") ? "Bearer (Header)" : "None"}
                    </td>
                    <td className="py-2.5 text-slate-400">
                      {ep.parameter ? `${ep.parameter} (path)` : "None"}
                    </td>
                    <td className="py-2.5">
                      {ep.authorization_tested ? (
                        <span className="inline-flex items-center gap-1 text-emerald-400 font-bold">
                          <CheckCircle2 size={12} /> TESTED
                        </span>
                      ) : (
                        <span className="text-slate-500">DISCOVERED</span>
                      )}
                    </td>
                    <td className="py-2.5">
                      {isVuln ? (
                        <span className="rounded bg-red-500/20 px-2 py-0.5 text-[10px] font-bold text-red-400 border border-red-500/30">
                          VULNERABLE ({matchedFinding?.id || "BOLA-001"})
                        </span>
                      ) : ep.authorization_tested ? (
                        <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/30">
                          SECURE
                        </span>
                      ) : (
                        <span className="text-slate-500">MAPPED</span>
                      )}
                    </td>
                    <td className="py-2.5 text-right">
                      <button
                        type="button"
                        onClick={() => loadEndpointIntoConsole(ep)}
                        className="inline-flex items-center gap-1 rounded bg-slate-800 px-2.5 py-1 text-[11px] font-bold text-cyan-300 hover:bg-slate-700 transition"
                      >
                        <Play size={10} /> Test In Console
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
