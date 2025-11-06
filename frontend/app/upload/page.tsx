'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api';

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  
  const [formData, setFormData] = useState({
    email: '',
    name: '',
    roleTarget: '',
    levelTarget: '',
    resumeText: '',
  });
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Load data from landing page
  useEffect(() => {
    const targetRole = localStorage.getItem('targetRole') || '';
    setFormData(prev => ({ ...prev, roleTarget: targetRole }));
  }, []);

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type === 'application/pdf') {
      setResumeFile(files[0]);
      setFormData({ ...formData, resumeText: '' });
    } else {
      setError('Please drop a PDF file');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setResumeFile(e.target.files[0]);
      setFormData({ ...formData, resumeText: '' });
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const pastedText = e.clipboardData.getData('text');
    if (pastedText) {
      setFormData({ ...formData, resumeText: formData.resumeText + pastedText });
      setResumeFile(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('email', formData.email);
      if (formData.name) formDataToSend.append('name', formData.name);
      
      // Use targetRole from localStorage or form
      const targetRole = localStorage.getItem('targetRole') || formData.roleTarget;
      if (targetRole) formDataToSend.append('roleTarget', targetRole);
      
      if (formData.levelTarget) formDataToSend.append('levelTarget', formData.levelTarget);
      
      if (resumeFile) {
        formDataToSend.append('resumeFile', resumeFile);
      } else if (formData.resumeText) {
        formDataToSend.append('resumeText', formData.resumeText);
      } else {
        throw new Error('Please upload a PDF file, drag-and-drop, or paste resume text');
      }

      const response = await apiClient.post('/api/profile/ingest', formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      localStorage.setItem('userId', response.data.userId);
      
      // Automatically trigger job search after upload
      const location = localStorage.getItem('location') || '';
      const recency = localStorage.getItem('recency') || 'w2';
      
      // Redirect to jobs page with auto-search
      router.push(`/jobs?autoSearch=true&query=${encodeURIComponent(targetRole)}&location=${encodeURIComponent(location)}&recency=${recency}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload resume');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Upload Your Resume</h1>
          <p className="text-gray-600">
            {formData.roleTarget && `Looking for: ${formData.roleTarget}`}
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-xl p-8 border border-purple-100">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email *
              </label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Level
              </label>
              <select
                value={formData.levelTarget}
                onChange={(e) => setFormData({ ...formData, levelTarget: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="">Select level</option>
                <option value="junior">Junior</option>
                <option value="mid">Mid-level</option>
                <option value="senior">Senior</option>
                <option value="staff">Staff</option>
                <option value="principal">Principal</option>
              </select>
            </div>

            {/* Drag and Drop Zone */}
            <div
              ref={dropZoneRef}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
                isDragging
                  ? 'border-purple-500 bg-purple-50'
                  : 'border-gray-300 hover:border-purple-400 hover:bg-gray-50'
              }`}
            >
              <div className="flex flex-col items-center gap-4">
                <span className="text-5xl">📄</span>
                <div>
                  <p className="text-lg font-semibold text-gray-700 mb-1">
                    Drag and drop your resume PDF here
                  </p>
                  <p className="text-sm text-gray-500">or click to browse</p>
                </div>
                {resumeFile && (
                  <p className="text-sm text-purple-600 font-medium">
                    Selected: {resumeFile.name}
                  </p>
                )}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">OR</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Paste Resume Text
              </label>
              <textarea
                rows={15}
                value={formData.resumeText}
                onPaste={handlePaste}
                onChange={(e) => {
                  setFormData({ ...formData, resumeText: e.target.value });
                  if (e.target.value) setResumeFile(null);
                }}
                placeholder="Paste your resume text here..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || (!resumeFile && !formData.resumeText)}
              className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-3 rounded-lg hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition font-semibold text-lg shadow-lg hover:shadow-xl"
            >
              {loading ? 'Processing & Searching Jobs...' : 'Upload & Find Jobs →'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
