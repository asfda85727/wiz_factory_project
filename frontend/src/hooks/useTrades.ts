import { useEffect, useState } from "react"
import { api } from "../services/apiClient"

export function useTrades(siteId: string | null) {
  const [trades, setTrades] = useState<string[]>([])

  useEffect(() => {
    if (!siteId) {
      setTrades([])
      return
    }
    let cancelled = false
    api
      .get<{ data: string[] }>(`/sites/${siteId}/trades`)
      .then((response) => {
        if (!cancelled) setTrades(response.data)
      })
      .catch(() => {
        if (!cancelled) setTrades([])
      })
    return () => {
      cancelled = true
    }
  }, [siteId])

  return { trades }
}
