export function JobCardSkeleton() {
  return (
    <div className="glass bg-white/90 backdrop-blur-xl rounded-2xl shadow-xl border border-purple-200/50 p-6 animate-pulse">
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1">
          <div className="h-7 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 rounded w-3/4 mb-3 animate-shimmer"></div>
          <div className="h-5 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 rounded w-1/2 mb-2 animate-shimmer"></div>
          <div className="h-4 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 rounded w-1/3 mb-2 animate-shimmer"></div>
          <div className="h-4 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 rounded w-1/4 mb-4 animate-shimmer"></div>
          <div className="flex gap-2 mb-2">
            <div className="h-6 bg-gradient-to-r from-purple-100 to-indigo-100 rounded-full w-20 animate-shimmer"></div>
            <div className="h-6 bg-gradient-to-r from-purple-100 to-indigo-100 rounded-full w-24 animate-shimmer"></div>
            <div className="h-6 bg-gradient-to-r from-purple-100 to-indigo-100 rounded-full w-16 animate-shimmer"></div>
          </div>
        </div>
        <div className="flex flex-col gap-2 min-w-[200px]">
          <div className="h-10 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 rounded-xl animate-shimmer"></div>
          <div className="h-10 bg-gradient-to-r from-purple-200 via-indigo-200 to-purple-200 rounded-xl animate-shimmer"></div>
        </div>
      </div>
    </div>
  );
}

export function ProgressBarSkeleton() {
  return (
    <div className="mt-6 space-y-3">
      <div className="flex items-center justify-between">
        <div className="h-4 bg-gray-200 rounded w-48 animate-pulse"></div>
        <div className="h-4 bg-gray-200 rounded w-12 animate-pulse"></div>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div className="bg-gradient-to-r from-purple-500 via-indigo-500 to-purple-500 h-3 rounded-full w-1/3 animate-pulse"></div>
      </div>
    </div>
  );
}

