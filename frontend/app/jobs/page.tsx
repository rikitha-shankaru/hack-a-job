'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
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
  jd_text?: string;
}

export default function JobsPage() {
  const searchParams = useSearchParams();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [searchForm, setSearchForm] = useState({
    query: '',
    location: '',
    recency: 'w2',
  });

  // Auto-search on mount if coming from upload
  useEffect(() => {
    const autoSearch = searchParams.get('autoSearch');
    const query = searchParams.get('query') || '';
    const location = searchParams.get('location') || '';
    const recency = searchParams.get('recency') || 'w2';

    if (autoSearch === 'true' && query) {
      setSearchForm({
        query,
        location,
        recency,
      });
      handleAutoSearch({ query, location, recency });
    }
  }, [searchParams]);

  const performSearch = async (searchData: { query: string; location: string; recency: string }) => {
    setLoading(true);
    setProgress(0);
    setStatus('Starting search...');
    setJobs([]);
    
    try {
      // Modern animated progress updates
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev < 90) {
            const newProgress = prev + Math.random() * 8;
            if (newProgress < 25) {
              setStatus('🔍 Searching job boards...');
            } else if (newProgress < 50) {
              setStatus('📄 Parsing job postings...');
            } else if (newProgress < 75) {
              setStatus('✅ Filtering and validating jobs...');
            } else {
              setStatus('🎯 Finalizing results...');
            }
            return Math.min(newProgress, 90);
          }
          return prev;
        });
      }, 400);
      
      const response = await apiClient.post('/api/jobs/search', searchData);
      
      clearInterval(progressInterval);
      setProgress(100);
      setStatus(`✨ Found ${response.data.jobs.length} jobs!`);
      
      setJobs(response.data.jobs);
      localStorage.setItem('jobs', JSON.stringify(response.data.jobs));
      
      setTimeout(() => {
        setProgress(0);
        setStatus('');
      }, 2000);
    } catch (error: any) {
      setProgress(0);
      setStatus('❌ Search failed: ' + (error.response?.data?.detail || 'Unknown error'));
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAutoSearch = (searchData: { query: string; location: string; recency: string }) => {
    performSearch(searchData);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(searchForm);
  };

  const checkCoverLetterRequired = (jdText?: string): boolean => {
    if (!jdText) return false;
    const text = jdText.toLowerCase();
    return text.includes('cover letter') || text.includes('cover letter required') || 
           text.includes('please include a cover letter');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
          Job Search Results
        </h1>
        
        <form onSubmit={handleSearch} className="bg-white rounded-xl shadow-lg p-6 mb-8 border border-purple-100">
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
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Recency
              </label>
              <select
                value={searchForm.recency}
                onChange={(e) => setSearchForm({ ...searchForm, recency: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
            className="mt-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-3 rounded-lg hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 font-semibold shadow-lg hover:shadow-xl transition-all"
          >
            {loading ? 'Searching...' : '🔍 Search Jobs'}
          </button>
          
          {loading && (
            <div className="mt-6 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 animate-pulse">{status}</span>
                <span className="text-sm font-bold text-purple-600">{Math.round(progress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden shadow-inner">
                <div
                  className="bg-gradient-to-r from-purple-500 via-indigo-500 to-purple-500 h-3 rounded-full transition-all duration-300 ease-out relative overflow-hidden"
                  style={{ width: `${progress}%` }}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"></div>
                </div>
              </div>
            </div>
          )}
        </form>

        {jobs.length > 0 && (
          <div className="mb-6 text-gray-700 text-xl font-semibold">
            Found <span className="text-purple-600">{jobs.length}</span> job{jobs.length !== 1 ? 's' : ''}
          </div>
        )}

        <div className="space-y-4">
          {jobs.map((job, index) => {
            const needsCoverLetter = checkCoverLetterRequired(job.jd_text);
            return (
              <div 
                key={job.id} 
                className="bg-white rounded-xl shadow-lg p-6 border border-purple-100 hover:shadow-xl transition-all duration-300 animate-fade-in"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div className="flex justify-between items-start gap-4">
                  <div className="flex-1">
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">
                      {job.title}
                    </h3>
                    <div className="space-y-2">
                      <p className="text-lg text-gray-700 font-semibold">{job.company || 'Company not specified'}</p>
                      {job.location && (
                        <p className="text-sm text-gray-600 flex items-center gap-2">
                          <span>📍</span> <span className="font-medium">{job.location}</span>
                        </p>
                      )}
                      {job.datePosted && (
                        <p className="text-sm text-gray-600 flex items-center gap-2">
                          <span>📅</span> <span>{new Date(job.datePosted).toLocaleDateString('en-US', { 
                            year: 'numeric', 
                            month: 'short', 
                            day: 'numeric' 
                          })}</span>
                        </p>
                      )}
                    </div>
                    {job.jd_keywords && job.jd_keywords.length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {job.jd_keywords.slice(0, 8).map((keyword, idx) => (
                          <span
                            key={idx}
                            className="px-3 py-1 bg-gradient-to-r from-purple-100 to-indigo-100 text-purple-700 text-xs rounded-full font-medium border border-purple-200"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    )}
                    {needsCoverLetter && (
                      <div className="mt-3 inline-flex items-center gap-2 px-3 py-1 bg-yellow-50 border border-yellow-200 rounded-full">
                        <span className="text-yellow-600">📝</span>
                        <span className="text-xs font-medium text-yellow-700">Cover letter required</span>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col gap-2 min-w-[200px]">
                    <a
                      href={job.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2 border-2 border-purple-300 text-purple-700 rounded-lg hover:bg-purple-50 font-semibold text-center transition-all"
                    >
                      View Job Details
                    </a>
                    <Link
                      href={`/jobs/${job.id}/tailor`}
                      className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 font-semibold text-center shadow-lg hover:shadow-xl transition-all"
                    >
                      {needsCoverLetter ? '✨ Tailor Resume & Cover Letter' : '✨ Tailor Resume'}
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {!loading && jobs.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">No jobs found. Try adjusting your search criteria.</p>
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fade-in {
          animation: fade-in 0.5s ease-out forwards;
          opacity: 0;
        }
        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
    </div>
  );
}
