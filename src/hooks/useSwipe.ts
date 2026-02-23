import { useState, useCallback } from 'react'

export type SwipeDirection = 'left' | 'right' | null

export function useSwipe() {
  const [direction, setDirection] = useState<SwipeDirection>(null)
  const [swiping, setSwiping] = useState(false)
  const [dragX, setDragX] = useState(0)

  const onDrag = useCallback((_: unknown, info: { offset: { x: number } }) => {
    setDragX(info.offset.x)
    setSwiping(true)
    if (info.offset.x > 40) setDirection('right')
    else if (info.offset.x < -40) setDirection('left')
    else setDirection(null)
  }, [])

  const reset = useCallback(() => {
    setDirection(null)
    setSwiping(false)
    setDragX(0)
  }, [])

  return { direction, swiping, dragX, onDrag, reset, setDirection }
}
