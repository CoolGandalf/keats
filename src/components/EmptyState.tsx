interface Props {
  seenCount: number
  totalCount: number
  onReset: () => void
}

export default function EmptyState({ seenCount, totalCount, onReset }: Props) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-8 text-center">
      <p className="font-serif text-2xl text-ink mb-2">No more poems</p>
      <p className="font-sans text-sm text-muted mb-6">
        You've seen {seenCount} of {totalCount} poems
      </p>
      <button
        onClick={onReset}
        className="font-sans text-sm font-medium px-6 py-3 rounded-full bg-ink text-cream active:scale-95 transition-transform"
      >
        Start over
      </button>
    </div>
  )
}
