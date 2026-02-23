import { createHash } from 'crypto'
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'fs'
import { join } from 'path'

interface RawPoem {
  title: string
  author: string
  lines: string[]
  linecount: string
  source: string
  category?: string
  reading_time_minutes?: number
}

interface ProcessedPoem {
  id: string
  title: string
  author: string
  lines: string[]
  linecount: number
  reading_time_minutes: number
  rank: number | null
  chunk: number
  prose: boolean
  source: string
}

const CHUNK_SIZE = 100
const DATA_DIR = join(import.meta.dirname, '..', 'data')
const OUT_DIR = join(import.meta.dirname, '..', 'public', 'poems')

function makeId(title: string, author: string): string {
  return createHash('sha256').update(`${title}|${author}`).digest('hex').slice(0, 12)
}

function parseRankedList(text: string): Map<string, number> {
  const ranked = new Map<string, number>()
  const lines = text.split('\n')
  let i = 0
  while (i < lines.length) {
    const line = lines[i].trim()
    // Look for lines that are just a number (rank)
    if (/^\d+$/.test(line)) {
      const rank = parseInt(line, 10)
      const title = (lines[i + 1] || '').replace(/^\t/, '').trim()
      const author = (lines[i + 2] || '').replace(/^\t/, '').trim()
      if (title && author) {
        ranked.set(normalize(title, author), rank)
      }
      i += 3
    } else {
      i++
    }
  }
  return ranked
}

function normalize(title: string, author: string): string {
  return `${title.toLowerCase().replace(/[^a-z0-9 ]/g, '')}|${author.toLowerCase().replace(/[^a-z0-9 ]/g, '')}`
}

function fuzzyMatch(poemTitle: string, poemAuthor: string, ranked: Map<string, number>): number | null {
  // Exact normalized match
  const key = normalize(poemTitle, poemAuthor)
  if (ranked.has(key)) return ranked.get(key)!

  // Try matching by last name only
  const authorLast = poemAuthor.split(/\s+/).pop()?.toLowerCase().replace(/[^a-z]/g, '') || ''
  const titleNorm = poemTitle.toLowerCase().replace(/[^a-z0-9 ]/g, '')

  for (const [k, rank] of ranked) {
    const [rTitle, rAuthor] = k.split('|')
    const rAuthorLast = rAuthor.split(/\s+/).pop() || ''
    if (titleNorm === rTitle && authorLast === rAuthorLast) return rank
  }

  return null
}

function countLines(lines: string[]): number {
  return lines.filter(l => l.trim() !== '').length
}

function wordCount(lines: string[]): number {
  return lines.join(' ').split(/\s+/).filter(Boolean).length
}

function readingTime(lines: string[]): number {
  return Math.round((wordCount(lines) / 200) * 10) / 10 || 0.5
}

const MAX_WORDS = 500 // skip wall-of-text poems

// Main
console.log('Loading catalog...')
const catalog: RawPoem[] = JSON.parse(readFileSync(join(DATA_DIR, 'catalog.json'), 'utf-8'))
const rankedText = readFileSync(join(DATA_DIR, 'ranked_top1000.txt'), 'utf-8')
const ranked = parseRankedList(rankedText)
console.log(`Parsed ${ranked.size} ranked poems`)

// Process poems
const seen = new Set<string>()
const poems: ProcessedPoem[] = []

for (const raw of catalog) {
  const id = makeId(raw.title, raw.author)
  if (seen.has(id)) continue
  seen.add(id)

  const isProse = raw.source === 'poetry_foundation' && raw.lines.length === 1

  // Skip prose-flagged (mangled single-line) and overly long poems
  if (isProse) continue
  if (wordCount(raw.lines) > MAX_WORDS) continue

  const rank = fuzzyMatch(raw.title, raw.author, ranked)

  poems.push({
    id,
    title: raw.title,
    author: raw.author,
    lines: raw.lines,
    linecount: countLines(raw.lines),
    reading_time_minutes: readingTime(raw.lines),
    rank,
    chunk: 0, // assigned below
    prose: false,
    source: raw.source,
  })
}

// Sort: ranked first (by rank), then unranked alphabetically
poems.sort((a, b) => {
  if (a.rank !== null && b.rank !== null) return a.rank - b.rank
  if (a.rank !== null) return -1
  if (b.rank !== null) return 1
  return a.title.localeCompare(b.title)
})

// Assign chunks
for (let i = 0; i < poems.length; i++) {
  poems[i].chunk = Math.floor(i / CHUNK_SIZE)
}

const chunkCount = Math.ceil(poems.length / CHUNK_SIZE)

// Write output
if (!existsSync(OUT_DIR)) mkdirSync(OUT_DIR, { recursive: true })

// Index (metadata only)
const index = {
  poems: poems.map(({ id, title, author, linecount, reading_time_minutes, rank, chunk, prose }) => ({
    id, title, author, linecount, reading_time_minutes, rank, chunk, prose,
  })),
  chunkCount,
}
writeFileSync(join(OUT_DIR, 'index.json'), JSON.stringify(index))
console.log(`Wrote index.json (${poems.length} poems)`)

// Chunks (full data)
for (let c = 0; c < chunkCount; c++) {
  const chunkPoems = poems
    .filter(p => p.chunk === c)
    .map(({ id, title, author, lines, linecount, reading_time_minutes, rank, chunk, prose }) => ({
      id, title, author, lines, linecount, reading_time_minutes, rank, chunk, prose,
    }))
  writeFileSync(join(OUT_DIR, `chunk-${c}.json`), JSON.stringify(chunkPoems))
}
console.log(`Wrote ${chunkCount} chunks`)

// Stats
const rankedCount = poems.filter(p => p.rank !== null).length
const proseCount = poems.filter(p => p.prose).length
console.log(`Ranked: ${rankedCount}, Prose-flagged: ${proseCount}, Total: ${poems.length}`)
