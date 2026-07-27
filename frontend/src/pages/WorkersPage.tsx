import { useEffect, useState } from "react"
import type { FormEvent } from "react"
import { api, ApiError } from "../services/apiClient"
import { useSites } from "../hooks/useSites"
import { WorkerDetailPanel } from "../components/WorkerDetailPanel"
import type { CursorPage, Worker, WorkerStatus } from "../types"

const STATUS_LABEL: Record<WorkerStatus, string> = {
  provisional: "임시등록",
  active: "정식",
}

export function WorkersPage() {
  const { sites } = useSites()
  const [workers, setWorkers] = useState<Worker[]>([])
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<"" | WorkerStatus>("")
  const [selectedWorkerId, setSelectedWorkerId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [listError, setListError] = useState<string | null>(null)

  const [newName, setNewName] = useState("")
  const [newBirthDate, setNewBirthDate] = useState("")
  const [newTrade, setNewTrade] = useState("")
  const [createError, setCreateError] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)

  const siteNameById = new Map(sites.map((site) => [site.id, site.name]))
  // 현장 제한 없이 "지금까지 입력된 공정" 전체를 후보로 보여준다(현재 로드된 목록 기준).
  const existingTrades = [...new Set(workers.map((w) => w.trade).filter((t): t is string => !!t))].sort()

  const loadWorkers = async () => {
    setIsLoading(true)
    setListError(null)
    try {
      const params = new URLSearchParams({ limit: "100" })
      if (search) params.set("search", search)
      if (statusFilter) params.set("status", statusFilter)
      const page = await api.get<CursorPage<Worker>>(`/workers?${params.toString()}`)
      setWorkers(page.data)
    } catch (err) {
      setListError(err instanceof ApiError ? err.message : "근로자 목록을 불러오지 못했습니다.")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadWorkers()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter])

  const handleSearchSubmit = (event: FormEvent) => {
    event.preventDefault()
    loadWorkers()
  }

  const handleCreate = async (event: FormEvent) => {
    event.preventDefault()
    setCreateError(null)
    setIsCreating(true)
    try {
      await api.post<Worker>("/workers", {
        name: newName,
        birth_date: newBirthDate || null,
        trade: newTrade || null,
      })
      setNewName("")
      setNewBirthDate("")
      setNewTrade("")
      await loadWorkers()
    } catch (err) {
      setCreateError(err instanceof ApiError ? err.message : "등록에 실패했습니다.")
    } finally {
      setIsCreating(false)
    }
  }

  const selectedWorker = workers.find((worker) => worker.id === selectedWorkerId) ?? null

  return (
    <div>
      <h1>근로자 입력</h1>

      <div className="panel">
        <h2>신규 임시 등록</h2>
        <form onSubmit={handleCreate} className="toolbar">
          <label>
            이름
            <input value={newName} onChange={(e) => setNewName(e.target.value)} required />
          </label>
          <label>
            생년월일 (선택 — 서류 없으면 이름만으로 등록 가능)
            <input type="date" value={newBirthDate} onChange={(e) => setNewBirthDate(e.target.value)} />
          </label>
          <label>
            공정 (선택)
            <input
              list="new-worker-trade-suggestions"
              value={newTrade}
              onChange={(e) => setNewTrade(e.target.value)}
              placeholder="예: 철거"
            />
            <datalist id="new-worker-trade-suggestions">
              {existingTrades.map((trade) => (
                <option key={trade} value={trade} />
              ))}
            </datalist>
          </label>
          <button type="submit" className="primary" disabled={isCreating}>
            등록
          </button>
        </form>
        {createError && <p className="form-error">{createError}</p>}
      </div>

      <div className="panel">
        <form onSubmit={handleSearchSubmit} className="toolbar">
          <label>
            검색
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="이름으로 검색"
            />
          </label>
          <label>
            상태
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as "" | WorkerStatus)}
            >
              <option value="">전체</option>
              <option value="provisional">임시등록</option>
              <option value="active">정식</option>
            </select>
          </label>
          <button type="submit">검색</button>
        </form>

        {listError && <p className="form-error">{listError}</p>}
        {isLoading ? (
          <p className="hint">불러오는 중...</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>이름</th>
                <th>생년월일</th>
                <th>공정</th>
                <th>상태</th>
                <th>소속 현장</th>
                <th>등록일</th>
              </tr>
            </thead>
            <tbody>
              {workers.map((worker) => (
                <tr
                  key={worker.id}
                  className="selectable"
                  onClick={() => setSelectedWorkerId(worker.id)}
                >
                  <td>{worker.name}</td>
                  <td>{worker.birth_date ?? "-"}</td>
                  <td>{worker.trade ?? "-"}</td>
                  <td>
                    <span className={`badge ${worker.status}`}>{STATUS_LABEL[worker.status]}</span>
                  </td>
                  <td>{worker.current_site_id ? (siteNameById.get(worker.current_site_id) ?? "-") : "-"}</td>
                  <td>{worker.created_at.slice(0, 10)}</td>
                </tr>
              ))}
              {workers.length === 0 && (
                <tr>
                  <td colSpan={6} className="hint">
                    등록된 근로자가 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {selectedWorker && (
        <WorkerDetailPanel
          worker={selectedWorker}
          sites={sites}
          existingTrades={existingTrades}
          onUpdated={(updated) => {
            setWorkers((prev) => prev.map((w) => (w.id === updated.id ? updated : w)))
          }}
          onDeleted={(deletedId) => {
            setWorkers((prev) => prev.filter((w) => w.id !== deletedId))
            setSelectedWorkerId(null)
          }}
          onClose={() => setSelectedWorkerId(null)}
        />
      )}
    </div>
  )
}
