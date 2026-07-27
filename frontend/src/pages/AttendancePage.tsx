import { useEffect, useRef, useState } from "react"
import { api, ApiError } from "../services/apiClient"
import { useSites } from "../hooks/useSites"
import { AttendancePdfImportPanel } from "../components/AttendancePdfImportPanel"
import type { AttendancePdfPreviewResponse, AttendanceRecord, AttendanceSummary, CursorPage, Worker } from "../types"

interface EntryRow {
  worker_id: string
  worker_name: string
  trade: string | null
  is_present: boolean
}

const UNCLASSIFIED_TRADE = "미분류"

function groupByTrade(entries: EntryRow[]): [string, EntryRow[]][] {
  const groups = new Map<string, EntryRow[]>()
  for (const entry of entries) {
    const key = entry.trade ?? UNCLASSIFIED_TRADE
    const existing = groups.get(key)
    if (existing) {
      existing.push(entry)
    } else {
      groups.set(key, [entry])
    }
  }
  return [...groups.entries()].sort(([a], [b]) => {
    if (a === UNCLASSIFIED_TRADE) return 1
    if (b === UNCLASSIFIED_TRADE) return -1
    return a.localeCompare(b)
  })
}

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

export function AttendancePage() {
  const { sites } = useSites()
  const [siteId, setSiteId] = useState("")
  const [workDate, setWorkDate] = useState(today())
  const [entries, setEntries] = useState<EntryRow[]>([])
  const [summary, setSummary] = useState<AttendanceSummary | null>(null)
  const [workers, setWorkers] = useState<Worker[]>([])
  const [addWorkerId, setAddWorkerId] = useState("")
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [pdfPreview, setPdfPreview] = useState<AttendancePdfPreviewResponse | null>(null)
  const [isUploadingPdf, setIsUploadingPdf] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    api.get<CursorPage<Worker>>("/workers?limit=100").then((page) => setWorkers(page.data))
  }, [])

  useEffect(() => {
    if (!siteId) {
      setEntries([])
      setSummary(null)
      return
    }
    loadDaily()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [siteId, workDate])

  const loadDaily = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await api.get<{ data: AttendanceRecord[]; summary: AttendanceSummary }>(
        `/attendance/daily?date=${workDate}&site_id=${siteId}`,
      )
      setEntries(
        response.data.map((record) => ({
          worker_id: record.worker_id,
          worker_name: record.worker_name,
          trade: record.trade,
          is_present: record.is_present,
        })),
      )
      setSummary(response.summary)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "출역 명단을 불러오지 못했습니다.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleAddWorker = () => {
    if (!addWorkerId || entries.some((entry) => entry.worker_id === addWorkerId)) return
    const worker = workers.find((w) => w.id === addWorkerId)
    setEntries((prev) => [
      ...prev,
      { worker_id: addWorkerId, worker_name: worker?.name ?? "", trade: worker?.trade ?? null, is_present: true },
    ])
    setAddWorkerId("")
  }

  const removeEntry = (workerId: string) => {
    setEntries((prev) => prev.filter((entry) => entry.worker_id !== workerId))
  }

  const handleSave = async () => {
    if (!siteId) return
    setIsSaving(true)
    setError(null)
    setMessage(null)
    try {
      const response = await api.post<{ data: AttendanceRecord[]; summary: AttendanceSummary }>(
        "/attendance/daily",
        {
          site_id: siteId,
          work_date: workDate,
          entries: entries.map((entry) => ({
            worker_id: entry.worker_id,
            is_present: entry.is_present,
          })),
        },
      )
      setSummary(response.summary)
      setMessage("저장되었습니다.")
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "저장에 실패했습니다.")
    } finally {
      setIsSaving(false)
    }
  }

  const handleCopyPrevious = async () => {
    if (!siteId) return
    setIsSaving(true)
    setError(null)
    setMessage(null)
    try {
      const response = await api.post<{ data: AttendanceRecord[]; summary: AttendanceSummary }>(
        `/attendance/copy-previous?date=${workDate}&site_id=${siteId}`,
      )
      setEntries(
        response.data.map((record) => ({
          worker_id: record.worker_id,
          worker_name: record.worker_name,
          trade: record.trade,
          is_present: record.is_present,
        })),
      )
      setSummary(response.summary)
      setMessage("전일 명단을 복사했습니다.")
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "전일 명단이 없습니다.")
    } finally {
      setIsSaving(false)
    }
  }

  const handlePdfFileSelected = async (file: File) => {
    if (!siteId) return
    setIsUploadingPdf(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append("site_id", siteId)
      formData.append("file", file)
      const response = await api.postForm<AttendancePdfPreviewResponse>("/attendance/pdf-preview", formData)
      setPdfPreview(response)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "PDF를 읽지 못했습니다.")
    } finally {
      setIsUploadingPdf(false)
      if (fileInputRef.current) fileInputRef.current.value = ""
    }
  }

  const handlePdfSaved = (savedDates: string[]) => {
    setPdfPreview(null)
    setMessage("PDF 명단을 반영했습니다.")
    if (savedDates.includes(workDate)) {
      loadDaily()
    }
  }

  const addableWorkers = workers.filter(
    (worker) => worker.current_site_id === siteId && !entries.some((entry) => entry.worker_id === worker.id),
  )

  return (
    <div>
      <h1>일일 출역 입력</h1>

      <div className="panel">
        <div className="toolbar">
          <label>
            현장
            <select value={siteId} onChange={(e) => setSiteId(e.target.value)}>
              <option value="">현장 선택</option>
              {sites.map((site) => (
                <option key={site.id} value={site.id}>
                  {site.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            날짜
            <input type="date" value={workDate} onChange={(e) => setWorkDate(e.target.value)} />
          </label>
          <button type="button" onClick={handleCopyPrevious} disabled={!siteId || isSaving}>
            전일 명단 복사
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            style={{ display: "none" }}
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) handlePdfFileSelected(file)
            }}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={!siteId || isUploadingPdf}
          >
            {isUploadingPdf ? "PDF 읽는 중..." : "PDF로 명단 가져오기"}
          </button>
        </div>

        {summary && (
          <p className="hint">
            전체 {summary.total_count}명 · 출역 {summary.present_count}명 ·{" "}
            {Object.entries(summary.by_trade)
              .map(([trade, count]) => `${trade} ${count}명`)
              .join(", ")}
          </p>
        )}

        {error && <p className="form-error">{error}</p>}
        {message && <p className="hint">{message}</p>}

        {!siteId ? (
          <p className="hint">현장을 먼저 선택하세요.</p>
        ) : isLoading ? (
          <p className="hint">불러오는 중...</p>
        ) : (
          <>
            {entries.length === 0 ? (
              <p className="hint">추가된 근로자가 없습니다.</p>
            ) : (
              <div
                style={{ display: "flex", gap: 16, flexWrap: "wrap", alignItems: "flex-start", overflowX: "auto" }}
              >
                {groupByTrade(entries).map(([trade, rows]) => (
                  <div key={trade} className="panel" style={{ minWidth: 160, flex: "0 0 auto" }}>
                    <h3 style={{ marginTop: 0 }}>
                      {trade} <span className="hint">({rows.length}명)</span>
                    </h3>
                    <table>
                      <tbody>
                        {rows.map((entry) => (
                          <tr key={entry.worker_id}>
                            <td>{entry.worker_name}</td>
                            <td>
                              <button type="button" onClick={() => removeEntry(entry.worker_id)}>
                                제거
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ))}
              </div>
            )}

            <div className="toolbar" style={{ marginTop: 14 }}>
              <label>
                근로자 추가 (이 현장 소속만 표시)
                <select value={addWorkerId} onChange={(e) => setAddWorkerId(e.target.value)}>
                  <option value="">선택</option>
                  {addableWorkers.map((worker) => (
                    <option key={worker.id} value={worker.id}>
                      {worker.name}
                    </option>
                  ))}
                </select>
              </label>
              <button type="button" onClick={handleAddWorker} disabled={!addWorkerId}>
                추가
              </button>
              <button
                type="button"
                className="primary"
                onClick={handleSave}
                disabled={isSaving}
                style={{ marginLeft: "auto" }}
              >
                저장
              </button>
            </div>
            {addableWorkers.length === 0 && (
              <p className="hint">
                이 현장에 소속된 근로자 중 추가할 수 있는 사람이 없습니다 — 근로자 마스터에서 이 현장으로
                배정된 근로자가 있는지 확인하세요.
              </p>
            )}
          </>
        )}
      </div>

      {pdfPreview && (
        <AttendancePdfImportPanel
          siteId={siteId}
          preview={pdfPreview}
          onClose={() => setPdfPreview(null)}
          onSaved={handlePdfSaved}
        />
      )}
    </div>
  )
}
