export interface PoemMeta {
  id: string
  title: string
  author: string
  linecount: number
  reading_time_minutes: number
  rank: number | null
  chunk: number
  prose: boolean
}

export interface Poem extends PoemMeta {
  lines: string[]
}

export interface PoemIndex {
  poems: PoemMeta[]
  chunkCount: number
}
