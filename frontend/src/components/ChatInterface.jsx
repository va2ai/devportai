import React, { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import TracePanel from './TracePanel';

const ChatInterface = ({ messages, onSendMessage, isLoading, selectedFilename }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput('');
  };

  return (
    <div className="flex flex-col h-full bg-white">
      <header className="px-6 py-4 border-b border-gray-100">
        <h2 className="text-xl font-semibold text-gray-800">Chat</h2>
        <p className="text-sm text-gray-500">
          {selectedFilename ? `Querying in context of ${selectedFilename}` : 'Querying across all documents'}
        </p>
      </header>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
            <svg className="w-16 h-16 mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
            <h3 className="text-lg font-semibold text-gray-700">No messages yet</h3>
            <p className="max-w-xs">Ask a question below to start the conversation.</p>
          </div>
        ) : (
          messages.map((message, idx) => (
            <React.Fragment key={message.id || idx}>
              <MessageBubble message={{ query: message.query }} isUser={true} />
              {message.response && <MessageBubble message={message} isUser={false} />}
              {message.trace_id && (
                <TracePanel
                  traceId={message.trace_id}
                  retrievalStatus={message.retrieval_status}
                />
              )}
            </React.Fragment>
          ))
        )}

        {isLoading && (
          <div className="flex justify-start">
             <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 max-w-[70%]">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '200ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '400ms' }} />
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-6 bg-white border-t border-gray-100">
        <form onSubmit={handleSubmit} className="relative">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSubmit(e)}
            placeholder="Ask a question..."
            disabled={isLoading}
            rows={1}
            className="w-full px-4 py-3 pr-20 bg-gray-100 rounded-xl border-transparent focus:ring-2 focus:ring-blue-500 focus:bg-white resize-none transition-all"
            style={{ minHeight: '52px' }}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-3 top-1/2 -translate-y-1/2 w-9 h-9 bg-gray-800 text-white rounded-full hover:bg-gray-900 disabled:bg-gray-300 transition-all flex items-center justify-center"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
