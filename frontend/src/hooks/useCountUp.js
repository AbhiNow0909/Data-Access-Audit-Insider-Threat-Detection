import { useEffect, useRef, useState } from 'react'

// Smoothly animates a number from 0 to `target` (ease-out cubic).
// Respects prefers-reduced-motion by snapping to the value.
export function useCountUp(target, duration = 900) {
  const [value, setValue] = useState(0)
  const raf = useRef(0)

  useEffect(() => {
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (reduce || !Number.isFinite(target)) {
      setValue(target || 0)
      return
    }
    const start = performance.now()
    const tick = (now) => {
      const p = Math.min(1, (now - start) / duration)
      const eased = 1 - Math.pow(1 - p, 3)
      setValue(target * eased)
      if (p < 1) raf.current = requestAnimationFrame(tick)
    }
    raf.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf.current)
  }, [target, duration])

  return value
}
