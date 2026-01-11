import React, { useState } from 'react'
import VerifierBadge from './VerifierBadge'
import CitationModal from './CitationModal'

/**
 * MessageBubble - Individual chat message with citations and verification badge
 *
 * Props:
 * - message: object containing query and response data
 * - isUser: boolean (true for user messages, false for AI responses)
 */
const MessageBubble = ({ message, isUser }) => {
  const [selectedCitation, setSelectedCitation] = useState(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const openCitationModal = (citation) => {
    setSelectedCitation(citation)
    setIsModalOpen(true)
  }

  const closeCitationModal = () => {
    setIsModalOpen(false)
    setSelectedCitation(null)
  }

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[80%] md:max-w-[70%]">
          <div className="bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-3">
            <p className="text-sm md:text-base">{message.query}</p>
          </div>
          <div className="text-xs text-gray-500 mt-1 text-right">
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        </div>
      </div>
    )
  }

  const response = message.response
  if (!response) return null

  const hasCitations = response.citations && response.citations.length > 0
  const hasUnsupportedClaims = response.unsupported_claims && response.unsupported_claims.length > 0
  const hasCorrections = response.corrections && response.corrections.length > 0

  return (
    <>
      <div className="flex justify-start mb-4">
        <div className="max-w-[80%] md:max-w-[70%]">
          {/* AI Avatar/Label */}
          <div className="flex items-center gap-2 mb-2">
            <div className="w-6 h-6 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10 3.5a1.5 1.5 0 013 0V4a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-.5a1.5 1.5 0 000 3h.5a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-.5a1.5 1.5 0 00-3 0v.5a1 1 0 01-1 1H6a1 1 0 01-1-1v-3a1 1 0 00-1-1h-.5a1.5 1.5 0 010-3H4a1 1 0 001-1V6a1 1 0 011-1h3a1 1 0 001-1v-.5z" />
              </svg>
            </div>
            <span className="text-xs font-medium text-gray-600">RAG Verifier</span>
          </div>

          {/* Message Content */}
          <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3">
            <p className="text-sm md:text-base text-gray-900 whitespace-pre-wrap">
              {response.final_text}
            </p>

            {/* Verifier Badge */}
            <div className="mt-3">
              <VerifierBadge
                confidenceLevel={response.confidence_level}
                confidenceScore={response.confidence_score}
                refusalReason={response.refusal_reason}
              />
            </div>

            {/* Unsupported Claims Warning */}
            {hasUnsupportedClaims && (
              <div className="mt-3 bg-orange-50 border border-orange-200 rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <div className="flex-1">
                    <h4 className="text-xs font-semibold text-orange-900 mb-1">
                      Unsupported Claims Detected
                    </h4>
                    <ul className="text-xs text-orange-800 space-y-1">
                      {response.unsupported_claims.map((claim, idx) => (
                        <li key={idx} className="flex items-start gap-1">
                          <span className="text-orange-600 flex-shrink-0">•</span>
                          <span>{claim}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Corrections */}
            {hasCorrections && (
              <div className="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  <div className="flex-1">
                    <h4 className="text-xs font-semibold text-blue-900 mb-1">
                      Corrections Made
                    </h4>
                    <ul className="text-xs text-blue-800 space-y-1">
                      {response.corrections.map((correction, idx) => (
                        <li key={idx} className="flex items-start gap-1">
                          <span className="text-blue-600 flex-shrink-0">•</span>
                          <span>{correction}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Citations */}
            {hasCitations && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <h4 className="text-xs font-semibold text-gray-700 mb-2">
                  Sources ({response.citations.length})
                </h4>
                <div className="flex flex-wrap gap-2">
                  {response.citations.map((citation, idx) => (
                    <button
                      key={idx}
                      onClick={() => openCitationModal(citation)}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-blue-400 transition-all text-xs group"
                    >
                      <svg className="w-3 h-3 text-gray-500 group-hover:text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
                      </svg>
                      <span className="text-gray-700 group-hover:text-blue-600">
                        [{idx + 1}]
                      </span>
                      <span className="text-gray-500 group-hover:text-blue-500 max-w-[120px] truncate">
                        {citation.source_chunks?.[0]?.document_filename || 'Source'}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Timestamp */}
          <div className="text-xs text-gray-500 mt-1">
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Citation Modal */}
      <CitationModal
        isOpen={isModalOpen}
        onClose={closeCitationModal}
        citation={selectedCitation}
      />
    </>
  )
}

export default MessageBubble
