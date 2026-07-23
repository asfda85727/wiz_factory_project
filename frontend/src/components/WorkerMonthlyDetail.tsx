import { useEffect, useState } from "react"
import { api, ApiError } from "../services/apiClient"
import type { WorkerMonthlyAttendance } from "../types"

interface WorkerMonthlyDetailProps {
  workerId: string
  workerName: string
  month: string
  onClose: () => void
}

export function WorkerMonthlyDetail({ workerId, workerName, month, onClose }: WorkerMonthlyDetailProps) {
  const [detail, setDetail] = useState<WorkerMonthlyAttendance | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setIsLoading(true)
    setError(null)
    api
      .get<WorkerMonthlyAttendance>(`/attendance/worker-monthly?worker_id=${workerId}&month=${month}`)
      .then((response) => {
        if (!cancelled) setDetail(response)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "출역 상세를 불러오지 못했습니다.")
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [workerId, month])

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
              </tr>
            </thead>
            <tbody>
              {present.map((day) => (
                <tr key={day.work_date}>
                  <td>{day.work_date}</td>
                  <td>{day.site_name}</td>
                  <td>{day.trade ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}
