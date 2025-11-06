'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api';

export default function Home() {
  const router = useRouter();
  const [step, setStep] = useState<'job-info' | 'resume'>('job-info');
  const [formData, setFormData] = useState({
    targetRole: '',
    location: '',
    recency: 'w2',
    email: '',
    name: '',
    levelTarget: '',
  });
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeText, setResumeText] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleJobInfoSubmit = () => {
    if (!formData.targetRole) {
      setError('Please enter a target job role');
      return;
    }
    setStep('resume');
    setError('');
  };

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
      setResumeText('');
    }
  };

  const handleResumeSubmit = async () => {
    if (!formData.email) {
      setError('Please enter your email');
      return;
    }

    // If no resume provided, AI will generate one
    if (!resumeFile && !resumeText) {
      // Continue without resume - AI will generate
    }

    setLoading(true);
    setError('');

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('email', formData.email);
      if (formData.name) formDataToSend.append('name', formData.name);
      formDataToSend.append('roleTarget', formData.targetRole);
      if (formData.levelTarget) formDataToSend.append('levelTarget', formData.levelTarget);
      
      if (resumeFile) {
        formDataToSend.append('resumeFile', resumeFile);
      } else if (resumeText) {
        formDataToSend.append('resumeText', resumeText);
      }
      // If neither provided, backend will generate resume

      const response = await apiClient.post('/api/profile/ingest', formDataToSend, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      localStorage.setItem('userId', response.data.userId);
      localStorage.setItem('targetRole', formData.targetRole);
      localStorage.setItem('location', formData.location);
      localStorage.setItem('recency', formData.recency);

      // Redirect to jobs page with auto-search
      router.push(`/jobs?autoSearch=true&query=${encodeURIComponent(formData.targetRole)}&location=${encodeURIComponent(formData.location)}&recency=${formData.recency}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process resume');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <div className="flex items-center justify-center gap-3 mb-4">
              <span className="text-5xl">🤖</span>
              <h1 className="text-6xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
                Hack-A-Job
              </h1>
            </div>
            <p className="text-xl text-gray-700 mb-2">
              <strong>AI-Powered</strong> Job Application Assistant
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-xl p-8 border border-purple-100">
            {step === 'job-info' ? (
              <>
                <h2 className="text-2xl font-semibold mb-6">Tell us about your job search</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Target Job Role *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.targetRole}
                      onChange={(e) => setFormData({ ...formData, targetRole: e.target.value })}
                      placeholder="e.g., Software Engineer, Data Scientist"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Location (Optional)
                    </label>
                    <input
                      type="text"
                      value={formData.location}
                      onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                      placeholder="e.g., New York, Remote, San Francisco"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Job Posting Recency
                    </label>
                    <select
                      value={formData.recency}
                      onChange={(e) => setFormData({ ...formData, recency: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    >
                      <option value="d7">Last 7 days</option>
                      <option value="w2">Last 2 weeks</option>
                      <option value="m1">Last month</option>
                    </select>
                  </div>

                  {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                      {error}
                    </div>
                  )}

                  <button
                    onClick={handleJobInfoSubmit}
                    disabled={!formData.targetRole}
                    className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-4 rounded-lg hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition font-semibold text-lg shadow-lg hover:shadow-xl"
                  >
                    Continue →
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="mb-6">
                  <button
                    onClick={() => setStep('job-info')}
                    className="text-purple-600 hover:text-purple-700 mb-4 flex items-center gap-2"
                  >
                    ← Back
                  </button>
                  <h2 className="text-2xl font-semibold mb-2">Upload Your Resume</h2>
                  <p className="text-gray-600">
                    Looking for: <strong>{formData.targetRole}</strong>
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Don't have a resume? We'll create one for you based on your job profile!
                  </p>
                </div>

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
                      Name (Optional)
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
                      Experience Level (Optional)
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
                    </select>
                  </div>

                  {/* Drag and Drop Zone */}
                  <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => document.getElementById('file-input')?.click()}
                    className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all ${
                      isDragging
                        ? 'border-purple-500 bg-purple-50 scale-105'
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
                      id="file-input"
                      type="file"
                      accept=".pdf"
                      onChange={(e) => {
                        if (e.target.files?.[0]) {
                          setResumeFile(e.target.files[0]);
                          setResumeText('');
                        }
                      }}
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
                      rows={8}
                      value={resumeText}
                      onChange={(e) => {
                        setResumeText(e.target.value);
                        if (e.target.value) setResumeFile(null);
                      }}
                      placeholder="Paste your resume text here..."
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>

                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-sm text-blue-800">
                      <strong>💡 No resume?</strong> Don't worry! We'll create a professional resume for you based on your job profile and experience level.
                    </p>
                  </div>

                  {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                      {error}
                    </div>
                  )}

                  <button
                    onClick={handleResumeSubmit}
                    disabled={loading || !formData.email}
                    className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-3 rounded-lg hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition font-semibold text-lg shadow-lg hover:shadow-xl"
                  >
                    {loading ? 'Processing...' : 'Search Jobs →'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
