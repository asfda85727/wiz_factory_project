import { useState } from "react"
import { api, ApiError } from "../services/apiClient"
import type { AttendancePdfPreviewResponse, AttendancePdfPreviewRow, AttendanceRecord, AttendanceSummary, Worker } from "../types"

interface RowState extends AttendancePdfPreviewRow {
  included: boolean
  updateTrade: boolean
}

interface AttendancePdfImportPanelProps {
  siteId: string
  preview: AttendancePdfPreviewResponse
  onClose: () => void
  onSaved: (savedDates: string[]) => void
}

function groupByDate<T extends { work_date: string }>(items: T[]): [string, T[]][] {
  const groups = new Map<string, T[]>()
  for (const item of items) {
    const existing = groups.get(item.work_date)
    if (existing) {
      existing.push(item)
    } else {
      groups.set(item.work_date, [item])
    }
  }
  return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b))
}

// 같은 공정명("관리자" 등)은 물리적으로 다른 열(본대/철거팀)에 나뉘어 있어도 화면에서는
// 한 덩어리로 붙어 보여야 한다 — 그 안에서는 원본 열 순서(column_index)대로, 즉 첫 번째
// 관리자 열 인원이 세로로 다 나온 뒤 두 번째 관리자 열 인원이 이어지도록 정렬한다.
function orderByTradeThenColumn<T extends { trade: string; column_index: number }>(items: T[]): T[] {
  const firstSeenOrder: string[] = []
  for (const item of items) {
    if (!firstSeenOrder.includes(item.trade)) firstSeenOrder.push(item.trade)
  }
  return [...items].sort((a, b) => {
    const tradeDiff = firstSeenOrder.indexOf(a.trade) - firstSeenOrder.indexOf(b.trade)
    return tradeDiff !== 0 ? tradeDiff : a.column_index - b.column_index
  })
}

export function AttendancePdfImportPanel({ siteId, preview, onClose, onSaved }: AttendancePdfImportPanelProps) {
  const [rows, setRows] = useState<RowState[]>(
    preview.rows.map((row) => ({ ...row, included: true, updateTrade: false })),
  )
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const toggleIncluded = (index: number) => {
    setRows((prev) => prev.map((row, i) => (i === index ? { ...row, included: !row.included } : row)))
  }

  const toggleUpdateTrade = (index: number) => {
    setRows((prev) => prev.map((row, i) => (i === index ? { ...row, updateTrade: !row.updateTrade } : row)))
  }

  const editTrade = (index: number, trade: string) => {
    setRows((prev) => prev.map((row, i) => (i === index ? { ...row, trade } : row)))
  }

  const handleConfirm = async () => {
    setIsSaving(true)
    setError(null)
    try {
      const includedRows = rows.filter((row) => row.included)

      // 같은 이름이 여러 날짜/공정 열에 신규로 등장해도 한 사람이므로 근로자는 이름당 1명만 생성
      const newWorkerIdByName = new Map<string, string>()
      for (const row of includedRows) {
        if (row.is_new && !newWorkerIdByName.has(row.raw_name)) {
          const created = await api.post<Worker>("/workers", {
            name: row.raw_name,
            trade: row.trade,
            current_site_id: siteId,
          })
          newWorkerIdByName.set(row.raw_name, created.id)
        }
      }

      const updatedTradeWorkerIds = new Set<string>()
      for (const row of includedRows) {
        if (row.updateTrade && row.matched_worker_id && !updatedTradeWorkerIds.has(row.matched_worker_id)) {
          await api.patch<Worker>(`/workers/${row.matched_worker_id}`, { trade: row.trade })
          updatedTradeWorkerIds.add(row.matched_worker_id)
        }
      }

      const resolvedWorkerId = (row: RowState): string =>
        row.matched_worker_id ?? newWorkerIdByName.get(row.raw_name) ?? ""

      const byDate = groupByDate(includedRows)
      const savedDates: string[] = []
      for (const [workDate, dateRows] of byDate) {
        const workerIds = [...new Set(dateRows.map(resolvedWorkerId))].filter(Boolean)
        await api.post<{ data: AttendanceRecord[]; summary: AttendanceSummary }>("/attendance/daily", {
          site_id: siteId,
          work_date: workDate,
          entries: workerIds.map((workerId) => ({ worker_id: workerId, is_present: true })),
        })
        savedDates.push(workDate)
      }

      onSaved(savedDates)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "저장에 실패했습니다.")
    } finally {
      setIsSaving(false)
    }
  }

  const rowsByDate = groupByDate(rows.map((row, index) => ({ ...row, index })))
  const removedByDate = groupByDate(preview.to_be_removed)

  return (
    <div className="panel worker-detail-panel">
      <div className="toolbar">
        <h2>PDF 명단 미리보기</h2>
        <button type="button" onClick={onClose} style={{ marginLeft: "auto" }} disabled={isSaving}>
          닫기
        </button>
      </div>

      {preview.skipped_pages.length > 0 && (
        <p className="hint">
          {preview.skipped_pages.map((p) => `${p.page_number}페이지: ${p.reason}`).join(" · ")} — 건너뛰었습니다.
        </p>
      )}

      {error && <p className="form-error">{error}</p>}

      {rowsByDate.map(([workDate, dateRows]) => (
        <div key={workDate} style={{ marginBottom: 24 }}>
          <h3>{workDate}</h3>
          <table>
            <thead>
              <tr>
                <th>포함</th>
                <th>이름</th>
                <th>공정</th>
                <th>상태</th>
                <th>공정 변경</th>
              </tr>
            </thead>
            <tbody>
              {orderByTradeThenColumn(dateRows).map((row) => {
                const isMismatched =
                  row.matched_worker_id !== null && row.stored_trade !== null && row.stored_trade !== row.trade
                return (
                  <tr key={row.index}>
                    <td>
                      <input
                        type="checkbox"
                        className="checkbox-lg"
                        checked={row.included}
                        onChange={() => toggleIncluded(row.index)}
                      />
                    </td>
                    <td>{row.raw_name}</td>
                    <td>
                      <input
                        value={row.trade}
                        onChange={(e) => editTrade(row.index, e.target.value)}
                        style={{ width: 100 }}
                      />
                    </td>
                    <td>
                      {row.is_new && <span className="badge provisional">신규</span>}
                      {!row.is_new && <span className="badge active">기존: {row.matched_worker_name}</span>}
                      {row.has_duplicate_name && <span className="badge danger">동명이인 있음</span>}
                      {row.site_mismatch && <span className="badge danger">다른 현장 배정중</span>}
                      {isMismatched && <span className="badge provisional">저장된 공정: {row.stored_trade}</span>}
                    </td>
                    <td>
                      {isMismatched && (
                        <label className="hint">
                          <input
                            type="checkbox"
                            checked={row.updateTrade}
                            onChange={() => toggleUpdateTrade(row.index)}
                          />{" "}
                          근로자 공정을 위 값으로 변경
                        </label>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      ))}

      {removedByDate.length > 0 && (
        <div className="panel" style={{ borderColor: "var(--danger)" }}>
          <h3 style={{ marginTop: 0 }}>이번 PDF에 없어서 삭제될 기존 출역 기록</h3>
          {removedByDate.map(([workDate, entries]) => (
            <p key={workDate} className="form-error">
              {workDate}: {entries.map((e) => e.worker_name).join(", ")}
            </p>
          ))}
        </div>
      )}

      <div className="toolbar" style={{ marginTop: 14 }}>
        <button type="button" className="primary" onClick={handleConfirm} disabled={isSaving}>
          확인 및 저장
        </button>
      </div>
    </div>
  )
}
