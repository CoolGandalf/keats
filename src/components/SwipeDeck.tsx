import { useCallback, useEffect } from 'react'
import { motion, useMotionValue, useTransform, animate } from 'framer-motion'
import type { Poem } from '../types/poem'
import PoemCard from './PoemCard'
import SwipeIndicator from './SwipeIndicator'
import { useSwipe } from '../hooks/useSwipe'

interface Props {
  current: Poem | null
  next: Poem | null
  onLike: (poem: Poem) => void
  onPass: () => void
  loading: boolean
}

const SWIPE_THRESHOLD = 100
const SWIPE_VELOCITY = 500

export default function SwipeDeck({ current, next, onLike, onPass, loading }: Props) {
  const x = useMotionValue(0)
  const rotate = useTransform(x, [-300, 0, 300], [-15, 0, 15])
  const nextScale = useTransform(x, [-300, 0, 300], [1, 0.95, 1])
  const { direction, dragX, onDrag, reset } = useSwipe()

  const handleSwipeComplete = useCallback((dir: 'left' | 'right') => {
    if (!current) return
    const target = dir === 'right' ? 500 : -500
    animate(x, target, {
      type: 'spring',
      stiffness: 300,
      damping: 30,
      onComplete: () => {
        if (dir === 'right') onLike(current)
        else onPass()
        x.set(0)
        reset()
      },
    })
  }, [current, onLike, onPass, x, reset])

  const handleDragEnd = useCallback(
    (_: unknown, info: { offset: { x: number }; velocity: { x: number } }) => {
      const { offset, velocity } = info
      if (offset.x > SWIPE_THRESHOLD || velocity.x > SWIPE_VELOCITY) {
        handleSwipeComplete('right')
      } else if (offset.x < -SWIPE_THRESHOLD || velocity.x < -SWIPE_VELOCITY) {
        handleSwipeComplete('left')
      } else {
        animate(x, 0, { type: 'spring', stiffness: 500, damping: 40 })
        reset()
      }
    },
    [handleSwipeComplete, x, reset],
  )

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') handleSwipeComplete('right')
      else if (e.key === 'ArrowLeft') handleSwipeComplete('left')
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [handleSwipeComplete])

  // Sync dragX from motion value
  useEffect(() => {
    const unsub = x.on('change', v => {
      onDrag(null, { offset: { x: v } })
    })
    return unsub
  }, [x, onDrag])

  if (loading && !current) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="font-sans text-sm text-muted animate-pulse">Loading poems...</p>
      </div>
    )
  }

  return (
    <div className="relative h-full">
      {/* Next card (behind) */}
      {next && (
        <motion.div className="absolute inset-0" style={{ scale: nextScale }}>
          <PoemCard poem={next} />
        </motion.div>
      )}

      {/* Current card (draggable) */}
      {current && (
        <motion.div
          className="absolute inset-0 z-10 cursor-grab active:cursor-grabbing"
          style={{ x, rotate }}
          drag="x"
          dragDirectionLock
          dragConstraints={{ left: 0, right: 0 }}
          dragElastic={1}
          onDragEnd={handleDragEnd}
        >
          <PoemCard poem={current} />
          <SwipeIndicator direction={direction} dragX={dragX} />
        </motion.div>
      )}

      {/* Action buttons */}
      {current && (
        <div className="absolute bottom-6 left-0 right-0 z-20 flex justify-center gap-6">
          <button
            onClick={() => handleSwipeComplete('left')}
            className="w-14 h-14 rounded-full bg-cream shadow-md flex items-center justify-center text-pass text-2xl active:scale-90 transition-transform border border-pass/20"
            aria-label="Pass"
          >
            ✕
          </button>
          <button
            onClick={() => handleSwipeComplete('right')}
            className="w-14 h-14 rounded-full bg-cream shadow-md flex items-center justify-center text-like text-2xl active:scale-90 transition-transform border border-like/20"
            aria-label="Like"
          >
            ♥
          </button>
        </div>
      )}
    </div>
  )
}
