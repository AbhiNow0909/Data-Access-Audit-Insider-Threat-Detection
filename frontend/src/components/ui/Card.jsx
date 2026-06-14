// Glassmorphism surface with optional hover lift and entrance animation.
export default function Card({ children, className = '', hover = false, delay, ...rest }) {
  const style = delay != null ? { animationDelay: `${delay}ms` } : undefined
  return (
    <div
      className={`glass ${hover ? 'glass-hover' : ''} ${delay != null ? 'animate-fade-up' : ''} ${className}`}
      style={style}
      {...rest}
    >
      {children}
    </div>
  )
}

export function CardHeader({ title, subtitle, icon, right }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <div className="flex items-center gap-2.5">
        {icon && (
          <span className="grid h-8 w-8 place-items-center rounded-lg border border-white/10 bg-white/5 text-indigo-300">
            {icon}
          </span>
        )}
        <div>
          <h3 className="text-sm font-semibold text-slate-100">{title}</h3>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
        </div>
      </div>
      {right}
    </div>
  )
}
