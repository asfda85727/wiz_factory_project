import { useEffect, useState } from "react"
import { api, ApiError } from "../services/apiClient"
import { useSites } from "../hooks/useSites"
import type { WorkerAttendanceDay, WorkerMonthlyAttendance } from "../types"

interface WorkerMonthlyDetailProps {
  workerId: string
  workerName: string
  month: string
  onClose: () => void
}

export function WorkerMonthlyDetail({ workerId, workerName, month, onClose }: WorkerMonthlyDetailProps) {
  const { sites } = useSites()
  const [detail, setDetail] = useState<WorkerMonthlyAttendance | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editWorkDate, setEditWorkDate] = useState("")
  const [editSiteId, setEditSiteId] = useState("")
  const [editError, setEditError] = useState<string | null>(null)
  const [isSavingEdit, setIsSavingEdit] = useState(false)

  const loadDetail = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await api.get<WorkerMonthlyAttendance>(
        `/attendance/worker-monthly?worker_id=${workerId}&month=${month}`,
      )
      setDetail(response)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "출역 상세를 불러오지 못했습니다.")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadDetail()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workerId, month])

  const handleDelete = async (day: WorkerAttendanceDay) => {
    if (!confirm(`${day.work_date} 출역 기록을 삭제할까요? 되돌릴 수 없습니다.`)) return
    setError(null)
    setDeletingId(day.id)
    try {
      await api.delete(`/attendance/${day.id}`)
      setDetail((prev) => (prev ? { ...prev, data: prev.data.filter((d) => d.id !== day.id) } : prev))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "삭제에 실패했습니다.")
    } finally {
      setDeletingId(null)
    }
  }

  const startEdit = (day: WorkerAttendanceDay) => {
    setEditingId(day.id)
    setEditWorkDate(day.work_date)
    setEditSiteId(day.site_id)
    setEditError(null)
  }

  const cancelEdit = () => {
    setEditingId(null)
    setEditError(null)
  }

  const handleSaveEdit = async (dayId: string) => {
    setEditError(null)
    setIsSavingEdit(true)
    try {
      await api.patch(`/attendance/${dayId}`, { work_date: editWorkDate, site_id: editSiteId })
      setEditingId(null)
      await loadDetail()
    } catch (err) {
      setEditError(err instanceof ApiError ? err.message : "수정에 실패했습니다.")
    } finally {
      setIsSavingEdit(false)
    }
  }

  const present = detail?.data.filter((day) => day.is_present) ?? []

  return (
    <div className="panel worker-detail-panel">
      <div className="toolbar">
        <h2>
          {workerName} · {month} 출역 상세
        </h2>
        <button type="button" onClick={onClose} style={{ marginLeft: "auto" }}>
          닫기
        </button>
      </div>

      {error && <p className="form-error">{error}</p>}

      {isLoading ? (
        <p className="hint">불러오는 중...</p>
      ) : present.length === 0 ? (
        <p className="hint">이 달에 출역한 기록이 없습니다.</p>
      ) : (
        <>
          <p className="hint">총 {present.length}일 출역</p>
          <table>
            <thead>
              <tr>
                <th>날짜</th>
                <th>현장</th>
                <th>공정</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {present.map((day) =>
                editingId === day.id ? (
                  <tr key={day.id}>
                    <td>
                      <input type="date" value={editWorkDate} onChange={(e) => setEditWorkDate(e.target.value)} />
                    </td>
                    <td>
                      <select value={editSiteId} onChange={(e) => setEditSiteId(e.target.value)}>
                        {sites.map((site) => (
                          <option key={site.id} value={site.id}>
                            {site.name}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>{day.trade ?? "-"}</td>
                    <td>
                      <button type="button" onClick={() => handleSaveEdit(day.id)} disabled={isSavingEdit}>
                        저장
                      </button>
                      <button type="button" onClick={cancelEdit} disabled={isSavingEdit}>
                        취소
                      </button>
                    </td>
                  </tr>
                ) : (
                  <tr key={day.id}>
                    <td>{day.work_date}</td>
                    <td>{day.site_name}</td>
                    <td>{day.trade ?? "-"}</td>
                    <td>
                      <button type="button" onClick={() => startEdit(day)}>
                        수정
                      </button>
                      <button type="button" onClick={() => handleDelete(day)} disabled={deletingId === day.id}>
                        삭제
                      </button>
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
          {editError && <p className="form-error">{editError}</p>}
        </>
      )}
    </div>
  )
}
