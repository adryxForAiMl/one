/**
 * Strict Target URL Validation for KAVACH
 * Rejects filenames, presentation files, random text strings, and malformed targets.
 * Requires real HTTP/HTTPS API URLs.
 */

const FORBIDDEN_EXTENSIONS = new Set([
  "pptx", "ppt", "pdf", "docx", "doc", "xlsx", "xls", "zip", "tar", "gz",
  "rar", "png", "jpg", "jpeg", "gif", "svg", "mp4", "mp3", "exe", "dmg",
  "sh", "bin", "apk", "iso", "csv", "tsv", "txt", "md"
])

export type UrlValidationResult = {
  isValid: boolean
  normalizedUrl: string
  error?: string
  warning?: string
}

export function validateTargetUrl(rawUrl: string): UrlValidationResult {
  const trimmed = rawUrl.trim()

  if (!trimmed) {
    return {
      isValid: false,
      normalizedUrl: "",
      error: "Target API URL is required.",
    }
  }

  // Reject strings with whitespace in the middle
  if (/\s/.test(trimmed)) {
    return {
      isValid: false,
      normalizedUrl: "",
      error: "URL cannot contain spaces.",
    }
  }

  // Reject obvious document/filename patterns like "presentation.pptx" or "audit.pdf"
  const lastSegment = trimmed.split("/").pop() || ""
  const extensionMatch = lastSegment.match(/\.([a-zA-Z0-9]+)$/)
  if (extensionMatch) {
    const ext = extensionMatch[1].toLowerCase()
    if (FORBIDDEN_EXTENSIONS.has(ext)) {
      return {
        isValid: false,
        normalizedUrl: "",
        error: `Files of type .${ext} are not API target endpoints. Provide a valid HTTP/HTTPS API URL.`,
      }
    }
  }

  // Require explicit http:// or https:// or accept localhost:port / 127.0.0.1:port
  let urlToParse = trimmed
  if (!/^https?:\/\//i.test(trimmed)) {
    // If it looks like a file name (e.g. "report.docx" or "test_file"), do NOT prepend http://
    if (!trimmed.includes(".") && !trimmed.startsWith("localhost")) {
      return {
        isValid: false,
        normalizedUrl: "",
        error: "Invalid target. Provide a complete URL starting with http:// or https://",
      }
    }
    // Check if it's localhost or an IP or a domain
    const hostPart = trimmed.split("/")[0].split(":")[0]
    const isLocal = hostPart === "localhost" || hostPart === "127.0.0.1" || hostPart === "0.0.0.0"
    const isDomain = hostPart.includes(".") && hostPart.length > 3
    if (!isLocal && !isDomain) {
      return {
        isValid: false,
        normalizedUrl: "",
        error: "Target must be a valid API hostname or IP address.",
      }
    }
    urlToParse = `http://${trimmed}`
  }

  try {
    const parsed = new URL(urlToParse)

    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return {
        isValid: false,
        normalizedUrl: "",
        error: "Target must use http:// or https:// protocol.",
      }
    }

    if (!parsed.hostname) {
      return {
        isValid: false,
        normalizedUrl: "",
        error: "Target URL must contain a valid hostname.",
      }
    }

    // Hostname checks
    const hostname = parsed.hostname.toLowerCase()
    const isLocalhost = hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1"
    const hasDot = hostname.includes(".")
    
    if (!isLocalhost && !hasDot) {
      return {
        isValid: false,
        normalizedUrl: "",
        error: "Target hostname must be a valid domain or local host (e.g., api.example.com or localhost).",
      }
    }

    // Reconstruct normalized URL (no trailing slash, standard scheme/host/path)
    const normalized = `${parsed.protocol}//${parsed.host}${parsed.pathname}`.replace(/\/+$/, "")

    return {
      isValid: true,
      normalizedUrl: normalized,
      warning: parsed.protocol === "http:" && !isLocalhost
        ? "Target uses unencrypted HTTP. Use HTTPS for production APIs."
        : undefined,
    }
  } catch {
    return {
      isValid: false,
      normalizedUrl: "",
      error: "Malformed URL. Expected format: https://api.example.com or http://localhost:8000",
    }
  }
}
