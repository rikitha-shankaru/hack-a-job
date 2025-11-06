'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api';

export default function UploadPage() {
  const router = useRouter();
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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setResumeFile(e.target.files[0]);
      // Clear text input when file is selected
      setFormData({ ...formData, resumeText: '' });
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
      if (formData.roleTarget) formDataToSend.append('roleTarget', formData.roleTarget);
      if (formData.levelTarget) formDataToSend.append('levelTarget', formData.levelTarget);
      
      if (resumeFile) {
        formDataToSend.append('resumeFile', resumeFile);
      } else if (formData.resumeText) {
        formDataToSend.append('resumeText', formData.resumeText);
      } else {
        throw new Error('Please upload a PDF file or paste resume text');
      }

      const response = await apiClient.post('/api/profile/ingest', formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      localStorage.setItem('userId', response.data.userId);
      router.push('/jobs');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload resume');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Upload Your Resume</h1>
        
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-8">
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
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
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
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Role
              </label>
              <input
                type="text"
                placeholder="e.g., Software Engineer"
                value={formData.roleTarget}
                onChange={(e) => setFormData({ ...formData, roleTarget: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Level
              </label>
              <select
                value={formData.levelTarget}
                onChange={(e) => setFormData({ ...formData, levelTarget: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              >
                <option value="">Select level</option>
                <option value="junior">Junior</option>
                <option value="mid">Mid-level</option>
                <option value="senior">Senior</option>
                <option value="staff">Staff</option>
                <option value="principal">Principal</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload PDF Resume (Recommended)
              </label>
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
              {resumeFile && (
                <p className="mt-2 text-sm text-gray-600">
                  Selected: {resumeFile.name}
                </p>
              )}
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
                onChange={(e) => {
                  setFormData({ ...formData, resumeText: e.target.value });
                  // Clear file when text is entered
                  if (e.target.value) setResumeFile(null);
                }}
                placeholder="Paste your resume text here..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
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
              className="w-full bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {loading ? 'Processing...' : 'Upload Resume'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

