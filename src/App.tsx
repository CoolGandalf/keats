import { useState, useCallback } from 'react'
import SwipeDeck from './components/SwipeDeck'
import LikedList from './components/LikedList'
import EmptyState from './components/EmptyState'
import { usePoems } from './hooks/usePoems'
import { useLikes } from './hooks/useLikes'

type View = 'swipe' | 'likes'

export default function App() {
  const [view, setView] = useState<View>('swipe')
  const { current, next, advance, loading, isEmpty, resetSeen, seenCount, totalCount } = usePoems()
  const { likes, likePoem, unlikePoem } = useLikes()

  const handleLike = useCallback(
    (poem: Parameters<typeof likePoem>[0]) => {
      likePoem(poem)
      advance()
    },
    [likePoem, advance],
  )

  const handlePass = useCallback(() => {
    advance()
  }, [advance])

  return (
    <div className="h-full bg-parchment relative">
      {view === 'swipe' ? (
        <>
          {isEmpty ? (
            <EmptyState
              seenCount={seenCount}
              totalCount={totalCount}
              onReset={resetSeen}
            />
          ) : (
            <SwipeDeck
              current={current}
              next={next}
              onLike={handleLike}
              onPass={handlePass}
              loading={loading}
            />
          )}
          {/* Likes button */}
          <button
            onClick={() => setView('likes')}
            className="absolute top-4 right-4 z-30 w-10 h-10 rounded-full bg-cream shadow-md flex items-center justify-center font-sans text-sm active:scale-90 transition-transform"
            aria-label="View liked poems"
          >
            <span className="text-like text-lg">♥</span>
            {likes.length > 0 && (
              <span className="absolute -top-1 -right-1 bg-like text-cream text-[0.65rem] font-semibold rounded-full w-5 h-5 flex items-center justify-center">
                {likes.length > 99 ? '99+' : likes.length}
              </span>
            )}
          </button>
        </>
      ) : (
        <LikedList
          likes={likes}
          onUnlike={unlikePoem}
          onBack={() => setView('swipe')}
        />
      )}
    </div>
  )
}
