// Shimmer skeleton primitives used for loading states.
export function Skeleton({ className = '' }) {
  return <div className={`skeleton ${className}`} />
}

export function SkeletonStatCards({ count = 5 }) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="glass p-4">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="mt-3 h-7 w-16" />
          <Skeleton className="mt-2 h-3 w-24" />
        </div>
      ))}
    </div>
  )
}

export function SkeletonPanel({ className = 'h-[60vh]' }) {
  return (
    <div className="glass p-5">
      <Skeleton className="h-4 w-40" />
      <Skeleton className={`mt-4 w-full ${className}`} />
    </div>
  )
}
