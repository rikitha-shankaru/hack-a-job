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
  const [searchForm, setSearchForm] = useState({
    query: '',
    location: '',
    recency: 'w2',
  });

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await apiClient.post('/api/jobs/search', searchForm);
      setJobs(response.data.jobs);
    } catch (error) {
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
            className="mt-4 bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Search Jobs'}
          </button>
        </form>

        <div className="space-y-4">
          {jobs.map((job) => (
            <div key={job.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">
                    {job.title}
                  </h3>
                  <p className="text-gray-600">{job.company}</p>
                  <p className="text-sm text-gray-500">{job.location}</p>
                  {job.datePosted && (
                    <p className="text-sm text-gray-500">
                      Posted: {new Date(job.datePosted).toLocaleDateString()}
                    </p>
                  )}
                  {job.jd_keywords && job.jd_keywords.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {job.jd_keywords.map((keyword, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-indigo-100 text-indigo-700 text-xs rounded"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  )}
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

