import { useState } from "react"
import type { FormEvent } from "react"
import { ApiError } from "../services/apiClient"
import { useSites } from "../hooks/useSites"
import type { Site } from "../types"

export function SitesPage() {
  const { sites, isLoading, createSite, updateSite, deleteSite } = useSites()
  const [name, setName] = useState("")
  const [clientName, setClientName] = useState("")
  const [startDate, setStartDate] = useState("")
  const [createError, setCreateError] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)

  const [selectedSiteId, setSelectedSiteId] = useState<string | null>(null)
  const [editName, setEditName] = useState("")
  const [editClientName, setEditClientName] = useState("")
  const [editError, setEditError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  const selectedSite = sites.find((site) => site.id === selectedSiteId) ?? null

  const handleCreate = async (event: FormEvent) => {
    event.preventDefault()
    setCreateError(null)
    setIsCreating(true)
    try {
      await createSite({ name, client_name: clientName, start_date: startDate })
      setName("")
      setClientName("")
      setStartDate("")
    } catch (err) {
      setCreateError(err instanceof ApiError ? err.message : "현장 생성에 실패했습니다.")
    } finally {
      setIsCreating(false)
    }
  }

  const handleSelect = (site: Site) => {
    setSelectedSiteId(site.id)
    setEditName(site.name)
    setEditClientName(site.client_name)
    setEditError(null)
  }

  const handleSave = async (event: FormEvent) => {
    event.preventDefault()
    if (!selectedSiteId) return
    setEditError(null)
    setIsSaving(true)
    try {
      await updateSite(selectedSiteId, { name: editName, client_name: editClientName })
    } catch (err) {
      setEditError(err instanceof ApiError ? err.message : "수정에 실패했습니다.")
    } finally {
      setIsSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedSiteId) return
    if (!confirm("이 현장을 삭제할까요? 되돌릴 수 없습니다.")) return
    setEditError(null)
    setIsSaving(true)
    try {
      await deleteSite(selectedSiteId)
      setSelectedSiteId(null)
    } catch (err) {
      setEditError(err instanceof ApiError ? err.message : "삭제에 실패했습니다.")
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div>
      <h1>현장 관리</h1>

      <div className="panel">
        <h2>신규 현장 추가</h2>
        <form onSubmit={handleCreate} className="toolbar">
          <label>
            현장명
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <label>
            발주처
            <input value={clientName} onChange={(e) => setClientName(e.target.value)} required />
          </label>
          <label>
            착공일
            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
          </label>
          <button type="submit" className="primary" disabled={isCreating}>
            추가
          </button>
        </form>
        {createError && <p className="form-error">{createError}</p>}
      </div>

      <div className="panel">
        {isLoading ? (
          <p className="hint">불러오는 중...</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>현장명</th>
                <th>발주처</th>
              </tr>
            </thead>
            <tbody>
              {sites.map((site) => (
                <tr key={site.id} className="selectable" onClick={() => handleSelect(site)}>
                  <td>{site.name}</td>
                  <td>{site.client_name}</td>
                </tr>
              ))}
              {sites.length === 0 && (
                <tr>
                  <td colSpan={2} className="hint">
                    등록된 현장이 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {selectedSite && (
        <div className="panel worker-detail-panel">
          <div className="toolbar">
            <h2>{selectedSite.name} 수정</h2>
            <button type="button" onClick={() => setSelectedSiteId(null)} style={{ marginLeft: "auto" }}>
              닫기
            </button>
          </div>
          <form onSubmit={handleSave} className="toolbar">
            <label>
              현장명
              <input value={editName} onChange={(e) => setEditName(e.target.value)} required />
            </label>
            <label>
              발주처
              <input value={editClientName} onChange={(e) => setEditClientName(e.target.value)} required />
            </label>
            <button type="submit" className="primary" disabled={isSaving}>
              저장
            </button>
            <button type="button" onClick={handleDelete} disabled={isSaving}>
              삭제
            </button>
          </form>
          {editError && <p className="form-error">{editError}</p>}
        </div>
      )}
    </div>
  )
}
