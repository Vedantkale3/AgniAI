import axios from 'axios'

const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const client = axios.create({
  baseURL: API_BASE_URL,
})

client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('mrpl_access_token')

    if (token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => Promise.reject(error),
)

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('mrpl_access_token')
      localStorage.removeItem('mrpl_authenticated_user')

      if (window.location.pathname !== '/login') {
        window.location.assign('/login')
      }
    }

    return Promise.reject(error)
  },
)

export const networkStatus = () =>
  client.get('/api/network/status')

export const getEgressAlerts = () =>
  client.get('/api/network/egress-alerts')

export const getModelRegistry = () =>
  client.get('/api/models/registry')

export const previewRouting = (text) =>
  client.get('/api/models/preview-routing', {
    params: { text },
  })

export const runAgent = (goal) =>
  client.post('/api/agent/run', { goal })

export const runAgentWithImage = (goal, file) => {
  const formData = new FormData()
  formData.append('goal', goal)
  formData.append('file', file)

  return client.post('/api/agent/run-with-image', formData)
}

export const getKnowledgeStats = () =>
  client.get('/api/knowledge/stats')

export const kbStats = getKnowledgeStats

export const searchKnowledge = (query, topK = 5) =>
  client.get('/api/knowledge/search', {
    params: {
      q: query,
      top_k: topK,
    },
  })

export const ingestDocument = (
  file,
  docType = 'SOP',
  isScanned = false,
) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('doc_type', docType)
  formData.append('is_scanned', String(isScanned))

  return client.post('/api/knowledge/ingest', formData)
}

export const ingestKnowledgeDocument = ingestDocument

export const runSandboxCode = (code) =>
  client.post('/api/sandbox/run', { code })

export const runSandbox = runSandboxCode

export const listDeliverables = () =>
  client.get('/api/deliverables/list')

export const downloadDeliverable = (filename) =>
  client.get(
    `/api/deliverables/download/${encodeURIComponent(filename)}`,
    { responseType: 'blob' },
  )

// Compatibility export for components that still display a link.
// Do not use this for protected downloads; use downloadDeliverable().
export const downloadUrl = (filename) =>
  `${API_BASE_URL}/api/deliverables/download/${encodeURIComponent(filename)}`

export const loginRequest = (username, password) =>
  axios.post(`${API_BASE_URL}/api/auth/login`, {
    username,
    password,
  })

export const getCurrentUser = () =>
  client.get('/api/auth/me')

export const logoutRequest = () =>
  client.post('/api/auth/logout')

export default client
