import { useState, useEffect } from 'react'
import ChatInterface from './components/ChatInterface'
import './App.css'

const API_BASE_URL = 'http://localhost:3000'

function App() {
  const [health, setHealth] = useState(null)
  const [healthLoading, setHealthLoading] = useState(true)
  const [healthError, setHealthError] = useState(null)

  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [latestTrace, setLatestTrace] = useState(null)

  // Check backend health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/health`)
        const data = await response.json()
        setHealth(data)
        setHealthError(null)
      } catch (err) {
        setHealthError(err.message)
      } finally {
        setHealthLoading(false)
      }
    }

    checkHealth()
    // Refresh health check every 30 seconds
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleSendMessage = async (query) => {
    // Create user message
    const userMessage = {
      id: Date.now(),
      query,
      timestamp: new Date().toISOString(),
      response: null,
      traceData: null,
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    const startTime = performance.now()

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          top_k: 5,
          similarity_threshold: 0.5,
        }),
      })

      const endTime = performance.now()
      const totalTime = endTime - startTime

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()

      // Simulate trace data breakdown (since backend doesn't return timing yet)
      // In production, the backend should include these timings
      const traceData = {
        retrieval_time_ms: totalTime * 0.15, // ~15% retrieval
        generation_time_ms: totalTime * 0.50, // ~50% generation
        verification_time_ms: totalTime * 0.35, // ~35% verification
        total_time_ms: totalTime,
      }

      // Update the message with response
      setMessages(prev =>
        prev.map(msg =>
          msg.id === userMessage.id
            ? {
                ...msg,
                response: data.response,
                trace_id: data.trace_id,
                retrieval_status: data.retrieval_status,
                traceData,
              }
            : msg
        )
      )

      setLatestTrace(traceData)
    } catch (error) {
      console.error('Error sending message:', error)

      // Add error response
      setMessages(prev =>
        prev.map(msg =>
          msg.id === userMessage.id
            ? {
                ...msg,
                response: {
                  final_text: `Error: ${error.message}. Please make sure the backend is running and try again.`,
                  confidence_level: 'refusal',
                  confidence_score: 0.0,
                  refusal_reason: 'API Error',
                  citations: [],
                  unsupported_claims: [],
                  corrections: [],
                },
              }
            : msg
        )
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900">
                RAG Verifier
              </h1>
              <p className="text-gray-600 text-xs sm:text-sm mt-1">
                Fact-Checking with Retrieval-Augmented Generation
              </p>
            </div>
            {/* Status Indicator */}
            <div className="flex items-center gap-2">
              {healthLoading ? (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 rounded-full">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
                  <span className="text-xs text-gray-600 hidden sm:inline">Checking...</span>
                </div>
              ) : health?.status === 'ok' ? (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-green-100 rounded-full">
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                  <span className="text-xs text-green-700 font-medium hidden sm:inline">Online</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-red-100 rounded-full">
                  <div className="w-2 h-2 bg-red-500 rounded-full" />
                  <span className="text-xs text-red-700 font-medium hidden sm:inline">Offline</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-4 sm:py-6 lg:py-8 px-4 sm:px-6 lg:px-8">
        {/* Health Check Error */}
        {healthError && (
          <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-4 rounded">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">
                  <strong>Backend Offline:</strong> {healthError}
                </p>
                <p className="text-xs text-red-600 mt-1">
                  Make sure the backend is running at {API_BASE_URL}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Chat Interface */}
        <div className="h-[calc(100vh-200px)] sm:h-[calc(100vh-180px)]">
          <ChatInterface
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            latestTrace={latestTrace}
          />
        </div>

        {/* Info Banner */}
        <div className="mt-4 bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                <strong>How it works:</strong> Your questions are processed through a three-step verification pipeline:
              </p>
              <ul className="text-xs text-blue-600 mt-2 space-y-1 list-disc list-inside">
                <li><strong>Retrieval:</strong> Semantic search finds relevant document chunks</li>
                <li><strong>Generation:</strong> AI drafts an answer using only retrieved context</li>
                <li><strong>Verification:</strong> Adversarial checker validates claims against sources</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
