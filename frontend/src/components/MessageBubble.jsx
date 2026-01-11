import React, { useState } from 'react';
import CitationModal from './CitationModal';
import VerifierBadge from './VerifierBadge';

const MessageBubble = ({ message, isUser }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState(null);

  const {
    query,
    response,
    retrieval_status: retrievalStatus,
  } = message;

  const {
    final_text: finalResponse,
    citations,
    confidence_level: confidence,
  } = response || {};

  const handleCitationClick = (citation) => {
    setModalContent(citation);
    setModalOpen(true);
  };

  const renderContent = (text) => {
    if (!text) return null;
    // This regex finds both standard markdown links and the custom citation format [number].
    const parts = text.split(/(\[\d+\])/g);

    return parts.map((part, index) => {
      const citationMatch = part.match(/\[(\d+)\]/);
      if (citationMatch) {
        const docNumber = parseInt(citationMatch[1], 10);
        const citation = citations.find(c => c.doc_num === docNumber);
        if (citation) {
          return (
            <button
              key={index}
              onClick={() => handleCitationClick(citation)}
              className="inline-block bg-blue-100 text-blue-800 rounded-full px-2 py-0.5 text-xs font-semibold hover:bg-blue-200 transition-colors mx-0.5"
              title={`View citation from ${citation.source_filename}`}
            >
              {docNumber}
            </button>
          );
        }
      }
      // Basic markdown link support
      if (part.includes('](')) {
        const linkMatch = part.match(/\[(.*?)\]\((.*?)\)/);
        if (linkMatch) {
          return <a href={linkMatch[2]} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{linkMatch[1]}</a>;
        }
      }

      return <span key={index}>{part}</span>;
    });
  };

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="bg-gray-800 text-white rounded-2xl rounded-br-sm px-5 py-3 max-w-xl">
          <p>{query}</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="flex justify-start">
        <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-5 py-4 max-w-2xl">
          <div className="prose prose-sm max-w-none text-gray-800">
            {renderContent(finalResponse)}
          </div>

          {retrievalStatus && (
            <div className="mt-4 pt-3 border-t border-gray-200">
              <p className="text-xs text-gray-500">{retrievalStatus}</p>
            </div>
          )}
        </div>
        <div className="ml-2 mt-1">
          <VerifierBadge confidence={confidence || 'low'} />
        </div>
      </div>

      <CitationModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        citation={modalContent}
      />
    </>
  );
};

export default MessageBubble;
