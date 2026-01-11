import React from 'react'

/**
 * CitationModal - Modal dialog showing full source chunk content
 *
 * Props:
 * - isOpen: boolean
 * - onClose: function
 * - citation: object with statement and source_chunks
 */
const CitationModal = ({ isOpen, onClose, citation }) => {
  if (!isOpen || !citation) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Citation Source</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="px-6 py-4 overflow-y-auto max-h-[calc(80vh-120px)]">
            {/* Statement */}
            <div className="mb-6">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">Statement</h4>
              <p className="text-gray-900 bg-blue-50 p-3 rounded-lg border border-blue-200">
                {citation.statement}
              </p>
              <div className="mt-2 flex items-center gap-2">
                <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                  citation.supported
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {citation.supported ? (
                    <>
                      <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      Supported
                    </>
                  ) : (
                    <>
                      <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                      Not Supported
                    </>
                  )}
                </span>
              </div>
            </div>

            {/* Source Chunks */}
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-3">
                Source Documents ({citation.source_chunks?.length || 0})
              </h4>
              <div className="space-y-4">
                {citation.source_chunks?.map((chunk, idx) => (
                  <div
                    key={chunk.chunk_id || idx}
                    className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                  >
                    {/* Document Info */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h5 className="text-sm font-medium text-gray-900">
                          {chunk.document_title || chunk.document_filename}
                        </h5>
                        <p className="text-xs text-gray-500 mt-1">
                          {chunk.document_filename} • Chunk #{chunk.chunk_index + 1}
                        </p>
                      </div>
                      <div className="ml-4 flex-shrink-0">
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {Math.round(chunk.similarity_score * 100)}% match
                        </span>
                      </div>
                    </div>

                    {/* Content */}
                    <div className="bg-white p-3 rounded border border-gray-200">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {chunk.content}
                      </p>
                    </div>

                    {/* Metadata */}
                    <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                      <span>Document ID: {chunk.document_id}</span>
                      <span>•</span>
                      <span>Chunk ID: {chunk.chunk_id}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4">
            <button
              onClick={onClose}
              className="w-full sm:w-auto px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CitationModal
