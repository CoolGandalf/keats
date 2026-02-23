import { parseInlineFormatting } from '../lib/poem-utils'

interface Props {
  lines: string[]
  prose: boolean
}

export default function PoemText({ lines, prose }: Props) {
  if (prose) {
    // Single-line poems from Poetry Foundation — render as flowing paragraph
    const text = lines.join(' ')
    return (
      <div className="font-serif text-[1.125rem] leading-[1.75] text-ink">
        <p>{parseInlineFormatting(text)}</p>
      </div>
    )
  }

  return (
    <div className="font-serif text-[1.125rem] leading-[1.75] text-ink">
      {lines.map((line, i) => {
        if (line === '' || line.trim() === '') {
          return <div key={i} className="h-[1em]" />
        }
        return (
          <p key={i} className="whitespace-pre-wrap m-0">
            {parseInlineFormatting(line)}
          </p>
        )
      })}
    </div>
  )
}
