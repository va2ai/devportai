import { useState, useEffect } from 'react'
import ChatInterface from './components/ChatInterface'
import DocumentUpload from './components/DocumentUpload'
import Sidebar from './components/Sidebar'
import './App.css'

const API_BASE_URL = 'http://localhost:3000'

function App() {
  const [health, setHealth] = useState(null)
  const [healthLoading, setHealthLoading] = useState(true)

  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('chat') // 'chat' or 'upload'
  const [uploadSuccess, setUploadSuccess] = useState(null)
  const [uploadError, setUploadError] = useState(null)
  const [selectedFilename, setSelectedFilename] = useState(null)
  const [documents, setDocuments] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadedFiles, setUploadedFiles] = useState([])

  // Check backend health on mount
  useEffect(() => {
    const checkHealth = async () => {
      setHealthLoading(true)
      try {
        const response = await fetch(`${API_BASE_URL}/health`)
        const data = await response.json()
        setHealth(data)
      } catch (err) {
        setHealth({ status: 'error' })
      } finally {
        setHealthLoading(false)
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/documents`)
        if (!response.ok) return
        const data = await response.json()
        setDocuments(Array.isArray(data.documents) ? data.documents : [])
      } catch (_) {
        // Ignore list errors
      }
    }
    fetchDocuments()
  }, [uploadedFiles]) // Refetch when new files are uploaded

  const handleSendMessage = async (query) => {
    const userMessage = {
      id: Date.now(),
      query,
      timestamp: new Date().toISOString(),
      response: null,
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          top_k: 5,
          similarity_threshold: 0.1,
          document_filename: selectedFilename || undefined,
        }),
      })

      if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorBody}`)
      }

      const data = await response.json()

      setMessages(prev =>
        prev.map(msg =>
          msg.id === userMessage.id ? { ...msg, ...data } : msg
        )
      )
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages(prev =>
        prev.map(msg =>
          msg.id === userMessage.id
            ? {
                ...msg,
                response: {
                  final_text: `Error: ${error.message}. Please check the backend connection.`,
                  confidence_level: 'refusal',
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
    setUploadSuccess(`Successfully uploaded and processed ${data.filename}.`)
    setUploadedFiles(prev => [
      {
        name: data.filename,
        documentId: data.document_id,
        chunkCount: data.chunk_count,
        summary: data.summary,
        timestamp: new Date().toISOString(),
      },
      ...prev,
    ]);
    setTimeout(() => setUploadSuccess(null), 5000)
  }

  const handleUploadError = (error) => {
    setUploadError(error)
    setTimeout(() => setUploadError(null), 5000)
  }

  return (
    <div className="flex h-screen bg-white text-gray-800">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        healthStatus={{ status: health?.status, loading: healthLoading }}
        documents={documents}
        selectedFilename={selectedFilename}
        onSelectFilename={setSelectedFilename}
      />
      <main className="flex-1 flex flex-col overflow-hidden">
        {activeTab === 'chat' ? (
          <ChatInterface
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            selectedFilename={selectedFilename}
          />
        ) : (
          <DocumentUpload
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
              isUploading={isUploading}
              setIsUploading={setIsUploading}
              uploadProgress={uploadProgress}
              setUploadProgress={setUploadProgress}
              uploadSuccess={uploadSuccess}
              uploadError={uploadError}
            />
        )}
      </main>
    </div>
  )
}

export default App
