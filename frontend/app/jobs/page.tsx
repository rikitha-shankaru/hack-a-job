'use client';

import { useState, useEffect } from 'react';
import apiClient from '@/lib/api';
import Link from 'next/link';

interface Job {
  id: string;
  company: string;
  title: string;
  location: string;
  datePosted: string;
  url: string;
  jd_keywords: string[];
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [searchForm, setSearchForm] = useState({
    query: '',
    location: '',
    recency: 'w2',
  });

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setProgress(0);
    setStatus('Starting search...');
    setJobs([]);
    
    try {
      // Simulate progress updates (since we can't get real-time updates from API)
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev < 90) {
            const newProgress = prev + Math.random() * 10;
            if (newProgress < 30) {
              setStatus('Searching job boards...');
            } else if (newProgress < 60) {
              setStatus('Parsing job postings...');
            } else if (newProgress < 90) {
              setStatus('Filtering and validating jobs...');
            }
            return Math.min(newProgress, 90);
          }
          return prev;
        });
      }, 500);
      
      const response = await apiClient.post('/api/jobs/search', searchForm);
      
      clearInterval(progressInterval);
      setProgress(100);
      setStatus(`Found ${response.data.jobs.length} jobs!`);
      
      setJobs(response.data.jobs);
      
      setTimeout(() => {
        setProgress(0);
        setStatus('');
      }, 2000);
    } catch (error: any) {
      setProgress(0);
      setStatus('Search failed: ' + (error.response?.data?.detail || 'Unknown error'));
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Job Search</h1>
        
        <form onSubmit={handleSearch} className="bg-white rounded-lg shadow p-6 mb-8">
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Query *
              </label>
              <input
                type="text"
                required
                value={searchForm.query}
                onChange={(e) => setSearchForm({ ...searchForm, query: e.target.value })}
                placeholder="e.g., software developer"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Location
              </label>
              <input
                type="text"
                value={searchForm.location}
                onChange={(e) => setSearchForm({ ...searchForm, location: e.target.value })}
                placeholder="e.g., Chicago"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Recency
              </label>
              <select
                value={searchForm.recency}
                onChange={(e) => setSearchForm({ ...searchForm, recency: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
              >
                <option value="d7">Last 7 days</option>
                <option value="w2">Last 2 weeks</option>
                <option value="m1">Last month</option>
              </select>
            </div>
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="mt-4 bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 font-semibold"
          >
            {loading ? 'Searching...' : 'Search Jobs'}
          </button>
          
          {loading && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">{status}</span>
                <span className="text-sm font-medium text-indigo-600">{Math.round(progress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}
        </form>

        {jobs.length > 0 && (
          <div className="mb-4 text-gray-600 text-lg">
            Found <span className="font-semibold text-indigo-600">{jobs.length}</span> job{jobs.length !== 1 ? 's' : ''}
          </div>
        )}

        <div className="space-y-4">
          {jobs.map((job) => (
            <div key={job.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {job.title}
                  </h3>
                  <div className="space-y-1">
                    <p className="text-gray-700 font-medium">{job.company || 'Company not specified'}</p>
                    {job.location && (
                      <p className="text-sm text-gray-600">
                        📍 <span className="font-medium">Location:</span> {job.location}
                      </p>
                    )}
                    {job.datePosted && (
                      <p className="text-sm text-gray-600">
                        📅 <span className="font-medium">Posted:</span> {new Date(job.datePosted).toLocaleDateString('en-US', { 
                          year: 'numeric', 
                          month: 'short', 
                          day: 'numeric' 
                        })}
                      </p>
                    )}
                    {(!job.datePosted && !job.location) && (
                      <p className="text-sm text-gray-400 italic">Details pending...</p>
                    )}
                  </div>
                  <div className="mt-3">
                    <p className="text-xs text-gray-500 mb-1 font-medium">Skills Required:</p>
                    {job.jd_keywords && job.jd_keywords.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {job.jd_keywords.map((keyword, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-indigo-100 text-indigo-700 text-xs rounded font-medium"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-400 italic">No skills specified</p>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    View Job
                  </a>
                  <Link
                    href={`/jobs/${job.id}/tailor`}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                  >
                    Tailor
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

