import Link from 'next/link';

export default function Home() {
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
              Intelligent resume tailoring, automated cover letters, and smart job matching
            </p>
          </div>
          
          <div className="bg-white rounded-xl shadow-xl p-8 mb-8 border border-purple-100">
            <div className="flex items-start gap-4 mb-6">
              <div className="bg-gradient-to-br from-purple-500 to-indigo-500 p-4 rounded-lg text-white text-2xl">
                ✨
              </div>
              <div>
                <h2 className="text-2xl font-semibold mb-2">AI-Powered Features</h2>
                <ul className="space-y-2 text-gray-600">
                  <li className="flex items-center gap-2">
                    <span className="text-green-600">✓</span>
                    <span><strong>AI Resume Tailoring</strong> - Optimized for each job with ATS compatibility</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-600">✓</span>
                    <span><strong>Smart Job Matching</strong> - AI calculates match scores and provides insights</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-600">✓</span>
                    <span><strong>Intelligent Analysis</strong> - Get AI explanations and recommendations</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-600">✓</span>
                    <span><strong>Format Preservation</strong> - Maintains your original resume styling</span>
                  </li>
                </ul>
              </div>
            </div>
            <Link
              href="/upload"
              className="inline-block w-full text-center bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-4 rounded-lg hover:from-purple-700 hover:to-indigo-700 transition font-semibold text-lg shadow-lg hover:shadow-xl"
            >
              Get Started with AI ✨
            </Link>
          </div>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow-lg p-6 border border-purple-100">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">🔍</span>
                <h3 className="text-xl font-semibold">AI Job Search</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Find relevant job postings using advanced search with AI-powered filtering.
              </p>
              <Link
                href="/jobs"
                className="text-indigo-600 hover:underline font-semibold"
              >
                Search Jobs →
              </Link>
            </div>
            
            <div className="bg-white rounded-lg shadow-lg p-6 border border-purple-100">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-2xl">🎯</span>
                <h3 className="text-xl font-semibold">AI Resume Tailoring</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Get AI-optimized resumes and cover letters tailored to each job application.
              </p>
              <Link
                href="/jobs"
                className="text-indigo-600 hover:underline font-semibold"
              >
                Tailor Resume →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

