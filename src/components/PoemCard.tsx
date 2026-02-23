import { forwardRef } from 'react'
import type { Poem } from '../types/poem'
import PoemText from './PoemText'
import { formatReadingTime } from '../lib/poem-utils'

interface Props {
  poem: Poem
  style?: React.CSSProperties
  className?: string
}

const PoemCard = forwardRef<HTMLDivElement, Props>(({ poem, style, className = '' }, ref) => {
  return (
    <div
      ref={ref}
      className={`absolute inset-x-4 top-4 bottom-24 bg-cream rounded-2xl shadow-lg overflow-hidden flex flex-col ${className}`}
      style={style}
    >
      {/* Scroll container */}
      <div
        className="flex-1 overflow-y-auto overscroll-contain px-6 py-8"
        style={{ touchAction: 'pan-y', WebkitOverflowScrolling: 'touch' }}
      >
        {/* Header */}
        <div className="mb-6">
          <h1 className="font-serif font-semibold text-[1.5rem] leading-tight text-ink m-0">
            {poem.title}
          </h1>
          <p className="font-serif italic text-[1rem] text-muted mt-1 mb-0">
            {poem.author}
          </p>
          <p className="font-sans text-[0.75rem] text-faint mt-1">
            {formatReadingTime(poem.reading_time_minutes)}
            {poem.linecount > 0 && ` · ${poem.linecount} lines`}
          </p>
        </div>

        {/* Poem body */}
        <PoemText lines={poem.lines} prose={poem.prose} />
      </div>
    </div>
  )
})

PoemCard.displayName = 'PoemCard'
export default PoemCard
