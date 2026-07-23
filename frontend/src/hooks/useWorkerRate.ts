import { useCallback, useEffect, useState } from "react"
import { api } from "../services/apiClient"
import type { CursorPage, WorkerRate } from "../types"

export function useWorkerRate(workerId: string) {
  const [currentRate, setCurrentRate] = useState<WorkerRate | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const reload = useCallback(async () => {
    setIsLoading(true)
    try {
      const page = await api.get<CursorPage<WorkerRate>>(`/workers/${workerId}/rates?limit=1`)
      setCurrentRate(page.data[0] ?? null)
    } finally {
      setIsLoading(false)
    }
  }, [workerId])

  useEffect(() => {
    reload()
  }, [reload])

  return { currentRate, isLoading, reload }
}
