interface PaginationProps {
  page: number
  lastPage: number
  onPageChange: (page: number) => void
}

export default function Pagination({ page, lastPage, onPageChange }: PaginationProps) {
  return (
    <div id="pagination">
      <button disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
        Prev
      </button>
      <span>{page} / {lastPage}</span>
      <button disabled={page >= lastPage} onClick={() => onPageChange(page + 1)}>
        Next
      </button>
    </div>
  )
}
