import { formatConfidence, formatCoords, formatDate, shortId } from '../lib/format'
import { priorityStyle, statusLabel } from '../lib/labels'

describe('format helpers', () => {
  it('handles missing values without crashing', () => {
    expect(formatDate(null)).toBe('-')
    expect(formatDate('not a date')).toBe('-')
    expect(formatCoords(null, null)).toBe('No location')
    expect(shortId(undefined)).toBe('-')
  })

  it('formats confidence given as a fraction or a percentage', () => {
    expect(formatConfidence(0.87)).toBe('87%')
    expect(formatConfidence(87)).toBe('87%')
  })

  it('formats coordinates to five decimals', () => {
    expect(formatCoords(27.492413, 77.673673)).toBe('27.49241, 77.67367')
  })
})

describe('labels', () => {
  it('uses the red / orange / green palette for HIGH / MEDIUM / LOW', () => {
    expect(priorityStyle('high').badge).toContain('high')
    expect(priorityStyle('MEDIUM').badge).toContain('medium')
    expect(priorityStyle('Low').badge).toContain('low')
    expect(priorityStyle(undefined).label).toBe('Unrated')
  })

  it('labels statuses for display', () => {
    expect(statusLabel('in_progress')).toBe('In Progress')
    expect(statusLabel(null)).toBe('Unknown')
  })
})
