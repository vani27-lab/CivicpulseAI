import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { officerApi } from '../api/officerApi'
import { ComplaintFilters } from '../components/ComplaintFilters'
import { ComplaintTable } from '../components/ComplaintTable'
import { EmptyState, ErrorState, LoadingState } from '../components/States'
import { Pagination } from '../components/Pagination'
import { StatsGrid } from '../components/StatsGrid'
import { useAsync, useDebounced } from '../hooks/useAsync'

const PAGE_SIZE = 20
const FILTER_KEYS = Object.keys(ComplaintFilters.EMPTY)

export default function DashboardPage() {
  const [params, setParams] = useSearchParams()
  const filters = useMemo(() => Object.fromEntries(FILTER_KEYS.map((k) => [k, params.get(k) || ''])), [params])
  const sortBy = params.get('sort_by') || 'priority'
  const sortDir = params.get('sort_dir') || 'desc'
  const page = Number(params.get('page')) || 1

  // The search box updates instantly; the request waits until typing pauses.
  const [searchText, setSearchText] = useState(filters.q)
  const debouncedSearch = useDebounced(searchText)
  useEffect(() => {
    if (debouncedSearch !== filters.q) update({ q: debouncedSearch }, true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch])

  const update = (changes, resetPage = false) => {
    const next = new URLSearchParams(params)
    Object.entries(changes).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)))
    if (resetPage) next.delete('page')
    setParams(next, { replace: true })
  }

  const stats = useAsync((signal) => officerApi.stats(signal), [])
  const options = useAsync((signal) => officerApi.filterOptions(signal), [])
  const list = useAsync(
    (signal) => officerApi.complaints({ ...filters, sort_by: sortBy, sort_dir: sortDir, page, page_size: PAGE_SIZE }, signal),
    [params.toString()],
  )

  const onSort = (key) => {
    // First click on a column sorts most-urgent / newest first; a second click flips it.
    const dir = sortBy === key ? (sortDir === 'desc' ? 'asc' : 'desc') : 'desc'
    update({ sort_by: key, sort_dir: dir }, true)
  }

  return (
    <>
      <h1 className="text-2xl font-bold">Complaints</h1>

      {stats.error ? <ErrorState error={stats.error} onRetry={stats.reload} />
        : stats.data ? <StatsGrid stats={stats.data} /> : <LoadingState label="Loading summary..." />}

      <section className="panel" aria-label="Complaint list">
        {options.data && (
          <ComplaintFilters
            value={{ ...filters, q: searchText }}
            options={options.data}
            onChange={(v) => {
              const { q, ...rest } = v
              setSearchText(q) // the debounced effect above writes q to the URL
              update(rest, true)
            }}
          />
        )}
        {options.error && <ErrorState error={options.error} onRetry={options.reload} />}

        {list.error ? <ErrorState error={list.error} onRetry={list.reload} />
          : list.loading && !list.data ? <LoadingState label="Loading complaints..." />
          : list.data?.items.length === 0 ? (
            <EmptyState title="No complaints match these filters">
              Clear a filter or change the search to see more complaints.
            </EmptyState>
          ) : list.data && (
            <>
              <div aria-busy={list.loading}>
                <ComplaintTable items={list.data.items} sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
              </div>
              <Pagination page={list.data.page} pageSize={list.data.page_size} total={list.data.total}
                          onPage={(p) => update({ page: p > 1 ? String(p) : '' })} />
            </>
          )}
      </section>
    </>
  )
}
