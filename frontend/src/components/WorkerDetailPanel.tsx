import { useEffect, useRef, useState } from "react"
import type { FormEvent } from "react"
import { api, ApiError } from "../services/apiClient"
import { useWorkerRate } from "../hooks/useWorkerRate"
import type { Site, Worker } from "../types"

interface WorkerDetailPanelProps {
  worker: Worker
  sites: Site[]
  existingTrades: string[]
  onUpdated: (worker: Worker) => void
  onDeleted: (workerId: string) => void
  onClose: () => void
}

interface EditableFields {
  name: string
  birth_date: string
  trade: string
  phone: string
  address: string
  bank_name: string
  resident_registration_number: string
  bank_account_number: string
  current_site_id: string
}

function toFormState(worker: Worker): EditableFields {
  return {
    name: worker.name,
    birth_date: worker.birth_date ?? "",
    trade: worker.trade ?? "",
    phone: worker.phone ?? "",
    address: worker.address ?? "",
    bank_name: worker.bank_name ?? "",
    resident_registration_number: "",
    bank_account_number: "",
    current_site_id: worker.current_site_id ?? "",
  }
}

export function WorkerDetailPanel({
  worker,
  sites,
  existingTrades,
  onUpdated,
  onDeleted,
  onClose,
}: WorkerDetailPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null)
  const [form, setForm] = useState<EditableFields>(() => toFormState(worker))
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const { currentRate, isLoading: isRateLoading, reload: reloadRate } = useWorkerRate(worker.id)

  const [rateInput, setRateInput] = useState("")
  const [rateEffectiveFrom, setRateEffectiveFrom] = useState(() => new Date().toISOString().slice(0, 10))
  const [rateError, setRateError] = useState<string | null>(null)
  const [isSavingRate, setIsSavingRate] = useState(false)

  useEffect(() => {
    setRateInput(currentRate ? String(currentRate.daily_rate) : "")
  }, [currentRate])

  useEffect(() => {
    panelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
  }, [worker.id])

  const handleSaveRate = async (event: FormEvent) => {
    event.preventDefault()
    setRateError(null)
    setIsSavingRate(true)
    try {
      const dailyRate = Number(rateInput)
      if (currentRate) {
        await api.patch(`/rates/${currentRate.id}`, { daily_rate: dailyRate })
      } else {
        await api.post(`/workers/${worker.id}/rates`, {
          daily_rate: dailyRate,
          effective_from: rateEffectiveFrom,
        })
      }
      await reloadRate()
    } catch (err) {
      setRateError(err instanceof ApiError ? err.message : "단가 저장에 실패했습니다.")
    } finally {
      setIsSavingRate(false)
    }
  }

  const buildPayload = () => {
    const payload: Record<string, unknown> = {
      name: form.name,
      birth_date: form.birth_date || null,
      trade: form.trade || null,
      phone: form.phone || null,
      address: form.address || null,
      bank_name: form.bank_name || null,
      current_site_id: form.current_site_id || null,
    }
    if (form.resident_registration_number) {
      payload.resident_registration_number = form.resident_registration_number
    }
    if (form.bank_account_number) {
      payload.bank_account_number = form.bank_account_number
    }
    return payload
  }

  const handleSave = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setIsSaving(true)
    try {
      const updated = await api.patch<Worker>(`/workers/${worker.id}`, buildPayload())
      onUpdated(updated)
      setForm(toFormState(updated))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "저장에 실패했습니다.")
    } finally {
      setIsSaving(false)
    }
  }

  const handleActivate = async () => {
    setError(null)
    setIsSaving(true)
    try {
      const updated = await api.patch<Worker>(`/workers/${worker.id}`, { ...buildPayload(), status: "active" })
      onUpdated(updated)
      setForm(toFormState(updated))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "정식 전환에 실패했습니다.")
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm(`${worker.name}님을 삭제할까요? 출역·정산·단가 기록이 모두 함께 삭제되며 되돌릴 수 없습니다.`)) return
    setError(null)
    setIsSaving(true)
    try {
      await api.delete(`/workers/${worker.id}`)
      onDeleted(worker.id)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "삭제에 실패했습니다.")
      setIsSaving(false)
    }
  }

  return (
    <div className="panel" ref={panelRef}>
      <div className="toolbar">
        <h2>{worker.name} 상세</h2>
        <button type="button" onClick={onClose} style={{ marginLeft: "auto" }}>
          닫기
        </button>
      </div>

      <p className="hint">
        주민등록번호: {worker.resident_registration_number_masked ?? "미등록"} · 계좌:{" "}
        {worker.bank_account_masked ?? "미등록"} · 신분증 사본: {worker.id_scan_uploaded ? "있음" : "없음"} ·
        통장 사본: {worker.bankbook_scan_uploaded ? "있음" : "없음"}
      </p>

      <div className="panel">
        <h3>노무비 단가</h3>
        {isRateLoading ? (
          <p className="hint">불러오는 중...</p>
        ) : (
          <form onSubmit={handleSaveRate} className="toolbar">
            <label>
              1일 단가 (원)
              <input
                type="number"
                min={0}
                value={rateInput}
                onChange={(e) => setRateInput(e.target.value)}
                required
              />
            </label>
            {!currentRate && (
              <label>
                적용 시작일
                <input
                  type="date"
                  value={rateEffectiveFrom}
                  onChange={(e) => setRateEffectiveFrom(e.target.value)}
                  required
                />
              </label>
            )}
            <button type="submit" className="primary" disabled={isSavingRate}>
              {currentRate ? "단가 수정" : "단가 등록"}
            </button>
            {currentRate && (
              <span className="hint">{currentRate.effective_from}부터 적용 중</span>
            )}
          </form>
        )}
        {rateError && <p className="form-error">{rateError}</p>}
      </div>

      <form onSubmit={handleSave}>
        <div className="field-grid">
          <label>
            이름
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </label>
          <label>
            생년월일
            <input
              type="date"
              value={form.birth_date}
              onChange={(e) => setForm({ ...form, birth_date: e.target.value })}
            />
          </label>
          <label>
            전화번호
            <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          </label>
          <label>
            주소
            <input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          </label>
          <label>
            거래은행
            <input value={form.bank_name} onChange={(e) => setForm({ ...form, bank_name: e.target.value })} />
          </label>
          <label>
            소속 현장
            <select
              value={form.current_site_id}
              onChange={(e) => setForm({ ...form, current_site_id: e.target.value })}
            >
              <option value="">미배정</option>
              {sites.map((site) => (
                <option key={site.id} value={site.id}>
                  {site.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            공정
            <input
              list="trade-suggestions"
              value={form.trade}
              onChange={(e) => setForm({ ...form, trade: e.target.value })}
              placeholder="예: 철거"
            />
            <datalist id="trade-suggestions">
              {existingTrades.map((trade) => (
                <option key={trade} value={trade} />
              ))}
            </datalist>
          </label>
          <label>
            주민등록번호 (변경 시에만 입력)
            <input
              placeholder="850315-1234567"
              value={form.resident_registration_number}
              onChange={(e) => setForm({ ...form, resident_registration_number: e.target.value })}
            />
          </label>
          <label>
            계좌번호 (변경 시에만 입력)
            <input
              value={form.bank_account_number}
              onChange={(e) => setForm({ ...form, bank_account_number: e.target.value })}
            />
          </label>
        </div>

        {error && <p className="form-error">{error}</p>}

        <div className="toolbar">
          <button type="submit" className="primary" disabled={isSaving}>
            저장
          </button>
          {worker.status === "provisional" && (
            <button type="button" onClick={handleActivate} disabled={isSaving}>
              정식 전환
            </button>
          )}
          <button type="button" onClick={handleDelete} disabled={isSaving} style={{ marginLeft: "auto" }}>
            삭제
          </button>
        </div>
      </form>
    </div>
  )
}
