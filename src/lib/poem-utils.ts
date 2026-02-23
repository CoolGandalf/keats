import type { ReactNode } from 'react'
import { createElement } from 'react'

/**
 * Parse _italic_ markers in a line into React elements.
 */
export function parseInlineFormatting(text: string): ReactNode[] {
  const parts: ReactNode[] = []
  const regex = /_([^_]+)_/g
  let last = 0
  let match: RegExpExecArray | null

  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) {
      parts.push(text.slice(last, match.index))
    }
    parts.push(createElement('em', { key: match.index }, match[1]))
    last = regex.lastIndex
  }

  if (last < text.length) {
    parts.push(text.slice(last))
  }

  return parts.length > 0 ? parts : [text]
}

/**
 * Format reading time for display.
 */
export function formatReadingTime(minutes: number): string {
  if (minutes < 1) return '< 1 min read'
  return `${Math.round(minutes)} min read`
}
