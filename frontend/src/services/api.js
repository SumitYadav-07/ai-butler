// The ONLY file in the frontend that makes network calls.
// It talks to this project's own backend. Nothing here contacts any financial institution.
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const TOKEN_KEY = 'ai_butler_token'

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

export class ApiError extends Error {
  constructor(message, { status = 0, code = 'error', details = null } = {}) {
    super(message)
    this.status = status
    this.code = code
    this.details = details
  }
}

async function request(method, path, body, params) {
  const url = new URL(`${BASE}/api${path}`)
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, value)
  })

  const headers = {}
  const token = tokenStore.get()
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let response
  try {
    response = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError('Cannot reach the server. Please check that the backend is running.')
  }

  let payload = null
  try {
    payload = await response.json()
  } catch {
    /* empty or non-JSON body */
  }

  if (!response.ok) {
    const err = payload?.error
    if (response.status === 401 && token && path !== '/auth/login') {
      tokenStore.clear()
      window.dispatchEvent(new Event('auth:expired'))
    }
    throw new ApiError(err?.message || 'Something went wrong. Please try again.', {
      status: response.status,
      code: err?.code,
      details: err?.details,
    })
  }
  return payload
}

export const api = {
  auth: {
    register: (b) => request('POST', '/auth/register', b),
    login: (b) => request('POST', '/auth/login', b),
    logout: () => request('POST', '/auth/logout'),
    me: () => request('GET', '/auth/me'),
  },
  profile: {
    get: () => request('GET', '/profile'),
    update: (b) => request('PUT', '/profile', b),
  },
  transactions: {
    list: (params) => request('GET', '/transactions', undefined, params),
    create: (b) => request('POST', '/transactions', b),
    remove: (id) => request('DELETE', `/transactions/${id}`),
  },
  dashboard: () => request('GET', '/dashboard'),
  analytics: () => request('GET', '/analytics'),
  emi: { calculate: (b) => request('POST', '/emi/calculate', b) },
  goals: {
    list: () => request('GET', '/goals'),
    create: (b) => request('POST', '/goals', b),
    update: (id, b) => request('PUT', `/goals/${id}`, b),
    remove: (id) => request('DELETE', `/goals/${id}`),
  },
  emergency: {
    get: () => request('GET', '/emergency-fund'),
    update: (b) => request('PUT', '/emergency-fund', b),
  },
  dailyBalance: {
    prompt: () => request('GET', '/daily-balance/prompt'),
    submit: (b) => request('POST', '/daily-balance', b),
  },
  butler: {
    chat: (message) => request('POST', '/butler/chat', { message }),
    history: () => request('GET', '/butler/history'),
    clear: () => request('DELETE', '/butler/history'),
  },
  // recurring-expenses | recurring-income | emis | savings
  recurring: (path) => ({
    list: () => request('GET', `/${path}`),
    create: (b) => request('POST', `/${path}`, b),
    remove: (id) => request('DELETE', `/${path}/${id}`),
  }),
}