import { useEffect, useMemo, useRef, useState } from "react"
import type { KeyboardEvent, MouseEvent } from "react"
import { api, ApiError } from "../services/apiClient"
import { WorkerMonthlyDetail } from "../components/WorkerMonthlyDetail"
import type { PayrollResult } from "../types"

interface SelectableCard {
  key: string
  name: string
  meta: string
  net?: number
}

// 클릭은 카드 하나 토글, 드래그는 처음 카드의 반대 상태로 지나가는 카드 전부를 한 번에 토글
// (스프레드시트 셀 드래그 선택과 같은 감각 — 체크박스를 하나씩 누르지 않아도 되게).
function CardToggleGroup({
  items,
  selected,
  onChange,
}: {
  items: SelectableCard[]
  selected: Set<string>
  onChange: (next: Set<string>) => void
}) {
  const dragModeRef = useRef<boolean | null>(null)

  useEffect(() => {
    const endDrag = () => {
      dragModeRef.current = null
    }
    window.addEventListener("mouseup", endDrag)
    return () => window.removeEventListener("mouseup", endDrag)
  }, [])

  const applyCard = (key: string, addMode: boolean) => {
    const next = new Set(selected)
    if (addMode) next.add(key)
    else next.delete(key)
    onChange(next)
  }

  const handleMouseDown = (key: string) => (event: MouseEvent) => {
    event.preventDefault()
    const addMode = !selected.has(key)
    dragModeRef.current = addMode
    applyCard(key, addMode)
  }

  const handleMouseEnter = (key: string) => () => {
    if (dragModeRef.current !== null) applyCard(key, dragModeRef.current)
  }

  const handleKeyDown = (key: string) => (event: KeyboardEvent) => {
    if (event.key === " " || event.key === "Enter") {
      event.preventDefault()
      applyCard(key, !selected.has(key))
    }
  }

  return (
    <div className="trade-cards" style={{ userSelect: "none" }}>
      {items.map((item) => (
        <div
          key={item.key}
          role="checkbox"
          aria-checked={selected.has(item.key)}
          tabIndex={0}
          className={`trade-card ${selected.has(item.key) ? "active" : ""}`}
          onMouseDown={handleMouseDown(item.key)}
          onMouseEnter={handleMouseEnter(item.key)}
          onKeyDown={handleKeyDown(item.key)}
        >
          <span className="trade-card-name">{item.name}</span>
          <span className="trade-card-meta">{item.meta}</span>
          {item.net !== undefined && <span className="trade-card-net">{item.net.toLocaleString()}원</span>}
        </div>
      ))}
    </div>
  )
}

function currentMonth(): string {
  return new Date().toISOString().slice(0, 7)
}

const MAX_MONTHS = 24

// "YYYY-MM" 시작~종료(양끝 포함)를 월 목록으로 편다. 시작이 종료보다 뒤면 빈 배열.
function monthsInRange(from: string, to: string): string[] {
  const [fromYear, fromMonthNum] = from.split("-").map(Number)
  const [toYear, toMonthNum] = to.split("-").map(Number)
  const start = fromYear * 12 + (fromMonthNum - 1)
  const end = toYear * 12 + (toMonthNum - 1)
  if (start > end) return []

  const months: string[] = []
  for (let cursor = start; cursor <= end; cursor++) {
    const year = Math.floor(cursor / 12)
    const monthNum = (cursor % 12) + 1
    months.push(`${year}-${String(monthNum).padStart(2, "0")}`)
  }
  return months
}

const CALC_STATUS_LABEL: Record<PayrollResult["calc_status"], string> = {
  ok: "완료",
  held: "보류",
}

const UNCLASSIFIED = "미분류"
const UNASSIGNED_SITE = "__unassigned__"

interface TradeGroup {
  trade: string
  count: number
  days: number
  net: number
}

interface SiteGroup {
  key: string
  name: string
  count: number
}

export function PayrollPage() {
  const [fromMonth, setFromMonth] = useState(currentMonth())
  const [toMonth, setToMonth] = useState(currentMonth())
  const [results, setResults] = useState<PayrollResult[]>([])
  const [selectedTrades, setSelectedTrades] = useState<Set<string>>(new Set())
  const [selectedSites, setSelectedSites] = useState<Set<string>>(new Set())
  const [search, setSearch] = useState("")
  const [selectedWorker, setSelectedWorker] = useState<{ id: string; name: string; month: string } | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isRecalculating, setIsRecalculating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadPayroll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fromMonth, toMonth])

  // 기간이 유효하지 않으면 에러 메시지를 세팅하고 조회할 월 목록을 반환하지 않는다(공통 가드).
  const resolveMonths = (): string[] | null => {
    const months = monthsInRange(fromMonth, toMonth)
    if (months.length === 0) {
      setError("기간이 올바르지 않습니다 — 시작월이 종료월보다 뒤입니다.")
      return null
    }
    if (months.length > MAX_MONTHS) {
      setError(`조회 기간은 최대 ${MAX_MONTHS}개월까지 가능합니다.`)
      return null
    }
    return months
  }

  const loadPayroll = async () => {
    setError(null)
    setSelectedTrades(new Set())
    setSelectedSites(new Set())
    setSelectedWorker(null)

    const months = resolveMonths()
    if (months === null) {
      setResults([])
      return
    }

    setIsLoading(true)
    try {
      const responses = await Promise.all(
        months.map((month) => api.get<{ data: PayrollResult[] }>(`/payroll?month=${month}`)),
      )
      setResults(responses.flatMap((response) => response.data))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "정산 결과를 불러오지 못했습니다.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleRecalculate = async () => {
    setError(null)
    setSelectedWorker(null)

    const months = resolveMonths()
    if (months === null) return

    setIsRecalculating(true)
    try {
      const responses = await Promise.all(
        months.map((month) => api.post<{ data: PayrollResult[] }>(`/payroll/recalculate?month=${month}`)),
      )
      setResults(responses.flatMap((response) => response.data))
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

  const siteGroups = useMemo<SiteGroup[]>(() => {
    const map = new Map<string, SiteGroup>()
    for (const row of results) {
      const key = row.site_id ?? UNASSIGNED_SITE
      const name = row.site_name ?? "현장 미배정"
      const group = map.get(key) ?? { key, name, count: 0 }
      group.count += 1
      map.set(key, group)
    }
    return [...map.values()].sort((a, b) => a.name.localeCompare(b.name))
  }, [results])

  const trimmedSearch = search.trim().toLowerCase()
  const filtered = results.filter((row) => {
    const tradeMatches = selectedTrades.size === 0 || selectedTrades.has(row.trade ?? UNCLASSIFIED)
    const siteMatches = selectedSites.size === 0 || selectedSites.has(row.site_id ?? UNASSIGNED_SITE)
    const nameMatches = trimmedSearch === "" || row.worker_name.toLowerCase().includes(trimmedSearch)
    return tradeMatches && siteMatches && nameMatches
  })
  // 공정 → 이름 → 월 순. 한 근로자의 여러 달이 인접해 시간순으로 이어지도록 마지막에 월로 정렬한다.
  const sortedFiltered = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const tradeA = a.trade ?? UNCLASSIFIED
      const tradeB = b.trade ?? UNCLASSIFIED
      if (tradeA !== tradeB) {
        if (tradeA === UNCLASSIFIED) return 1
        if (tradeB === UNCLASSIFIED) return -1
        return tradeA.localeCompare(tradeB)
      }
      if (a.worker_name !== b.worker_name) return a.worker_name.localeCompare(b.worker_name)
      return a.target_month.localeCompare(b.target_month)
    })
  }, [filtered])
  const totalNetPay = filtered.reduce((sum, row) => sum + row.net_pay, 0)

  return (
    <div>
      <h1>명세서</h1>

      <div className="panel">
        <div className="toolbar">
          <label>
            시작월
            <input type="month" value={fromMonth} onChange={(e) => setFromMonth(e.target.value)} />
          </label>
          <label>
            종료월
            <input type="month" value={toMonth} onChange={(e) => setToMonth(e.target.value)} />
          </label>
          <label>
            이름 검색
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="근로자 이름"
            />
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
            <p className="hint">공정 — 클릭하거나 눌러서 드래그하면 여러 개 한 번에 선택됩니다(전체 미선택 시 전체 표시)</p>
            <CardToggleGroup
              items={tradeGroups.map((g) => ({
                key: g.trade,
                name: g.trade,
                meta: `${g.count}명 · ${g.days}일`,
                net: g.net,
              }))}
              selected={selectedTrades}
              onChange={setSelectedTrades}
            />

            <p className="hint">현장</p>
            <CardToggleGroup
              items={siteGroups.map((g) => ({ key: g.key, name: g.name, meta: `${g.count}명` }))}
              selected={selectedSites}
              onChange={setSelectedSites}
            />
          </>
        )}

        {isLoading ? (
          <p className="hint">불러오는 중...</p>
        ) : (
          <table className="numeric-table">
            <thead>
              <tr>
                <th>월</th>
                <th>이름</th>
                <th>공정</th>
                <th>현장</th>
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
              {sortedFiltered.map((row) => (
                <tr
                  key={row.id}
                  className="selectable"
                  onClick={() =>
                    setSelectedWorker({
                      id: row.worker_id,
                      name: row.worker_name,
                      month: row.target_month.slice(0, 7),
                    })
                  }
                >
                  <td>{row.target_month.slice(0, 7)}</td>
                  <td>{row.worker_name}</td>
                  <td>{row.trade ?? "-"}</td>
                  <td>{row.site_name ?? "-"}</td>
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
                  <td colSpan={14} className="hint">
                    {results.length === 0
                      ? "계산된 정산 결과가 없습니다. 재계산을 눌러주세요."
                      : "조건에 맞는 근로자가 없습니다."}
                  </td>
                </tr>
              )}
            </tbody>
            {filtered.length > 0 && (
              <tfoot>
                <tr>
                  <td colSpan={12}>합계</td>
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
          month={selectedWorker.month}
          onClose={() => setSelectedWorker(null)}
        />
      )}
    </div>
  )
}
