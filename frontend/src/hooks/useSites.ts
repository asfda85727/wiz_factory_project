import { useEffect, useState } from "react"
import { api } from "../services/apiClient"
import type { CursorPage, Site } from "../types"

interface NewSiteInput {
  name: string
  client_name: string
  start_date: string
}

export function useSites() {
  const [sites, setSites] = useState<Site[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    api
      .get<CursorPage<Site>>("/sites?limit=100")
      .then((page) => {
        if (!cancelled) setSites(page.data)
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const createSite = async (input: NewSiteInput): Promise<Site> => {
    const site = await api.post<Site>("/sites", input)
    setSites((prev) => [...prev, site])
    return site
  }

  const updateSite = async (siteId: string, input: Partial<NewSiteInput>): Promise<Site> => {
    const site = await api.patch<Site>(`/sites/${siteId}`, input)
    setSites((prev) => prev.map((s) => (s.id === siteId ? site : s)))
    return site
  }

  const deleteSite = async (siteId: string): Promise<void> => {
    await api.delete(`/sites/${siteId}`)
    setSites((prev) => prev.filter((s) => s.id !== siteId))
  }

  return { sites, isLoading, createSite, updateSite, deleteSite }
}
