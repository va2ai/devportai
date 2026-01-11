import React, { useState } from 'react'

/**
 * TracePanel - Collapsible developer panel showing latency breakdown
 *
 * Props:
 * - traceData: object with timing information
 * - traceId: string (optional)
 * - retrievalStatus: string
 */
const TracePanel = ({ traceData, traceId, retrievalStatus }) => {
  const [isOpen, setIsOpen] = useState(false)

  if (!traceData) return null

  const {
    retrieval_time_ms = 0,
    generation_time_ms = 0,
    verification_time_ms = 0,
    total_time_ms = 0
  } = traceData

  const getProgressBarWidth = (time) => {
    if (total_time_ms === 0) return '0%'
    return `${(time / total_time_ms) * 100}%`
  }

  const formatTime = (ms) => {
    if (ms < 1000) return `${Math.round(ms)}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden bg-white shadow-sm">
      {/* Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span className="text-sm font-semibold text-gray-700">
            Performance Trace
          </span>
          <span className="text-xs text-gray-500">
            ({formatTime(total_time_ms)} total)
          </span>
        </div>
        <svg
          className={`w-5 h-5 text-gray-600 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Content */}
      {isOpen && (
        <div className="p-4 space-y-4">
          {/* Trace ID */}
          {traceId && (
            <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
              <span className="text-xs font-medium text-blue-700">Trace ID:</span>
              <code className="ml-2 text-xs text-blue-900 font-mono">{traceId}</code>
            </div>
          )}

          {/* Retrieval Status */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Retrieval Status:</span>
            <span className={`px-2 py-1 rounded text-xs font-semibold ${
              retrievalStatus === 'success'
                ? 'bg-green-100 text-green-800'
                : retrievalStatus === 'partial'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
            }`}>
              {retrievalStatus || 'unknown'}
            </span>
          </div>

          {/* Latency Breakdown */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-gray-700">Latency Breakdown</h4>

            {/* Retrieval */}
            {retrieval_time_ms > 0 && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-gray-600">Retrieval</span>
                  <span className="text-xs font-medium text-gray-900">
                    {formatTime(retrieval_time_ms)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all"
                    style={{ width: getProgressBarWidth(retrieval_time_ms) }}
                  />
                </div>
              </div>
            )}

            {/* Generation */}
            {generation_time_ms > 0 && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-gray-600">Generation</span>
                  <span className="text-xs font-medium text-gray-900">
                    {formatTime(generation_time_ms)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-purple-500 h-2 rounded-full transition-all"
                    style={{ width: getProgressBarWidth(generation_time_ms) }}
                  />
                </div>
              </div>
            )}

            {/* Verification */}
            {verification_time_ms > 0 && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-gray-600">Verification</span>
                  <span className="text-xs font-medium text-gray-900">
                    {formatTime(verification_time_ms)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full transition-all"
                    style={{ width: getProgressBarWidth(verification_time_ms) }}
                  />
                </div>
              </div>
            )}

            {/* Total */}
            <div className="pt-3 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-700">Total Time</span>
                <span className="text-sm font-bold text-gray-900">
                  {formatTime(total_time_ms)}
                </span>
              </div>
            </div>
          </div>

          {/* Legend */}
          <div className="pt-3 border-t border-gray-200">
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-blue-500 rounded" />
                <span className="text-gray-600">Retrieval</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-purple-500 rounded" />
                <span className="text-gray-600">Generation</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-green-500 rounded" />
                <span className="text-gray-600">Verification</span>
              </div>
            </div>
          </div>

          {/* Note */}
          <div className="text-xs text-gray-500 italic">
            Note: Latency breakdown shows time spent in each pipeline stage.
            Retrieval includes semantic search, generation creates the draft answer,
            and verification performs adversarial fact-checking.
          </div>
        </div>
      )}
    </div>
  )
}

export default TracePanel
