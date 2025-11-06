'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api';
import Link from 'next/link';
import { JobCardSkeleton, ProgressBarSkeleton } from '@/components/SkeletonLoader';
import ParticleBackground from '@/components/ParticleBackground';

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

interface TailoredAssets {
  assetsId: string;
  originalResumePdfUrl?: string;
  resumePdfUrl: string;
  coverPdfUrl: string;
  diffs?: any;
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
  const [tailoringJobId, setTailoringJobId] = useState<string | null>(null);
  const [tailoredAssets, setTailoredAssets] = useState<Record<string, TailoredAssets>>({});
  const [activeTab, setActiveTab] = useState<Record<string, 'original' | 'tailored' | 'cover'>>({});
  const [error, setError] = useState<Record<string, string>>({});

  // Restore jobs and search form on mount (only once)
  useEffect(() => {
    // Check if we already have jobs in localStorage (from previous search)
    const savedJobs = localStorage.getItem('jobs');
    const savedSearch = localStorage.getItem('lastSearch');
    
    if (savedJobs) {
      try {
        const parsedJobs = JSON.parse(savedJobs);
        if (parsedJobs && parsedJobs.length > 0) {
          // Restore jobs from localStorage instead of searching again
          setJobs(parsedJobs);
          
          // Restore search form from saved search or URL params
          if (savedSearch) {
            try {
              const parsedSearch = JSON.parse(savedSearch);
              setSearchForm({
                query: parsedSearch.query || '',
                location: parsedSearch.location || '',
                recency: parsedSearch.recency || 'w2',
              });
            } catch (e) {
              // Fallback to URL params
              const query = searchParams.get('query') || '';
              const location = searchParams.get('location') || '';
              const recency = searchParams.get('recency') || 'w2';
              setSearchForm({ query, location, recency });
            }
          } else {
            // Use URL params if no saved search
            const query = searchParams.get('query') || '';
            const location = searchParams.get('location') || '';
            const recency = searchParams.get('recency') || 'w2';
            setSearchForm({ query, location, recency });
          }
          
          return; // Don't trigger new search if we have saved jobs
        }
      } catch (e) {
        console.error('Failed to parse saved jobs:', e);
      }
    }

    // Only auto-search if we don't have saved jobs
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
  }, []); // Empty dependency array - only run once on mount

  const performSearch = useCallback(async (searchData: { query: string; location: string; recency: string }) => {
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
      // Store jobs in localStorage for persistence across navigation
      localStorage.setItem('jobs', JSON.stringify(response.data.jobs));
      // Also store search params for restoring form
      localStorage.setItem('lastSearch', JSON.stringify(searchData));
      
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

  const handleAutoSearch = useCallback((searchData: { query: string; location: string; recency: string }) => {
    performSearch(searchData);
  }, [performSearch]);

  const handleSearch = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(searchForm);
  }, [searchForm, performSearch]);

  const handleTailor = useCallback(async (jobId: string) => {
    setTailoringJobId(jobId);
    setError(prev => ({ ...prev, [jobId]: '' }));
    
    const userId = localStorage.getItem('userId');
    if (!userId) {
      setError(prev => ({ ...prev, [jobId]: 'Please upload your resume first' }));
      setTailoringJobId(null);
      return;
    }

    try {
      const response = await apiClient.post('/api/tailor', {
        userId,
        jobId,
      });
      setTailoredAssets(prev => ({ ...prev, [jobId]: response.data }));
      setActiveTab(prev => ({ ...prev, [jobId]: 'tailored' }));
    } catch (err: any) {
      setError(prev => ({ ...prev, [jobId]: err.response?.data?.detail || 'Failed to tailor resume' }));
    } finally {
      setTailoringJobId(null);
    }
  }, []);

  const checkCoverLetterRequired = useCallback((jdText?: string): boolean => {
    if (!jdText) return false;
    const text = jdText.toLowerCase();
    return text.includes('cover letter') || text.includes('cover letter required') || 
           text.includes('please include a cover letter');
  }, []);

  // Memoize jobs list to prevent unnecessary re-renders
  const memoizedJobs = useMemo(() => jobs, [jobs]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100 py-12 px-4 relative overflow-hidden">
      <ParticleBackground />
      <div className="max-w-6xl mx-auto relative z-10">
        <h1 className="text-5xl font-bold mb-8 gradient-text animate-fade-in-up">
          Job Search Results
        </h1>
        
        <form onSubmit={handleSearch} className="glass bg-white/90 backdrop-blur-xl rounded-2xl shadow-2xl p-6 mb-8 border border-purple-200/50 animate-fade-in-up hover-lift">
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
            className="mt-4 bg-gradient-to-r from-purple-600 via-indigo-600 to-purple-600 text-white px-8 py-4 rounded-xl hover:from-purple-700 hover:via-indigo-700 hover:to-purple-700 disabled:opacity-50 font-semibold shadow-lg hover:shadow-2xl btn-magic animate-gradient relative overflow-hidden transform hover:scale-105 transition-all duration-300"
          >
            {loading ? (
              <span className="relative z-10 flex items-center justify-center gap-2">
                <div className="spinner w-5 h-5 border-2"></div>
                Searching...
              </span>
            ) : (
              <span className="relative z-10 flex items-center justify-center gap-2">
                🔍 Search Jobs
              </span>
            )}
          </button>
          
          {loading && (
            <ProgressBarSkeleton />
          )}
          {loading && memoizedJobs.length > 0 && (
            <div className="mt-6 space-y-3 animate-fade-in-up">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 animate-pulse">{status}</span>
                <span className="text-sm font-bold gradient-text">{Math.round(progress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden shadow-inner">
                <div
                  className="bg-gradient-to-r from-purple-500 via-indigo-500 to-purple-500 h-4 rounded-full transition-all duration-300 ease-out relative overflow-hidden animate-gradient"
                  style={{ width: `${progress}%` }}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"></div>
                </div>
              </div>
            </div>
          )}
        </form>

        {memoizedJobs.length > 0 && (
          <div className="mb-6 text-gray-700 text-xl font-semibold animate-fade-in-up">
            Found <span className="gradient-text font-bold">{memoizedJobs.length}</span> job{memoizedJobs.length !== 1 ? 's' : ''}
          </div>
        )}

        {/* Show skeleton loaders while loading */}
        {loading && memoizedJobs.length === 0 && (
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <JobCardSkeleton key={i} />
            ))}
          </div>
        )}

        <div className="space-y-4">
          {memoizedJobs.map((job, index) => {
            const needsCoverLetter = checkCoverLetterRequired(job.jd_text);
            const isTailoring = tailoringJobId === job.id;
            const assets = tailoredAssets[job.id];
            const tab = activeTab[job.id] || 'tailored';
            
            return (
              <div 
                key={job.id} 
                className="glass bg-white/90 backdrop-blur-xl rounded-2xl shadow-xl border border-purple-200/50 hover:shadow-2xl transition-all duration-300 animate-fade-in-up hover-lift card-3d"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                {/* Job Card */}
                <div className="p-6">
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
                              className="px-3 py-1 bg-gradient-to-r from-purple-100 to-indigo-100 text-purple-700 text-xs rounded-full font-medium border border-purple-200 hover:scale-110 hover:shadow-md transition-all cursor-default animate-scale-in"
                              style={{ animationDelay: `${idx * 30}ms` }}
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
                        className="px-4 py-2 border-2 border-purple-300 text-purple-700 rounded-xl hover:bg-gradient-to-r hover:from-purple-50 hover:to-indigo-50 font-semibold text-center transition-all hover-lift hover-glow"
                      >
                        View Job Details
                      </a>
                      <button
                        onClick={() => handleTailor(job.id)}
                        disabled={isTailoring || !!assets}
                        className="px-6 py-3 bg-gradient-to-r from-purple-600 via-indigo-600 to-purple-600 text-white rounded-xl hover:from-purple-700 hover:via-indigo-700 hover:to-purple-700 disabled:opacity-50 font-semibold text-center shadow-lg hover:shadow-2xl btn-magic animate-gradient relative overflow-hidden transform hover:scale-105 transition-all duration-300"
                      >
                        {isTailoring ? (
                          <span className="relative z-10 flex items-center justify-center gap-2">
                            <div className="spinner w-4 h-4 border-2"></div>
                            Tailoring...
                          </span>
                        ) : assets ? (
                          <span className="relative z-10">✅ Tailored</span>
                        ) : (
                          <span className="relative z-10 flex items-center justify-center gap-2">
                            ✨ {needsCoverLetter ? 'Tailor Resume & Cover Letter' : 'Tailor Resume'}
                          </span>
                        )}
                      </button>
                    </div>
                  </div>

                  {error[job.id] && (
                    <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                      {error[job.id]}
                    </div>
                  )}
                </div>

                {/* Tailored Assets Preview */}
                {assets && (
                  <div className="border-t border-gray-200 p-6 bg-gray-50">
                    <h4 className="text-lg font-semibold mb-4">Tailored Documents</h4>
                    
                    {/* Tabs */}
                    <div className="flex gap-2 mb-4 border-b border-gray-200">
                      {assets.originalResumePdfUrl && (
                        <button
                          onClick={() => setActiveTab({ ...activeTab, [job.id]: 'original' })}
                          className={`px-4 py-2 font-medium transition-colors ${
                            tab === 'original'
                              ? 'border-b-2 border-purple-600 text-purple-600'
                              : 'text-gray-600 hover:text-gray-900'
                          }`}
                        >
                          📄 Original Resume
                        </button>
                      )}
                      <button
                        onClick={() => setActiveTab({ ...activeTab, [job.id]: 'tailored' })}
                        className={`px-4 py-2 font-medium transition-colors ${
                          tab === 'tailored'
                            ? 'border-b-2 border-purple-600 text-purple-600'
                            : 'text-gray-600 hover:text-gray-900'
                        }`}
                      >
                        ✨ Tailored Resume
                      </button>
                      <button
                        onClick={() => setActiveTab({ ...activeTab, [job.id]: 'cover' })}
                        className={`px-4 py-2 font-medium transition-colors ${
                          tab === 'cover'
                            ? 'border-b-2 border-purple-600 text-purple-600'
                            : 'text-gray-600 hover:text-gray-900'
                        }`}
                      >
                        ✉️ Cover Letter
                      </button>
                    </div>

                    {/* PDF Preview */}
                    <div className="border border-gray-200 rounded-lg overflow-hidden bg-gray-50 mb-4" style={{ height: '600px' }}>
                      {tab === 'original' && assets.originalResumePdfUrl && (
                        <iframe
                          src={`${assets.originalResumePdfUrl}#toolbar=1`}
                          className="w-full h-full"
                          title="Original Resume Preview"
                        />
                      )}
                      {tab === 'tailored' && assets.resumePdfUrl && (
                        <iframe
                          src={`${assets.resumePdfUrl}#toolbar=1`}
                          className="w-full h-full"
                          title="Tailored Resume Preview"
                        />
                      )}
                      {tab === 'cover' && assets.coverPdfUrl && (
                        <iframe
                          src={`${assets.coverPdfUrl}#toolbar=1`}
                          className="w-full h-full"
                          title="Cover Letter Preview"
                        />
                      )}
                    </div>

                    {/* Download Actions */}
                    <div className="grid md:grid-cols-3 gap-4">
                      {assets.originalResumePdfUrl && (
                        <a
                          href={assets.originalResumePdfUrl}
                          download
                          target="_blank"
                          className="flex items-center justify-center gap-2 px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-all font-semibold"
                        >
                          <span>📄</span>
                          Download Original
                        </a>
                      )}
                      <a
                        href={assets.resumePdfUrl}
                        download
                        target="_blank"
                        className="flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all font-semibold"
                      >
                        <span>✨</span>
                        Download Tailored Resume
                      </a>
                      <a
                        href={assets.coverPdfUrl}
                        download
                        target="_blank"
                        className="flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-lg hover:from-indigo-700 hover:to-blue-700 transition-all font-semibold"
                      >
                        <span>✉️</span>
                        Download Cover Letter
                      </a>
                    </div>

                    {/* Apply Options */}
                    <div className="mt-6 grid md:grid-cols-2 gap-4">
                      <a
                        href={job.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-center gap-2 px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition font-medium"
                      >
                        <span>✋</span>
                        Manual Application →
                      </a>
                      <Link
                        href={`/jobs/${job.id}/tailor`}
                        className="flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition font-medium"
                      >
                        <span>🤖</span>
                        AI Autofill →
                      </Link>
                    </div>
                  </div>
                )}
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
