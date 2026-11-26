import { formatScore } from '../lib/format'
import { priorityStyle } from '../lib/labels'

/** "HIGH — 68/100". Band and score come from Module 4; nothing is recalculated here. */
export function PriorityBadge({ band, score }) {
  const style = priorityStyle(band)
  const bandText = band ? String(band).toUpperCase() : 'UNRATED'
  return (
    <span className={`inline-flex items-center rounded px-2 py-0.5 text-sm font-semibold ${style.badge}`}>
      {score == null ? bandText : `${bandText} \u2014 ${formatScore(score)}/100`}
    </span>
  )
}
