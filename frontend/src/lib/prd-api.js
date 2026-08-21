const API_BASE = '/api'

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  if (!response.ok) {
    const errorText = await response.text().catch(() => '')
    throw new Error(
      `API request failed (${response.status}): ${errorText || response.statusText}`
    )
  }

  return response.json()
}

const prdApi = {
  /**
   * Get overall system health and PRD compliance status.
   */
  async getSystemHealth() {
    return request('/prd/system-health')
  },

  /**
   * Get background queue metrics.
   */
  async getQueueMetrics() {
    return request('/prd/queue-metrics')
  },
}

export default prdApi