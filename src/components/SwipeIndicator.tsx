import { motion } from 'framer-motion'
import type { SwipeDirection } from '../hooks/useSwipe'

interface Props {
  direction: SwipeDirection
  dragX: number
}

export default function SwipeIndicator({ direction, dragX }: Props) {
  const opacity = Math.min(Math.abs(dragX) / 120, 1)

  return (
    <>
      {/* Like indicator */}
      <motion.div
        className="absolute top-8 right-8 z-10 rounded-xl border-4 border-like px-4 py-2 font-sans font-semibold text-like text-2xl -rotate-12"
        style={{ opacity: direction === 'right' ? opacity : 0 }}
      >
        LIKE
      </motion.div>

      {/* Pass indicator */}
      <motion.div
        className="absolute top-8 left-8 z-10 rounded-xl border-4 border-pass px-4 py-2 font-sans font-semibold text-pass text-2xl rotate-12"
        style={{ opacity: direction === 'left' ? opacity : 0 }}
      >
        NOPE
      </motion.div>
    </>
  )
}
