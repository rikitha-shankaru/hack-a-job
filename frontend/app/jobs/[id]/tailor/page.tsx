'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api';

export default function TailorPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;
  const [tailorLoading, setTailorLoading] = useState(false);
  const [workflowLoading, setWorkflowLoading] = useState(false);
  const [assets, setAssets] = useState<any>(null);
  const [error, setError] = useState('');

  const handleTailor = async () => {
    setTailorLoading(true);
    setError('');
    
    const userId = localStorage.getItem('userId');
    if (!userId) {
      setError('Please upload your resume first');
      router.push('/upload');
      return;
    }

    try {
      const response = await apiClient.post('/api/tailor', {
        userId,
        jobId,
      });
      setAssets(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to tailor resume');
    } finally {
      setTailorLoading(false);
    }
  };

  const handleEmail = async () => {
    if (!assets) return;
    
    const userId = localStorage.getItem('userId');
    if (!userId) return;

    try {
      await apiClient.post('/api/email/send', {
        userId,
        jobId,
        assetsId: assets.assetsId,
      });
      alert('Email sent successfully!');
    } catch (err: any) {
      alert('Failed to send email: ' + (err.response?.data?.detail || 'Unknown error'));
    }
  };

  const handleCompleteWorkflow = async () => {
    setWorkflowLoading(true);
    setError('');
    
    const userId = localStorage.getItem('userId');
    if (!userId) {
      setError('Please upload your resume first');
      router.push('/upload');
      return;
    }

    try {
      const response = await apiClient.post('/api/tailor/complete', {
        userId,
        jobId,
      });
      
      if (response.data.verification_url) {
        alert(`Complete workflow finished! Check your email for verification link: ${response.data.verification_url}`);
        // Optionally redirect to verification page
        window.location.href = response.data.verification_url;
      } else {
        alert('Workflow completed! ' + (response.data.message || ''));
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to run complete workflow');
    } finally {
      setWorkflowLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">🤖</span>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
              AI Resume Tailoring
            </h1>
          </div>
          <p className="text-gray-600">Powered by advanced AI to optimize your resume for each job</p>
        </div>
        
        {!assets ? (
          <div className="bg-white rounded-xl shadow-xl p-8 border border-purple-100">
            <div className="flex items-start gap-4 mb-6">
              <div className="bg-purple-100 p-3 rounded-lg">
                <span className="text-2xl">✨</span>
              </div>
              <div>
                <h2 className="text-2xl font-semibold mb-2">AI-Powered Tailoring</h2>
                <p className="text-gray-600">
                  Our AI will analyze the job description and intelligently tailor your resume to maximize 
                  ATS compatibility and job match score while preserving all your original information.
                </p>
              </div>
            </div>
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                {error}
              </div>
            )}
            <div className="space-y-4">
              <button
                onClick={handleTailor}
                disabled={tailorLoading || workflowLoading}
                className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-4 rounded-lg hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 font-semibold text-lg transition-all shadow-lg hover:shadow-xl"
              >
                {tailorLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin">⚙️</span>
                    AI is analyzing and tailoring your resume...
                  </span>
                ) : (
                  '🤖 Generate AI-Tailored Resume'
                )}
              </button>
              
              <button
                onClick={handleCompleteWorkflow}
                disabled={tailorLoading || workflowLoading}
                className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white px-6 py-4 rounded-lg hover:from-green-700 hover:to-emerald-700 disabled:opacity-50 font-semibold text-lg transition-all shadow-lg hover:shadow-xl"
              >
                {workflowLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin">⚙️</span>
                    Running complete workflow...
                  </span>
                ) : (
                  '🚀 Run Complete Workflow (Tailor + Autofill + Email)'
                )}
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* AI Match Score */}
            {assets.diffs?.match_score && (
              <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl shadow-xl p-6 text-white">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-semibold mb-1">AI Job Match Score</h3>
                    <p className="text-purple-100">How well your resume matches this position</p>
                  </div>
                  <div className="text-right">
                    <div className="text-5xl font-bold">{assets.diffs.match_score.overall_score}</div>
                    <div className="text-purple-200 text-sm">out of 100</div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4 mt-4">
                  <div className="bg-white/20 rounded-lg p-3">
                    <div className="text-sm text-purple-100">Skills Match</div>
                    <div className="text-2xl font-bold">{assets.diffs.match_score.skills_match}%</div>
                  </div>
                  <div className="bg-white/20 rounded-lg p-3">
                    <div className="text-sm text-purple-100">Experience Match</div>
                    <div className="text-2xl font-bold">{assets.diffs.match_score.experience_match}%</div>
                  </div>
                  <div className="bg-white/20 rounded-lg p-3">
                    <div className="text-sm text-purple-100">Keyword Match</div>
                    <div className="text-2xl font-bold">{assets.diffs.match_score.keyword_match}%</div>
                  </div>
                </div>
                {assets.diffs.match_score.explanation && (
                  <div className="mt-4 bg-white/10 rounded-lg p-4">
                    <p className="text-sm text-purple-50">{assets.diffs.match_score.explanation}</p>
                  </div>
                )}
              </div>
            )}

            {/* AI Explanation */}
            {assets.diffs?.ai_explanation && (
              <div className="bg-white rounded-xl shadow-xl p-8 border border-purple-100">
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-3xl">🧠</span>
                  <h3 className="text-2xl font-semibold">AI Analysis</h3>
                </div>
                <div className="bg-gray-50 rounded-lg p-6 mb-4">
                  <p className="text-gray-700 leading-relaxed whitespace-pre-line">
                    {assets.diffs.ai_explanation}
                  </p>
                </div>
              </div>
            )}

            {/* AI Recommendations */}
            {assets.diffs?.ai_recommendations && assets.diffs.ai_recommendations.length > 0 && (
              <div className="bg-white rounded-xl shadow-xl p-8 border border-purple-100">
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-3xl">💡</span>
                  <h3 className="text-2xl font-semibold">AI Recommendations</h3>
                </div>
                <ul className="space-y-3">
                  {assets.diffs.ai_recommendations.map((rec: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-3 bg-blue-50 rounded-lg p-4">
                      <span className="text-blue-600 font-bold mt-1">✓</span>
                      <span className="text-gray-700">{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Changes Summary */}
            {assets.diffs && (
              <div className="bg-white rounded-xl shadow-xl p-8 border border-purple-100">
                <h3 className="text-xl font-semibold mb-4">Changes Summary</h3>
                <ul className="space-y-2">
                  {assets.diffs.bullets_changed?.length > 0 && (
                    <li className="flex items-center gap-2">
                      <span className="text-green-600">✓</span>
                      <span>{assets.diffs.bullets_changed.length} bullet points optimized</span>
                    </li>
                  )}
                  {assets.diffs.sections_reordered && (
                    <li className="flex items-center gap-2">
                      <span className="text-green-600">✓</span>
                      <span>Sections reordered for better relevance</span>
                    </li>
                  )}
                </ul>
              </div>
            )}

            {/* Download Actions */}
            <div className="bg-white rounded-xl shadow-xl p-8 border border-purple-100">
              <h2 className="text-2xl font-semibold mb-6">Your Tailored Assets</h2>
              <div className="grid md:grid-cols-2 gap-4">
                <a
                  href={assets.resumePdfUrl}
                  target="_blank"
                  className="flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl font-semibold"
                >
                  <span>📄</span>
                  Download Resume PDF
                </a>
                <a
                  href={assets.coverPdfUrl}
                  target="_blank"
                  className="flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-indigo-600 to-blue-600 text-white rounded-lg hover:from-indigo-700 hover:to-blue-700 transition-all shadow-lg hover:shadow-xl font-semibold"
                >
                  <span>✉️</span>
                  Download Cover Letter PDF
                </a>
              </div>
              <button
                onClick={handleEmail}
                className="w-full mt-4 px-6 py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 transition-all shadow-lg hover:shadow-xl font-semibold"
              >
                📧 Email Me Both Documents
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

