import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

vi.mock('../api/officerApi', () => ({ officerApi: { updateStatus: vi.fn() } }))
import { officerApi } from '../api/officerApi'
import { StatusUpdateForm } from '../components/StatusUpdateForm'

const setup = (props = {}) =>
  render(
    <StatusUpdateForm complaintId="c1" currentStatus="in_progress" allowedNextStatuses={['resolved', 'assigned']}
                      canOverride={false} onUpdated={vi.fn()} {...props} />,
  )

const photo = (name = 'after.png', type = 'image/png', size = 1000) => {
  const file = new File(['x'.repeat(10)], name, { type })
  Object.defineProperty(file, 'size', { value: size })
  return file
}

beforeEach(() => { vi.clearAllMocks(); global.URL.createObjectURL = vi.fn(() => 'blob:x'); global.URL.revokeObjectURL = vi.fn() })

describe('StatusUpdateForm', () => {
  it('only offers the transitions the server allowed', () => {
    setup()
    const options = screen.getAllByRole('option').map((o) => o.textContent)
    expect(options).toEqual(['Select a status', 'Resolved', 'Assigned'])
  })

  it('requires an after-photo before a complaint can be resolved', async () => {
    setup()
    await userEvent.selectOptions(screen.getByLabelText(/move to/i), 'resolved')
    expect(screen.getByRole('button', { name: /resolve complaint/i })).toBeDisabled()
    await userEvent.upload(screen.getByLabelText(/after-photo/i), photo())
    expect(screen.getByRole('button', { name: /resolve complaint/i })).toBeEnabled()
  })

  it('rejects non-image files and oversized photos before upload', async () => {
    setup()
    const user = userEvent.setup({ applyAccept: false }) // let the PDF through so the component's own check runs
    await user.selectOptions(screen.getByLabelText(/move to/i), 'resolved')
    await user.upload(screen.getByLabelText(/after-photo/i), photo('x.pdf', 'application/pdf'))
    expect(screen.getByRole('alert')).toHaveTextContent(/JPEG, PNG or WebP/)
    await user.upload(screen.getByLabelText(/after-photo/i), photo('big.png', 'image/png', 9 * 1024 * 1024))
    expect(screen.getByRole('alert')).toHaveTextContent(/8 MB/)
  })

  it('sends status, comment and photo, then reports success', async () => {
    officerApi.updateStatus.mockResolvedValue({ new_status: 'resolved' })
    const onUpdated = vi.fn()
    setup({ onUpdated })
    await userEvent.selectOptions(screen.getByLabelText(/move to/i), 'resolved')
    await userEvent.type(screen.getByLabelText(/comment/i), 'Pothole filled')
    const file = photo()
    await userEvent.upload(screen.getByLabelText(/after-photo/i), file)
    await userEvent.click(screen.getByRole('button', { name: /resolve complaint/i }))
    await waitFor(() => expect(onUpdated).toHaveBeenCalled())
    expect(officerApi.updateStatus).toHaveBeenCalledWith('c1', expect.objectContaining({
      newStatus: 'resolved', comment: 'Pothole filled', photo: file, adminOverride: false,
    }))
    expect(screen.getByRole('status')).toHaveTextContent(/changed to Resolved/)
  })

  it('shows the server error when the update fails', async () => {
    officerApi.updateStatus.mockRejectedValue(new Error('Upload an after-photo to resolve this complaint.'))
    setup({ allowedNextStatuses: ['assigned'] })
    await userEvent.selectOptions(screen.getByLabelText(/move to/i), 'assigned')
    await userEvent.click(screen.getByRole('button', { name: /update status/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/after-photo/)
  })

  it('shows the override control to admins only, and demands a reason', async () => {
    const { unmount } = setup()
    expect(screen.queryByText(/admin override/i)).not.toBeInTheDocument()
    unmount()
    setup({ canOverride: true })
    await userEvent.click(screen.getByLabelText(/skip workflow/i))
    await userEvent.selectOptions(screen.getByLabelText(/move to/i), 'resolved')
    expect(screen.getByRole('button', { name: /resolve complaint/i })).toBeDisabled()
    await userEvent.type(screen.getByLabelText(/reason for override/i), 'Verified on site')
    expect(screen.getByRole('button', { name: /resolve complaint/i })).toBeEnabled()
  })

  it('explains when no transitions remain', () => {
    setup({ currentStatus: 'resolved', allowedNextStatuses: [] })
    expect(screen.getByText(/no further status changes/i)).toBeInTheDocument()
  })
})
