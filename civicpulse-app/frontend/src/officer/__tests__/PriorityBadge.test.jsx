import { render, screen } from '@testing-library/react'
import { PriorityBadge } from '../components/PriorityBadge'
import { PriorityExplanation } from '../components/PriorityExplanation'

describe('PriorityBadge', () => {
  it('shows band and score in the "HIGH — 68/100" format', () => {
    render(<PriorityBadge band="HIGH" score={68} />)
    expect(screen.getByText('HIGH \u2014 68/100')).toBeInTheDocument()
  })

  it.each([
    ['HIGH', 'text-high-text'],
    ['MEDIUM', 'text-medium-text'],
    ['LOW', 'text-low-text'],
  ])('colours %s with its own palette', (band, cls) => {
    render(<PriorityBadge band={band} score={50} />)
    expect(screen.getByText(new RegExp(band)).className).toContain(cls)
  })

  it('still renders when the score is missing', () => {
    render(<PriorityBadge band="LOW" score={null} />)
    expect(screen.getByText('LOW')).toBeInTheDocument()
  })
})

describe('PriorityExplanation', () => {
  it('lists the reasons Module 4 produced', () => {
    render(<PriorityExplanation reasons={['Serious pothole', '12 citizen reports']} />)
    expect(screen.getAllByRole('listitem')).toHaveLength(2)
  })

  it('shows an honest empty message instead of inventing reasons', () => {
    render(<PriorityExplanation reasons={[]} />)
    expect(screen.getByText(/did not record an explanation/i)).toBeInTheDocument()
  })
})
