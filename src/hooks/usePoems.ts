import { useState, useEffect, useCallback, useRef } from 'react'
import type { PoemMeta, Poem, PoemIndex } from '../types/poem'
import { tieredShuffle } from '../lib/shuffle'
import { load, save } from '../lib/storage'

const QUEUE_BUFFER = 5 // keep at least this many poems ready

export function usePoems() {
  const [queue, setQueue] = useState<Poem[]>([])
  const [loading, setLoading] = useState(true)
  const indexRef = useRef<PoemIndex | null>(null)
  const shuffledRef = useRef<PoemMeta[]>([])
  const loadedChunks = useRef<Set<number>>(new Set())
  const chunkCache = useRef<Map<number, Poem[]>>(new Map())
  const cursorRef = useRef(0)
  const seenRef = useRef<Set<string>>(new Set(load<string[]>('seen', [])))

  // Load index on mount
  useEffect(() => {
    fetch('/poems/index.json')
      .then(r => r.json())
      .then((index: PoemIndex) => {
        indexRef.current = index
        shuffledRef.current = tieredShuffle(index.poems, seenRef.current)
        cursorRef.current = 0
        fillQueue()
      })
      .catch(console.error)
  }, [])

  const fetchChunk = useCallback(async (chunkNum: number): Promise<Poem[]> => {
    if (chunkCache.current.has(chunkNum)) return chunkCache.current.get(chunkNum)!
    if (loadedChunks.current.has(chunkNum)) return chunkCache.current.get(chunkNum) || []
    loadedChunks.current.add(chunkNum)

    const res = await fetch(`/poems/chunk-${chunkNum}.json`)
    const poems: Poem[] = await res.json()
    chunkCache.current.set(chunkNum, poems)
    return poems
  }, [])

  const fillQueue = useCallback(async () => {
    const shuffled = shuffledRef.current
    if (!shuffled.length) {
      setLoading(false)
      return
    }

    const needed = QUEUE_BUFFER
    const toLoad: PoemMeta[] = []

    while (toLoad.length < needed && cursorRef.current < shuffled.length) {
      toLoad.push(shuffled[cursorRef.current])
      cursorRef.current++
    }

    if (toLoad.length === 0) {
      setLoading(false)
      return
    }

    // Determine which chunks we need
    const chunksNeeded = new Set(toLoad.map(p => p.chunk))
    await Promise.all([...chunksNeeded].map(fetchChunk))

    // Resolve full poems from cache
    const resolved: Poem[] = []
    for (const meta of toLoad) {
      const chunk = chunkCache.current.get(meta.chunk)
      const poem = chunk?.find(p => p.id === meta.id)
      if (poem) resolved.push(poem)
    }

    setQueue(prev => [...prev, ...resolved])
    setLoading(false)
  }, [fetchChunk])

  const advance = useCallback(() => {
    setQueue(prev => {
      const next = prev.slice(1)
      const current = prev[0]
      if (current) {
        seenRef.current.add(current.id)
        save('seen', [...seenRef.current])
      }
      // Refill if running low
      if (next.length < QUEUE_BUFFER) {
        fillQueue()
      }
      return next
    })
  }, [fillQueue])

  const resetSeen = useCallback(() => {
    seenRef.current = new Set()
    save('seen', [])
    if (indexRef.current) {
      shuffledRef.current = tieredShuffle(indexRef.current.poems, seenRef.current)
      cursorRef.current = 0
      setQueue([])
      setLoading(true)
      fillQueue()
    }
  }, [fillQueue])

  return {
    current: queue[0] || null,
    next: queue[1] || null,
    advance,
    loading,
    isEmpty: !loading && queue.length === 0,
    resetSeen,
    seenCount: seenRef.current.size,
    totalCount: indexRef.current?.poems.length || 0,
  }
}
