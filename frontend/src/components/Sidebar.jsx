import React from 'react';

const Sidebar = ({ activeTab, setActiveTab, healthStatus, documents, selectedFilename, onSelectFilename }) => {
  const { status, loading } = healthStatus;

  return (
    <aside className="w-80 bg-gray-50 p-6 flex flex-col h-screen">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 bg-gradient-to-br from-gray-700 to-gray-900 rounded-lg flex items-center justify-center">
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h1 className="text-xl font-bold text-gray-800">RAG Verifier</h1>
          <p className="text-xs text-gray-500">Fact-Checking with AI</p>
        </div>
      </div>

      <nav className="flex flex-col gap-2 mb-8">
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
            activeTab === 'chat'
              ? 'bg-gray-800 text-white shadow-md'
              : 'text-gray-600 hover:bg-gray-200'
          }`}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
          <span className="font-medium">Chat</span>
        </button>
        <button
          onClick={() => setActiveTab('upload')}
          className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
            activeTab === 'upload'
              ? 'bg-gray-800 text-white shadow-md'
              : 'text-gray-600 hover:bg-gray-200'
          }`}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
          <span className="font-medium">Upload</span>
        </button>
      </nav>

      <div className="flex-grow overflow-y-auto">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Documents</h2>
        <div className="flex flex-col gap-1.5">
          <button
            onClick={() => onSelectFilename(null)}
            className={`w-full text-left text-sm px-3 py-2 rounded-md transition-colors ${
              !selectedFilename ? 'bg-blue-100 text-blue-800 font-semibold' : 'hover:bg-gray-200 text-gray-700'
            }`}
          >
            All Documents
          </button>
          {documents.map(doc => (
            <button
              key={`${doc.document_id}-${doc.filename}`}
              onClick={() => onSelectFilename(doc.filename)}
              className={`w-full text-left text-sm px-3 py-2 rounded-md truncate transition-colors ${
                selectedFilename === doc.filename ? 'bg-blue-100 text-blue-800 font-semibold' : 'hover:bg-gray-200 text-gray-700'
              }`}
              title={doc.filename}
            >
              {doc.filename}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-auto pt-6 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">Backend Status</span>
          {loading ? (
            <div className="flex items-center gap-2 px-2.5 py-1 bg-gray-200 rounded-full">
              <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-pulse" />
              <span className="text-xs text-gray-600">Checking...</span>
            </div>
          ) : status === 'ok' ? (
            <div className="flex items-center gap-2 px-2.5 py-1 bg-green-100 rounded-full">
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
              <span className="text-xs text-green-700 font-medium">Online</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-2.5 py-1 bg-red-100 rounded-full">
              <div className="w-1.5 h-1.5 bg-red-500 rounded-full" />
              <span className="text-xs text-red-700 font-medium">Offline</span>
            </div>
          )}
        </div>
        {status !== 'ok' && !loading && (
           <p className="text-xs text-red-500 mt-2">Could not connect to the backend. Please ensure it's running.</p>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
