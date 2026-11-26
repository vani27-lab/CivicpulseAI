import { config } from '../config'
import { request } from './http'

const p = config.paths

export const officerApi = {
  stats: (signal) => request(p.stats, { signal }),
  filterOptions: (signal) => request(p.filters, { signal }),
  complaints: (params, signal) => request(p.complaints, { params, signal }),
  complaint: (id, signal) => request(`${p.complaints}/${id}`, { signal }),
  mapPoints: (params, signal) => request(p.complaintMap, { params, signal }),
  heatmap: (params, signal) => request(p.heatmap, { params, signal }),

  /** Status change. `photo` is a File (required to resolve unless admin override). */
  updateStatus: (id, { newStatus, comment, photo, adminOverride, overrideReason }) => {
    const form = new FormData()
    form.append('new_status', newStatus)
    if (comment) form.append('comment', comment)
    if (photo) form.append('after_photo', photo)
    if (adminOverride) {
      form.append('admin_override', 'true')
      form.append('override_reason', overrideReason || '')
    }
    return request(p.status(id), { method: 'PATCH', form })
  },

  correctClassification: (id, { issueType, reason }) =>
    request(p.classification(id), { method: 'PATCH', json: { issue_type: issueType, reason: reason || null } }),

  duplicates: (params, signal) => request(p.duplicates, { params, signal }),
  confirmMerge: (candidateId) => request(p.confirmMerge(candidateId), { method: 'POST' }),
  rejectMerge: (candidateId) => request(p.rejectMerge(candidateId), { method: 'POST' }),
  split: (id, { reportIds, reason }) =>
    request(p.split(id), { method: 'POST', json: { report_ids: reportIds, reason } }),
}
