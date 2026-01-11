import React from 'react';

const CitationModal = ({ isOpen, onClose, citation }) => {
  if (!isOpen || !citation) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        <header className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">Citation Details</h2>
            <p className="text-sm text-gray-500 truncate" title={citation.source_filename}>
              Source: {citation.source_filename}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </header>
        
        <main className="p-6 overflow-y-auto">
          <blockquote className="border-l-4 border-gray-300 pl-4 py-2 bg-gray-50 rounded-r-lg">
            <p className="text-gray-700 italic">
              {citation.text_content}
            </p>
          </blockquote>

           <div className="mt-6 text-sm">
            <h3 className="font-semibold text-gray-700 mb-2">Metadata</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2 text-gray-600">
              <p><strong>Document ID:</strong> <span className="font-mono text-xs bg-gray-100 p-1 rounded">{citation.source_document_id}</span></p>
              <p><strong>Chunk ID:</strong> <span className="font-mono text-xs bg-gray-100 p-1 rounded">{citation.source_chunk_id}</span></p>
              <p><strong>Similarity Score:</strong> {citation.similarity_score.toFixed(4)}</p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default CitationModal;
