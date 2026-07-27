const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

const TOKEN_STORAGE_KEY = "accessToken"

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// sessionStorage: 탭/창을 닫으면 토큰이 자동으로 사라져 다시 로그인해야 한다.
// (localStorage와 달리 브라우저를 닫았다 열면 세션이 유지되지 않음 — 의도된 동작.)
export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_STORAGE_KEY)
}

export function setToken(token: string): void {
  sessionStorage.setItem(TOKEN_STORAGE_KEY, token)
}

export function clearToken(): void {
  sessionStorage.removeItem(TOKEN_STORAGE_KEY)
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const problem = (await response.json()) as { detail?: unknown }
    if (typeof problem.detail === "string" && problem.detail) {
      return problem.detail
    }
    if (Array.isArray(problem.detail) && problem.detail.length > 0) {
      return problem.detail
        .map((entry) => (entry && typeof entry === "object" && "msg" in entry ? String(entry.msg) : String(entry)))
        .join(" / ")
    }
    return `요청 실패 (${response.status})`
  } catch {
    return `요청 실패 (${response.status})`
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const isFormData = options.body instanceof FormData
  const headers: HeadersInit = {
    ...(options.body && !isFormData ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })

  if (!response.ok) {
    if (response.status === 401 && window.location.pathname !== "/login") {
      clearToken()
      window.location.href = "/login"
    }
    throw new ApiError(response.status, await parseErrorDetail(response))
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  postForm: <T>(path: string, form: FormData) => request<T>(path, { method: "POST", body: form }),
}
