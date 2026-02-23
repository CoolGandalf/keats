import { useState } from 'react'
import type { Poem } from '../types/poem'
import PoemCard from './PoemCard'

interface LikedPoem extends Poem {
  likedAt: number
}

interface Props {
  likes: LikedPoem[]
  onUnlike: (id: string) => void
  onBack: () => void
}

export default function LikedList({ likes, onUnlike, onBack }: Props) {
  const [reading, setReading] = useState<Poem | null>(null)

  if (reading) {
    return (
      <div className="h-full relative">
        <PoemCard poem={reading} className="!bottom-16" />
        <div className="absolute bottom-4 left-0 right-0 z-20 flex justify-center gap-4">
          <button
            onClick={() => {
              onUnlike(reading.id)
              setReading(null)
            }}
            className="px-5 py-2.5 rounded-full bg-cream shadow-md font-sans text-sm text-pass border border-pass/20 active:scale-95 transition-transform"
          >
            Remove
          </button>
          <button
            onClick={() => setReading(null)}
            className="px-5 py-2.5 rounded-full bg-cream shadow-md font-sans text-sm text-ink active:scale-95 transition-transform"
          >
            Back to list
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-ink/5">
        <button
          onClick={onBack}
          className="font-sans text-sm text-muted active:text-ink transition-colors"
        >
          ← Swipe
        </button>
        <h2 className="font-serif font-semibold text-lg text-ink">
          Liked ({likes.length})
        </h2>
        <div className="w-12" /> {/* spacer */}
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {likes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full px-8 text-center">
            <p className="font-serif text-xl text-muted">No liked poems yet</p>
            <p className="font-sans text-sm text-faint mt-2">
              Swipe right on poems you love
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-ink/5">
            {likes.map(poem => (
              <li key={poem.id}>
                <button
                  onClick={() => setReading(poem)}
                  className="w-full text-left px-4 py-3 active:bg-ink/5 transition-colors"
                >
                  <p className="font-serif font-semibold text-ink text-[1rem] leading-snug">
                    {poem.title}
                  </p>
                  <p className="font-serif italic text-muted text-sm">
                    {poem.author}
                  </p>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
