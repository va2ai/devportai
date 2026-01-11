import { useState, useEffect } from 'react'
import ChatInterface from './components/ChatInterface'
import DocumentUpload from './components/DocumentUpload'
import './App.css'

const API_BASE_URL = 'http://localhost:3000'

function App() {
  const [health, setHealth] = useState(null)
  const [healthLoading, setHealthLoading] = useState(true)
  const [healthError, setHealthError] = useState(null)

  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [latestTrace, setLatestTrace] = useState(null)
  const [activeTab, setActiveTab] = useState('chat') // 'chat' or 'upload'
  const [uploadSuccess, setUploadSuccess] = useState(null)
  const [uploadError, setUploadError] = useState(null)

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
          similarity_threshold: 0.1,
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

  const handleUploadSuccess = (data) => {
    setUploadSuccess(`Successfully uploaded ${data.filename} (${data.chunk_count} chunks created)`)
    setUploadError(null)
    // Clear success message after 5 seconds
    setTimeout(() => setUploadSuccess(null), 5000)
  }

  const handleUploadError = (error) => {
    setUploadError(error)
    setUploadSuccess(null)
    // Clear error message after 5 seconds
    setTimeout(() => setUploadError(null), 5000)
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
        {/* Tab Navigation */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('chat')}
                className={`${
                  activeTab === 'chat'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors flex items-center gap-2`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                Chat
              </button>
              <button
                onClick={() => setActiveTab('upload')}
                className={`${
                  activeTab === 'upload'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors flex items-center gap-2`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                Upload Documents
              </button>
            </nav>
          </div>
        </div>

        {/* Upload Success/Error Messages */}
        {uploadSuccess && (
          <div className="mb-4 bg-green-50 border-l-4 border-green-400 p-4 rounded">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-green-700">{uploadSuccess}</p>
              </div>
            </div>
          </div>
        )}

        {uploadError && (
          <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-4 rounded">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700">{uploadError}</p>
              </div>
            </div>
          </div>
        )}

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

        {/* Content Area - Conditional Rendering */}
        {activeTab === 'chat' ? (
          <>
            {/* Chat Interface */}
            <div className="h-[calc(100vh-260px)] sm:h-[calc(100vh-240px)]">
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
          </>
        ) : (
          <>
            {/* Document Upload */}
            <DocumentUpload
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
            />

            {/* Upload Info Banner */}
            <div className="mt-4 bg-purple-50 border-l-4 border-purple-400 p-4 rounded">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-purple-700">
                    <strong>Tip:</strong> After uploading documents, switch to the Chat tab to ask questions about your content.
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}

export default App
