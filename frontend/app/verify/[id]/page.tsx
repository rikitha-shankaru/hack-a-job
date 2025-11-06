'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api';

export default function VerifyPage() {
  const params = useParams();
  const runId = params.id as string;
  const [loading, setLoading] = useState(true);
  const [run, setRun] = useState<any>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    // Fetch autofill run details
    // In production, this would be a secure endpoint
    // For now, we'll show a placeholder
    setLoading(false);
  }, [runId]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-xl shadow-xl p-8 border border-purple-100">
          <div className="text-center mb-8">
            <span className="text-5xl mb-4 block">✨</span>
            <h1 className="text-3xl font-bold mb-2">Application Ready for Review</h1>
            <p className="text-gray-600">
              Your AI-powered application has been pre-filled and is ready for your review
            </p>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin text-4xl mb-4">⚙️</div>
              <p>Loading application details...</p>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-2 text-green-800">
                  ✓ Application Pre-filled Successfully
                </h2>
                <p className="text-green-700">
                  All fields have been filled using AI. Please review the information below before submitting.
                </p>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">What was filled:</h3>
                <ul className="space-y-2 text-gray-700">
                  <li className="flex items-center gap-2">
                    <span className="text-green-600">✓</span>
                    <span>Personal information (name, email, phone)</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-600">✓</span>
                    <span>Resume and cover letter uploaded</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-600">✓</span>
                    <span>Application questions answered by AI</span>
                  </li>
                </ul>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-2">⚠️ Important</h3>
                <p className="text-gray-700">
                  Please review all filled information carefully. The AI has done its best to answer questions
                  based on your resume, but you should verify everything is accurate before submitting.
                </p>
              </div>

              <div className="flex gap-4">
                <a
                  href={`/autofill/${runId}`}
                  className="flex-1 text-center px-6 py-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition font-semibold"
                >
                  Review Full Details
                </a>
                <button
                  className="flex-1 px-6 py-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700 transition font-semibold"
                >
                  Ready to Submit ✓
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

