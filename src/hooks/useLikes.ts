import { useState, useCallback } from 'react'
import type { Poem } from '../types/poem'
import { load, save } from '../lib/storage'

interface LikedPoem extends Poem {
  likedAt: number
}

export function useLikes() {
  const [likes, setLikes] = useState<LikedPoem[]>(() => load<LikedPoem[]>('likes', []))

  const likePoem = useCallback((poem: Poem) => {
    setLikes(prev => {
      if (prev.some(p => p.id === poem.id)) return prev
      const next = [{ ...poem, likedAt: Date.now() }, ...prev]
      save('likes', next)
      return next
    })
  }, [])

  const unlikePoem = useCallback((id: string) => {
    setLikes(prev => {
      const next = prev.filter(p => p.id !== id)
      save('likes', next)
      return next
    })
  }, [])

  const isLiked = useCallback((id: string) => {
    return likes.some(p => p.id === id)
  }, [likes])

  return { likes, likePoem, unlikePoem, isLiked }
}
