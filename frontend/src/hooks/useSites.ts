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

  return { sites, isLoading, createSite }
}
