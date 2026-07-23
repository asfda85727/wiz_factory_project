import { useEffect, useMemo, useState } from "react"
import { api, ApiError } from "../services/apiClient"
import { WorkerMonthlyDetail } from "../components/WorkerMonthlyDetail"
import type { PayrollResult } from "../types"

function currentMonth(): string {
  return new Date().toISOString().slice(0, 7)
}

const CALC_STATUS_LABEL: Record<PayrollResult["calc_status"], string> = {
  ok: "완료",
  held: "보류",
}

const UNCLASSIFIED = "미분류"

interface TradeGroup {
  trade: string
  count: number
  days: number
  net: number
}

export function PayrollPage() {
  const [month, setMonth] = useState(currentMonth())
  const [results, setResults] = useState<PayrollResult[]>([])
  const [selectedTrade, setSelectedTrade] = useState<string | null>(null)
  const [selectedWorker, setSelectedWorker] = useState<{ id: string; name: string } | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isRecalculating, setIsRecalculating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadPayroll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [month])

  const loadPayroll = async () => {
    setIsLoading(true)
    setError(null)
    setSelectedTrade(null)
    setSelectedWorker(null)
    try {
      const response = await api.get<{ data: PayrollResult[] }>(`/payroll?month=${month}`)
      setResults(response.data)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "정산 결과를 불러오지 못했습니다.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleRecalculate = async () => {
    setIsRecalculating(true)
    setError(null)
    setSelectedWorker(null)
    try {
      const response = await api.post<{ data: PayrollResult[] }>(`/payroll/recalculate?month=${month}`)
      setResults(response.data)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "재계산에 실패했습니다.")
    } finally {
      setIsRecalculating(false)
    }
  }

  const tradeGroups = useMemo<TradeGroup[]>(() => {
    const map = new Map<string, TradeGroup>()
    for (const row of results) {
      const key = row.trade ?? UNCLASSIFIED
      const group = map.get(key) ?? { trade: key, count: 0, days: 0, net: 0 }
      group.count += 1
      group.days += row.work_days
      group.net += row.net_pay
      map.set(key, group)
    }
    return [...map.values()].sort((a, b) => a.trade.localeCompare(b.trade))
  }, [results])

  const filtered = selectedTrade
    ? results.filter((row) => (row.trade ?? UNCLASSIFIED) === selectedTrade)
    : results
  const totalNetPay = filtered.reduce((sum, row) => sum + row.net_pay, 0)

  return (
    <div>
      <h1>명세서</h1>

      <div className="panel">
        <div className="toolbar">
          <label>
            대상월
            <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} />
          </label>
          <button type="button" className="primary" onClick={handleRecalculate} disabled={isRecalculating}>
            {isRecalculating ? "재계산 중..." : "재계산"}
          </button>
        </div>

        <p className="hint">
          실제 임금 명세서(원청·타 사업장 근무 반영 등)와 차이가 날 수 있는 국세청 기준 예상치입니다.
        </p>

        {error && <p className="form-error">{error}</p>}

        {!isLoading && results.length > 0 && (
          <>
            <div className="trade-cards">
              <button
                type="button"
                className={`trade-card ${selectedTrade === null ? "active" : ""}`}
                onClick={() => setSelectedTrade(null)}
              >
                <span className="trade-card-name">전체 공정</span>
                <span className="trade-card-meta">{results.length}명</span>
              </button>
              {tradeGroups.map((group) => (
                <button
                  key={group.trade}
                  type="button"
                  className={`trade-card ${selectedTrade === group.trade ? "active" : ""}`}
                  onClick={() => setSelectedTrade(group.trade)}
                >
                  <span className="trade-card-name">{group.trade}</span>
                  <span className="trade-card-meta">
                    {group.count}명 · {group.days}일
                  </span>
                  <span className="trade-card-net">{group.net.toLocaleString()}원</span>
                </button>
              ))}
            </div>
          </>
        )}

        {isLoading ? (
          <p className="hint">불러오는 중...</p>
        ) : (
          <table className="numeric-table">
            <thead>
              <tr>
                <th>이름</th>
                <th>공정</th>
                <th>출역일</th>
                <th>지급총액</th>
                <th>소득세</th>
                <th>지방세</th>
                <th>고용보험</th>
                <th>국민연금</th>
                <th>건강보험</th>
                <th>장기요양</th>
                <th>차감지급액</th>
                <th>상태</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => (
                <tr
                  key={row.id}
                  className="selectable"
                  onClick={() => setSelectedWorker({ id: row.worker_id, name: row.worker_name })}
                >
                  <td>{row.worker_name}</td>
                  <td>{row.trade ?? "-"}</td>
                  <td>{row.work_days}</td>
                  <td>{row.gross_pay.toLocaleString()}</td>
                  <td>{row.income_tax.toLocaleString()}</td>
                  <td>{row.local_tax.toLocaleString()}</td>
                  <td>{row.employment_insurance.toLocaleString()}</td>
                  <td>{row.national_pension.toLocaleString()}</td>
                  <td>{row.health_insurance.toLocaleString()}</td>
                  <td>{row.long_term_care.toLocaleString()}</td>
                  <td>{row.net_pay.toLocaleString()}</td>
                  <td>
                    <span className={`badge ${row.calc_status}`}>{CALC_STATUS_LABEL[row.calc_status]}</span>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={12} className="hint">
                    계산된 정산 결과가 없습니다. 재계산을 눌러주세요.
                  </td>
                </tr>
              )}
            </tbody>
            {filtered.length > 0 && (
              <tfoot>
                <tr>
                  <td colSpan={10}>합계</td>
                  <td>{totalNetPay.toLocaleString()}</td>
                  <td></td>
                </tr>
              </tfoot>
            )}
          </table>
        )}
      </div>

      {selectedWorker && (
        <WorkerMonthlyDetail
          workerId={selectedWorker.id}
          workerName={selectedWorker.name}
          month={month}
          onClose={() => setSelectedWorker(null)}
        />
      )}
    </div>
  )
}
