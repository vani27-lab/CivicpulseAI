import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import { ComplaintTable } from '../components/ComplaintTable'

const items = [
  { id: 'aaaaaaaa-1111', issue_type: 'Pothole', status: 'submitted', department_name: 'Roads', report_count: 12,
    priority_score: 68, priority_band: 'HIGH', created_at: '2026-11-01T10:00:00Z', latitude: 27.49, longitude: 77.67 },
  { id: 'bbbbbbbb-2222', issue_type: 'Garbage', status: 'in_progress', department_name: null, report_count: 1,
    priority_score: 20, priority_band: 'LOW', created_at: '2026-11-02T10:00:00Z', latitude: null, longitude: null },
]

const renderTable = (props = {}) =>
  render(
    <MemoryRouter>
      <ComplaintTable items={items} sortBy="priority" sortDir="desc" onSort={() => {}} {...props} />
    </MemoryRouter>,
  )

describe('ComplaintTable', () => {
  it('renders one row per complaint, in the order the API returned (HIGH first)', () => {
    renderTable()
    const rows = screen.getAllByTestId('complaint-row')
    expect(rows).toHaveLength(2)
    expect(within(rows[0]).getByText('HIGH \u2014 68/100')).toBeInTheDocument()
    expect(within(rows[1]).getByText('Unassigned')).toBeInTheDocument()
  })

  it('shows every required column', () => {
    renderTable()
    ;['Complaint ID', 'Issue', 'Location', 'Department', 'Reports', 'Priority', 'Status', 'Submitted', 'Actions']
      .forEach((name) => expect(screen.getByRole('columnheader', { name: new RegExp(name) })).toBeInTheDocument())
  })

  it('exposes the active sort to assistive tech and reports clicks', async () => {
    const onSort = vi.fn()
    renderTable({ onSort })
    expect(screen.getByRole('columnheader', { name: /Priority/ })).toHaveAttribute('aria-sort', 'descending')
    await userEvent.click(screen.getByRole('button', { name: /Submitted/ }))
    expect(onSort).toHaveBeenCalledWith('created_at')
  })

  it('links each row to its detail page', () => {
    renderTable()
    expect(screen.getAllByRole('link')[0]).toHaveAttribute('href', '/officer/complaints/aaaaaaaa-1111')
  })
})
