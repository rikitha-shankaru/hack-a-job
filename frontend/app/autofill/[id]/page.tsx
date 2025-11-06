'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api';

export default function AutofillPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;
  const [loading, setLoading] = useState(false);
  const [run, setRun] = useState<any>(null);
  const [error, setError] = useState('');

  const handleRun = async () => {
    setLoading(true);
    setError('');
    
    const userId = localStorage.getItem('userId');
    if (!userId) {
      setError('Please upload your resume first');
      router.push('/upload');
      return;
    }

    try {
      const response = await apiClient.post('/api/autofill/run', {
        userId,
        jobId,
      });
      setRun(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to run autofill');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (submit: boolean) => {
    if (!run) return;

    try {
      await apiClient.post('/api/autofill/approve', {
        runId: run.runId,
        submit,
      });
      alert(submit ? 'Application submitted!' : 'Form approved');
    } catch (err: any) {
      alert('Failed: ' + (err.response?.data?.detail || 'Unknown error'));
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Autofill Application Form</h1>
        
        {!run ? (
          <div className="bg-white rounded-lg shadow p-8">
            <p className="mb-6">Pre-fill the application form for this job.</p>
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                {error}
              </div>
            )}
            <button
              onClick={handleRun}
              disabled={loading}
              className="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? 'Processing...' : 'Run Autofill'}
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-8">
              <h2 className="text-2xl font-semibold mb-4">Form Preview</h2>
              <p className="mb-4">Status: {run.status}</p>
              
              {run.confidence && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-2">Confidence Scores:</h3>
                  <ul className="space-y-2">
                    {Object.entries(run.confidence).map(([field, score]: [string, any]) => (
                      <li key={field} className="flex justify-between">
                        <span>{field}:</span>
                        <span className={score < 0.85 ? 'text-yellow-600' : 'text-green-600'}>
                          {(score * 100).toFixed(0)}%
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {run.screenshots && run.screenshots.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-2">Screenshots:</h3>
                  <div className="space-y-4">
                    {run.screenshots.map((screenshot: string, idx: number) => (
                      <img
                        key={idx}
                        src={`data:image/png;base64,${screenshot}`}
                        alt={`Screenshot ${idx + 1}`}
                        className="border border-gray-300 rounded"
                      />
                    ))}
                  </div>
                </div>
              )}
              
              <div className="flex gap-4">
                <button
                  onClick={() => handleApprove(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                >
                  Approve Only
                </button>
                <button
                  onClick={() => handleApprove(true)}
                  disabled={run.status === 'error'}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  Approve & Submit
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

