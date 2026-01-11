import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch('http://localhost:8000/health')
        const data = await response.json()
        setHealth(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    checkHealth()
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4">
          <h1 className="text-4xl font-bold text-gray-900">RAG Verifier</h1>
          <p className="text-gray-600 mt-2">Fact-Checking with Retrieval-Augmented Generation</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-12 px-4">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6">Application Status</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Frontend Status</h3>
              <div className="flex items-center">
                <div className="w-4 h-4 bg-green-500 rounded-full mr-2"></div>
                <span className="text-green-700 font-semibold">Connected</span>
              </div>
            </div>

            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Backend Status</h3>
              {loading && <span className="text-gray-600">Checking...</span>}
              {error && <span className="text-red-600">Error: {error}</span>}
              {health && (
                <div className="flex items-center">
                  <div className={`w-4 h-4 rounded-full mr-2 ${health.status === 'ok' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <span className={health.status === 'ok' ? 'text-green-700' : 'text-red-700'}>
                    {health.status === 'ok' ? 'Connected' : 'Error'}
                  </span>
                </div>
              )}
            </div>

            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Database Status</h3>
              {health && (
                <div className="flex items-center">
                  <div className={`w-4 h-4 rounded-full mr-2 ${health.db === 'connected' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <span className={health.db === 'connected' ? 'text-green-700' : 'text-red-700'}>
                    {health.db === 'connected' ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
              )}
            </div>

            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">API Endpoint</h3>
              <p className="text-gray-700 font-mono text-sm">http://localhost:8000</p>
            </div>
          </div>

          {health && (
            <div className="mt-8 bg-gray-50 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-2">Health Check Response</h3>
              <pre className="bg-gray-900 text-green-400 p-4 rounded overflow-auto text-xs">
                {JSON.stringify(health, null, 2)}
              </pre>
            </div>
          )}
        </div>

        <div className="mt-8 bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
          <p className="text-yellow-700">
            <strong>Note:</strong> This is the foundation for the RAG Fact-Check application.
            RAG logic and verification features will be implemented in the next phase.
          </p>
        </div>
      </main>
    </div>
  )
}

export default App
