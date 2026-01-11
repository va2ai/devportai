import React from 'react';

const TracePanel = ({ traceId, retrievalStatus }) => {
  if (!traceId) return null;

  return (
    <div className="mt-2 ml-12 -mb-2">
      <div className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-xs text-gray-500">
        <span className="font-semibold text-gray-600">Trace ID:</span>{' '}
        <a
          href={`http://localhost:8000/traces/${traceId}`}
          target="_blank"
          rel="noopener noreferrer"
          className="font-mono text-blue-600 hover:underline"
        >
          {traceId}
        </a>
      </div>
    </div>
  );
};

export default TracePanel;
