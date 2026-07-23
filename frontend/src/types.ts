export type WorkerStatus = "provisional" | "active"

export interface Worker {
  id: string
  name: string
  birth_date: string | null
  status: WorkerStatus
  trade: string | null
  phone: string | null
  address: string | null
  bank_name: string | null
  resident_registration_number_masked: string | null
  bank_account_masked: string | null
  id_scan_uploaded: boolean
  bankbook_scan_uploaded: boolean
  current_site_id: string | null
  created_at: string
}

export interface WorkerRate {
  id: string
  worker_id: string
  daily_rate: number
  effective_from: string
  effective_to: string | null
  created_by: string
  created_at: string
}

export interface Site {
  id: string
  name: string
  client_name: string
  start_date: string
  created_at: string
}

export interface AttendanceRecord {
  id: string
  worker_id: string
  worker_name: string
  site_id: string
  work_date: string
  trade: string | null
  is_present: boolean
  recorded_by: string
  recorded_at: string
  updated_at: string
}

export interface AttendanceSummary {
  total_count: number
  present_count: number
  by_trade: Record<string, number>
}

export interface PayrollResult {
  id: string
  worker_id: string
  worker_name: string
  trade: string | null
  target_month: string
  work_days: number
  gross_pay: number
  income_tax: number
  local_tax: number
  employment_insurance: number
  national_pension: number
  health_insurance: number
  long_term_care: number
  net_pay: number
  calc_status: "ok" | "held"
  created_at: string
  updated_at: string
}

export interface CursorPage<T> {
  data: T[]
  pagination: { next_cursor: string | null; has_more: boolean }
}

export interface WorkerAttendanceDay {
  work_date: string
  site_id: string
  site_name: string
  trade: string | null
  is_present: boolean
}

export interface WorkerMonthlyAttendance {
  worker_id: string
  worker_name: string
  present_days: number
  data: WorkerAttendanceDay[]
}
