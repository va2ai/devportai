import React, { useState, useRef } from 'react'

/**
 * DocumentUpload - Drag-and-drop file upload component
 *
 * Props:
 * - onUploadSuccess: function(data) => void
 * - onUploadError: function(error) => void
 */
const DocumentUpload = ({ onUploadSuccess, onUploadError }) => {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadedFiles, setUploadedFiles] = useState([])
  const fileInputRef = useRef(null)

  const handleDragEnter = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    handleFiles(files)
  }

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files)
    handleFiles(files)
  }

  const handleFiles = async (files) => {
    // Filter for supported file types
    const supportedFiles = files.filter(file => {
      const type = file.type
      return type === 'application/pdf' || type === 'text/plain'
    })

    if (supportedFiles.length === 0) {
      onUploadError?.('Please upload PDF or TXT files only')
      return
    }

    // Upload files one by one
    for (const file of supportedFiles) {
      await uploadFile(file)
    }
  }

  const uploadFile = async (file) => {
    setIsUploading(true)
    setUploadProgress(0)

    const formData = new FormData()
    formData.append('file', file)

    try {
      // Simulate progress (since we don't have real upload progress)
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      const response = await fetch('http://localhost:3000/api/v1/ingest', {
        method: 'POST',
        body: formData,
      })

      clearInterval(progressInterval)
      setUploadProgress(100)

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()

      // Add to uploaded files list
      setUploadedFiles(prev => [{
        name: file.name,
        size: file.size,
        documentId: data.document_id,
        chunkCount: data.chunk_count,
        timestamp: new Date().toISOString(),
      }, ...prev])

      onUploadSuccess?.(data)

      // Reset progress after a delay
      setTimeout(() => {
        setUploadProgress(0)
      }, 2000)

    } catch (error) {
      console.error('Upload error:', error)
      onUploadError?.(error.message)
      setUploadProgress(0)
    } finally {
      setIsUploading(false)
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Documents</h3>

      {/* Upload Area */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400 bg-gray-50'
        }`}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.txt"
          onChange={handleFileSelect}
          className="hidden"
        />

        {isUploading ? (
          <div className="space-y-4">
            <div className="flex items-center justify-center">
              <svg className="animate-spin h-12 w-12 text-blue-600" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">Uploading...</p>
              <p className="text-xs text-gray-500 mt-1">Processing and generating embeddings</p>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-xs text-gray-600">{uploadProgress}%</p>
          </div>
        ) : (
          <>
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="mt-2 text-sm font-medium text-gray-900">
              Drop files here or click to browse
            </p>
            <p className="mt-1 text-xs text-gray-500">
              PDF or TXT files up to 50MB
            </p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              Select Files
            </button>
          </>
        )}
      </div>

      {/* Uploaded Files List */}
      {uploadedFiles.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">
            Recently Uploaded ({uploadedFiles.length})
          </h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {uploadedFiles.map((file, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3 bg-green-50 border border-green-200 rounded-lg"
              >
                <div className="flex-shrink-0">
                  <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {file.name}
                  </p>
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-600">
                    <span>{formatFileSize(file.size)}</span>
                    <span>•</span>
                    <span>{file.chunkCount} chunks</span>
                    <span>•</span>
                    <span>Doc ID: {file.documentId}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Help Text */}
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start gap-2">
          <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div className="flex-1">
            <p className="text-xs font-medium text-blue-900">What happens when you upload?</p>
            <ul className="mt-1 text-xs text-blue-800 space-y-1">
              <li>1. Text is extracted from your document</li>
              <li>2. Content is split into searchable chunks</li>
              <li>3. Embeddings are generated for semantic search</li>
              <li>4. Document becomes available for chat queries</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DocumentUpload
