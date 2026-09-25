/**
 * KAVACH Centralized API Client
 * Centralizes all communication with the KAVACH Core backend.
 * Uses VITE_API_BASE_URL with safe development fallback.
 */

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8001"
).replace(/\/+$/, "")

export type PreflightCheckItem = {
  name: string
  label: string
  status: "pass" | "warn" | "fail"
  detail: string
}

export type PreflightResponse = {
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
  endpoints?: Array<{
    path: string
    method: string
    category: string
    parameter?: string | null
    collection_path?: string | null
    authorization_tested: boolean
    finding_count: number
    severity?: string | null
    status: string
  }>
  checklist: PreflightCheckItem[]
  message: string
  what_next: string
}

export type AuthenticationProfilePayload = {
  name: string
  type: string
  token?: string
  api_key?: string
  header?: string
}

export type ScanRequestPayload = {
  target_url: string
  authentication_profiles: AuthenticationProfilePayload[]
}

export class ApiError extends Error {
  status?: number
  stateCode?: string
  constructor(message: string, status?: number, stateCode?: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.stateCode = stateCode
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`

  const defaultHeaders: Record<string, string> = {
    "Accept": "application/json",
  }

  if (options.body && typeof options.body === "string") {
    defaultHeaders["Content-Type"] = "application/json"
  }

  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...(options.headers as Record<string, string> || {}),
      },
    })

    if (!res.ok) {
      let message = `Request failed with HTTP ${res.status}`
      let stateCode: string | undefined

      try {
        const errorJson = await res.json()
        if (typeof errorJson?.detail === "string") {
          message = errorJson.detail
        } else if (Array.isArray(errorJson?.detail)) {
          message = errorJson.detail.map((d: { msg?: string }) => d.msg || "Validation error").join("; ")
        }
        if (errorJson?.state_code) {
          stateCode = errorJson.state_code
        }
      } catch {
        // Fallback to text or status
        const text = await res.text().catch(() => "")
        if (text) message = text
      }

      throw new ApiError(message, res.status, stateCode)
    }

    return (await res.json()) as T
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err
    }

    if (err instanceof TypeError && err.message.toLowerCase().includes("fetch")) {
      throw new ApiError(
        `Unable to connect to KAVACH Core backend at ${API_BASE_URL}. Ensure the backend service is running (e.g. uvicorn app.main:app --port 8001).`,
        0,
        "CONNECTION_REFUSED"
      )
    }

    throw new ApiError(
      err instanceof Error ? err.message : "An unexpected API error occurred."
    )
  }
}

/**
 * Check backend health
 */
export async function checkBackendHealth() {
  return request<{ status: string; service: string; version: string }>("/health")
}

/**
 * Validate target API via POST /validate-target
 */
export async function validateTargetApi(targetUrl: string): Promise<PreflightResponse> {
  return request<PreflightResponse>("/validate-target", {
    method: "POST",
    body: JSON.stringify({
      target_url: targetUrl,
      target: targetUrl,
    }),
  })
}

/**
 * Execute zero-trust security scan via POST /scan
 */
export async function executeSecurityScan<T>(payload: ScanRequestPayload): Promise<T> {
  return request<T>("/scan", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

/**
 * Fetch scan details by ID via GET /scans/{scanId}
 */
export async function fetchScanDetails<T>(scanId: string): Promise<T> {
  return request<T>(`/scans/${encodeURIComponent(scanId)}`)
}
