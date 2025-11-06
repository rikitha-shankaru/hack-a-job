'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    targetRole: '',
    location: '',
    recency: 'w2', // Default: last 2 weeks
  });

  const handleStart = () => {
    // Store form data in localStorage to use in upload page
    localStorage.setItem('targetRole', formData.targetRole);
    localStorage.setItem('location', formData.location);
    localStorage.setItem('recency', formData.recency);
    router.push('/upload');
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
            <p className="text-lg text-gray-600">
              Tell me about your job search, and I'll help you find and apply to the perfect roles
            </p>
          </div>
          
          <div className="bg-white rounded-xl shadow-xl p-8 mb-8 border border-purple-100">
            <div className="flex items-start gap-4 mb-6">
              <div className="bg-gradient-to-br from-purple-500 to-indigo-500 p-4 rounded-lg text-white text-2xl">
                🤖
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-semibold mb-4">Let's Get Started!</h2>
                <p className="text-gray-600 mb-6">
                  I'll help you find jobs and tailor your resume. First, tell me what you're looking for:
                </p>
                
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
                      placeholder="e.g., Software Engineer, Data Scientist, Product Manager"
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
                    <p className="mt-1 text-xs text-gray-500">Leave empty to search all locations</p>
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
                </div>
              </div>
            </div>
            
            <button
              onClick={handleStart}
              disabled={!formData.targetRole}
              className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-4 rounded-lg hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition font-semibold text-lg shadow-lg hover:shadow-xl"
            >
              Next: Upload Your Resume →
            </button>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow-lg p-6 border border-purple-100">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">📄</span>
                <h3 className="text-xl font-semibold">1. Upload Resume</h3>
              </div>
              <p className="text-gray-600 text-sm">
                Upload your resume (PDF, drag-and-drop, or paste text)
              </p>
            </div>
            
            <div className="bg-white rounded-lg shadow-lg p-6 border border-purple-100">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">🔍</span>
                <h3 className="text-xl font-semibold">2. Find Jobs</h3>
              </div>
              <p className="text-gray-600 text-sm">
                AI automatically searches and lists matching jobs
              </p>
            </div>
            
            <div className="bg-white rounded-lg shadow-lg p-6 border border-purple-100">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">✨</span>
                <h3 className="text-xl font-semibold">3. Tailor & Apply</h3>
              </div>
              <p className="text-gray-600 text-sm">
                Get tailored resume/cover letter and apply manually or with AI autofill
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

