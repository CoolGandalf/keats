import type { PoemMeta } from '../types/poem'

/**
 * Tiered Fisher-Yates shuffle.
 * Ranked poems are interleaved so top-ranked appear earlier
 * without a hard boundary between tiers.
 */
export function tieredShuffle(poems: PoemMeta[], seen: Set<string>): PoemMeta[] {
  const unseen = poems.filter(p => !seen.has(p.id))

  // Split into tiers
  const top100: PoemMeta[] = []
  const mid: PoemMeta[] = []
  const low: PoemMeta[] = []
  const unranked: PoemMeta[] = []

  for (const p of unseen) {
    if (p.rank !== null && p.rank <= 100) top100.push(p)
    else if (p.rank !== null && p.rank <= 500) mid.push(p)
    else if (p.rank !== null) low.push(p)
    else unranked.push(p)
  }

  fisherYates(top100)
  fisherYates(mid)
  fisherYates(low)
  fisherYates(unranked)

  // Interleave: take from tiers in weighted round-robin
  const result: PoemMeta[] = []
  const queues = [top100, mid, low, unranked]
  const weights = [3, 2, 1, 1] // top100 poems 3× more likely to appear early

  let exhausted = 0
  while (exhausted < queues.length) {
    exhausted = 0
    for (let i = 0; i < queues.length; i++) {
      const take = weights[i]
      for (let j = 0; j < take && queues[i].length > 0; j++) {
        result.push(queues[i].pop()!)
      }
      if (queues[i].length === 0) exhausted++
    }
  }

  return result
}

function fisherYates<T>(arr: T[]): void {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[arr[i], arr[j]] = [arr[j], arr[i]]
  }
}
