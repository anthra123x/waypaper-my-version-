interface PaginationProps {
  page: number
  lastPage: number
  onPageChange: (page: number) => void
}

export default function Pagination({ page, lastPage, onPageChange }: PaginationProps) {
  const pages: (number | string)[] = []
  const maxVisible = 7

  if (lastPage <= maxVisible) {
    for (let i = 1; i <= lastPage; i++) pages.push(i)
  } else {
    pages.push(1)
    if (page > 3) pages.push('…')
    const start = Math.max(2, page - 1)
    const end = Math.min(lastPage - 1, page + 1)
    for (let i = start; i <= end; i++) pages.push(i)
    if (page < lastPage - 2) pages.push('…')
    pages.push(lastPage)
  }

  return (
    <div id="pagination">
      <button className="page-btn" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
        ‹ Prev
      </button>
      {pages.map((p, i) =>
        typeof p === 'string' ? (
          <span key={`ellipsis-${i}`} className="page-ellipsis">{p}</span>
        ) : (
          <button
            key={p}
            className={`page-btn ${p === page ? 'active' : ''}`}
            onClick={() => onPageChange(p)}
            disabled={p === page}
          >
            {p}
          </button>
        )
      )}
      <button className="page-btn" disabled={page >= lastPage} onClick={() => onPageChange(page + 1)}>
        Next ›
      </button>
      <span className="page-total">{lastPage} pages</span>
    </div>
  )
}
