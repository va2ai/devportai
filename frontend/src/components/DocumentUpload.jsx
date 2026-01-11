import React, { useState, useRef } from 'react';

const DocumentUpload = ({ onUploadSuccess, onUploadError, isUploading, setIsUploading, uploadProgress, setUploadProgress, uploadSuccess, uploadError }) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      uploadFile(files[0]);
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      uploadFile(files[0]);
    }
  };

  const uploadFile = async (file) => {
    setIsUploading(true);
    setUploadProgress(0);
    onUploadError(null);
    onUploadSuccess(null);
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', 'http://localhost:3000/api/v1/ingest', true);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percentComplete = Math.round((event.loaded / event.total) * 100);
        setUploadProgress(percentComplete);
      }
    };

    xhr.onload = () => {
      setIsUploading(false);
      if (xhr.status === 200 || xhr.status === 201) {
        const data = JSON.parse(xhr.responseText);
        onUploadSuccess(data);
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          onUploadError(error.detail || 'An unknown error occurred.');
        } catch (e) {
          onUploadError('An unknown error occurred.');
        }
      }
    };

    xhr.onerror = () => {
      setIsUploading(false);
      onUploadError('Upload failed. Check your network connection.');
    };

    xhr.send(formData);
  };

  return (
    <div className="flex flex-col h-full bg-white p-6">
       <header className="px-6 py-4 border-b border-gray-100 -mx-6 -mt-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-800">Upload Documents</h2>
        <p className="text-sm text-gray-500">Add new documents to your knowledge base</p>
      </header>

      <div className="flex-grow flex items-center justify-center">
        <div className="w-full max-w-lg">
          <div
            className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300 ${
              isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50'
            }`}
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input ref={fileInputRef} type="file" onChange={handleFileSelect} className="hidden" />

            <div className="flex flex-col items-center text-gray-500">
               <svg className="w-16 h-16 mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
              <p className="font-semibold text-gray-700">Drag & drop a file here</p>
              <p className="text-sm mt-1">or</p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="mt-4 px-5 py-2.5 bg-gray-800 text-white rounded-lg hover:bg-gray-900 transition-colors font-medium text-sm"
              >
                Browse File
              </button>
            </div>
          </div>

          {isUploading && (
            <div className="mt-6">
              <div className="flex justify-between items-center text-sm font-medium text-gray-700 mb-1">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full transition-all" style={{ width: `${uploadProgress}%` }} />
              </div>
            </div>
          )}

          {uploadSuccess && (
            <div className="mt-6 p-4 bg-green-50 text-green-800 border border-green-200 rounded-lg text-sm">
              {uploadSuccess}
            </div>
          )}

          {uploadError && (
            <div className="mt-6 p-4 bg-red-50 text-red-800 border border-red-200 rounded-lg text-sm">
              {uploadError}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;
