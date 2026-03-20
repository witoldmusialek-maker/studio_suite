import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Alert,
  Autocomplete,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'

import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { useBooking } from '../contexts/BookingContext'

type StatsResponse = {
  salons: number
  clients: number
  appointments: number
  planned_appointments: number
  completed_appointments: number
  available_staff: number
  appointments_in_progress: number
  revenue_today: number
}

type AppointmentRow = {
  id: number
  salon_id: number
  client_id: number
  start_at: string
  end_at: string
  status: string
  resources: number[]
  services: number[]
  bundle_id?: number | null
  total_price_snapshot: number
}

type SessionRow = {
  id: number
  user_id: number
  username: string
  role: string
  salon_id?: number | null
  salon_name?: string | null
  online_since: string
  last_seen: string
  online_seconds: number
  ip_address?: string | null
  is_active?: boolean
}

type SalonStaffRow = {
  id: number
  display_name: string
  role_code?: string | null
  can_be_booked: boolean
  is_active: boolean
}

type StockLocationRow = {
  id: number
  salon_id: number
  code: string
  name: string
  location_type: string
  is_active: boolean
}

type StocktakeCandidate = {
  product_id: number
  product_code: string
  product_name: string
  unit: string
  measurement_mode: 'PCS' | 'WEIGHT'
  dose_weight?: number | null
  package_weight?: number | null
}

type StocktakeLineDraft = {
  candidate: StocktakeCandidate | null
  countedUnits: string
  measuredGrossWeight: string
}

type InventoryIssueLineRow = {
  id: number
  quantity_actual?: number | null
  total_cost?: number | null
}

type InventoryIssueRow = {
  id: number
  issue_time: string
  status: string
  appointment_id?: number | null
  service_id?: number | null
  staff_id?: number | null
  lines: InventoryIssueLineRow[]
}

type VipCardInfo = {
  id: number
  client_id: number
  discount_pct: number
  expiry?: string | null
}

type InvitationInfo = {
  id: number
  client_id: number
  service_id: number
  expiry?: string | null
  used_on_payment_id?: number | null
}

const STATUS_COLOR: Record<string, 'default' | 'primary' | 'success' | 'error'> = {
  planned: 'default',
  started: 'primary',
  in_progress: 'primary',
  done: 'success',
  completed: 'success',
  cancelled: 'error',
  no_show: 'error',
}

const startOfDay = (base: Date) => new Date(base.getFullYear(), base.getMonth(), base.getDate(), 0, 0, 0, 0)
const endOfDay = (base: Date) => new Date(base.getFullYear(), base.getMonth(), base.getDate(), 23, 59, 59, 999)
const SALON_ORDER_CODES = ['05', '12', '02', '07'] as const

const getSalonOrderRank = (salon: { code?: string | null; name: string }) => {
  const code = (salon.code || '').trim()
  const idx = SALON_ORDER_CODES.indexOf(code as (typeof SALON_ORDER_CODES)[number])
  if (idx >= 0) return idx
  const normalized = salon.name.toLowerCase()
  if (normalized.includes('pulaw')) return 0
  if (normalized.includes('kras')) return 1
  if (normalized.includes('odyn')) return 2
  return 99
}

const sortSalonsPreferred = <T extends { code?: string | null; name: string }>(rows: T[]) =>
  [...rows].sort((left, right) => {
    const rankDiff = getSalonOrderRank(left) - getSalonOrderRank(right)
    if (rankDiff !== 0) return rankDiff
    return left.name.localeCompare(right.name, 'pl')
  })

const toDateTimeLocalValue = (value: Date) => {
  const copy = new Date(value.getTime() - value.getTimezoneOffset() * 60000)
  return copy.toISOString().slice(0, 16)
}

const toApiLocalDateTime = (value: Date) => `${toDateTimeLocalValue(value)}:00`

const nextHalfHour = (base = new Date()) => {
  const copy = new Date(base)
  copy.setSeconds(0, 0)
  const minutes = copy.getMinutes()
  const add = minutes === 0 || minutes === 30 ? 0 : minutes < 30 ? 30 - minutes : 60 - minutes
  copy.setMinutes(minutes + add)
  return copy
}

const WALK_IN_MAX_LEAD_MINUTES = 90

const DashboardPage = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { salons, clients, resources, services, bundles, appointments, addClient, addAppointment, reload } = useBooking()

  const [selectedSalonId, setSelectedSalonId] = useState<number | ''>('')
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [todayAppointments, setTodayAppointments] = useState<AppointmentRow[]>([])
  const [activeSessions, setActiveSessions] = useState<SessionRow[]>([])
  const [salonStaff, setSalonStaff] = useState<SalonStaffRow[]>([])
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [isSavingWalkIn, setIsSavingWalkIn] = useState(false)
  const [walkInClientId, setWalkInClientId] = useState<number | ''>('')
  const [walkInClientName, setWalkInClientName] = useState('')
  const [walkInClientPhone, setWalkInClientPhone] = useState('')
  const [walkInVipLabel, setWalkInVipLabel] = useState('')
  const [walkInPromoLabels, setWalkInPromoLabels] = useState<string[]>([])
  const [walkInBundleId, setWalkInBundleId] = useState<number | ''>('')
  const [walkInStaffId, setWalkInStaffId] = useState<number | ''>('')
  const [walkInStartAt, setWalkInStartAt] = useState(toDateTimeLocalValue(nextHalfHour()))
  const [stocktakeDialogOpen, setStocktakeDialogOpen] = useState(false)
  const [stocktakeSaving, setStocktakeSaving] = useState(false)
  const [stocktakeLocationId, setStocktakeLocationId] = useState<number | ''>('')
  const [stocktakeLocations, setStocktakeLocations] = useState<StockLocationRow[]>([])
  const [stocktakeCandidates, setStocktakeCandidates] = useState<StocktakeCandidate[]>([])
  const [stocktakeRows, setStocktakeRows] = useState<StocktakeLineDraft[]>([])
  const [stocktakeDraftCandidate, setStocktakeDraftCandidate] = useState<StocktakeCandidate | null>(null)
  const [stocktakeDraftValue, setStocktakeDraftValue] = useState('')
  const [stocktakeProductQuery, setStocktakeProductQuery] = useState('')
  const stocktakeProductInputRef = useRef<HTMLInputElement | null>(null)
  const stocktakeQuantityInputRef = useRef<HTMLInputElement | null>(null)
  const [stocktakeLegacyDialogOpen, setStocktakeLegacyDialogOpen] = useState(false)
  const [stocktakeLegacySaving, setStocktakeLegacySaving] = useState(false)
  const [stocktakeLegacySearch, setStocktakeLegacySearch] = useState('')
  const [stocktakeLegacyValues, setStocktakeLegacyValues] = useState<Record<number, string>>({})
  const [inventoryIssuesToday, setInventoryIssuesToday] = useState<InventoryIssueRow[]>([])
  const [managerPerformedSort, setManagerPerformedSort] = useState<'newest' | 'oldest'>('newest')
  const [managerOutflowSort, setManagerOutflowSort] = useState<'newest' | 'oldest'>('newest')
  const orderedSalons = useMemo(() => sortSalonsPreferred(salons), [salons])
  const isReceptionist = user?.role === 'receptionist'
  const isManagerRole = ['manager', 'manager_main', 'manager_salon'].includes(user?.role || '')
  const isMainManager = user?.role === 'manager_main'
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(today.getDate() + 1)
  const dayAfterTomorrow = new Date(today)
  dayAfterTomorrow.setDate(today.getDate() + 2)
  const canStocktakeFromDashboard = user?.role === 'receptionist'

  useEffect(() => {
    if (selectedSalonId === '' && orderedSalons.length) {
      const nextSalonId =
        orderedSalons.find((salon) => user?.assigned_salon_ids?.includes(salon.id))?.id ?? orderedSalons[0].id
      setSelectedSalonId(nextSalonId)
    }
  }, [orderedSalons, selectedSalonId, user?.assigned_salon_ids])

  useEffect(() => {
    if (selectedSalonId === '') return

    let cancelled = false
    let intervalId: number | undefined

    const fetchData = async () => {
      setError('')
      try {
        const sessionParams =
          (user?.role === 'manager' || user?.role === 'manager_main' || user?.role === 'manager_salon')
            ? { salon_id: selectedSalonId }
            : undefined
        const sessionRequest =
          user?.role === 'admin'
            ? api.get<SessionRow[]>('/sessions/history', { params: { limit: 100 } })
            : (user?.role === 'manager' || user?.role === 'manager_main' || user?.role === 'manager_salon')
              ? api.get<SessionRow[]>('/sessions', { params: sessionParams })
              : null
        const requests: [
          Promise<{ data: StatsResponse }>,
          Promise<{ data: AppointmentRow[] }>,
          Promise<{ data: SalonStaffRow[] }>,
          Promise<{ data: SessionRow[] }> | null,
          Promise<{ data: InventoryIssueRow[] }> | null,
        ] = [
          api.get<StatsResponse>('/booking/stats', { params: { date: 'today', salon_id: selectedSalonId } }),
          api.get<AppointmentRow[]>('/booking/appointments', { params: { date: 'today', salon_id: selectedSalonId, sort: 'start_asc' } }),
          api.get<SalonStaffRow[]>(`/booking/salons/${selectedSalonId}/staff`, { params: { can_take_bookings: true } }),
          sessionRequest,
          isManagerRole
            ? api.get<InventoryIssueRow[]>('/inventory/issues', {
                params: { salon_id: selectedSalonId, status_filter: 'POSTED' },
              })
            : null,
        ]
        const [statsRes, appointmentsRes, staffRes, sessionsRes, issuesRes] = await Promise.all([
          requests[0],
          requests[1],
          requests[2] ?? Promise.resolve({ data: [] as SalonStaffRow[] }),
          requests[3] ?? Promise.resolve({ data: [] as SessionRow[] }),
          requests[4] ?? Promise.resolve({ data: [] as InventoryIssueRow[] }),
        ])
        if (cancelled) return
        setStats(statsRes.data)
        setTodayAppointments(appointmentsRes.data || [])
        setSalonStaff(staffRes.data || [])
        setActiveSessions(sessionsRes.data || [])
        setInventoryIssuesToday((issuesRes.data || []).filter((row) => {
          const dt = new Date(row.issue_time)
          const now = new Date()
          return dt.getFullYear() === now.getFullYear()
            && dt.getMonth() === now.getMonth()
            && dt.getDate() === now.getDate()
        }))
      } catch (err: any) {
        if (!cancelled) {
          setError(err?.response?.data?.detail || 'Nie udalo sie pobrac danych dashboardu.')
        }
      }
    }

    void fetchData()
    intervalId = window.setInterval(() => {
      void fetchData()
    }, 30000)

    return () => {
      cancelled = true
      if (intervalId) window.clearInterval(intervalId)
    }
  }, [appointments, isManagerRole, selectedSalonId, user?.role])

  useEffect(() => {
    if (!canStocktakeFromDashboard || selectedSalonId === '') return
    let cancelled = false
    const loadLocations = async () => {
      try {
        const response = await api.get<StockLocationRow[]>('/inventory/stock-locations', {
          params: { salon_id: selectedSalonId },
        })
        if (cancelled) return
        const rows = (response.data || []).filter((row) => row.is_active)
        setStocktakeLocations(rows)
        setStocktakeLocationId((prev) => {
          if (prev !== '' && rows.some((row) => row.id === prev)) return prev
          return rows[0]?.id ?? ''
        })
      } catch {
        if (!cancelled) {
          setStocktakeLocations([])
          setStocktakeLocationId('')
        }
      }
    }
    void loadLocations()
    return () => {
      cancelled = true
    }
  }, [canStocktakeFromDashboard, selectedSalonId])

  const loadStocktakeCandidates = async (salonId: number) => {
    const response = await api.get<StocktakeCandidate[]>('/inventory/stocktake-candidates', {
      params: { salon_id: salonId },
    })
    setStocktakeCandidates(response.data || [])
  }

  const openStocktakeDialog = async () => {
    if (selectedSalonId === '') return
    setError('')
    const locationId = stocktakeLocations[0]?.id ?? stocktakeLocationId
    if (!locationId) {
      setError('Brak aktywnej lokalizacji magazynowej. Dodaj lokalizacje w Magazyn -> Lokalizacje.')
      return
    }
    setStocktakeLocationId(locationId)
    setStocktakeRows([])
    setStocktakeDraftCandidate(null)
    setStocktakeDraftValue('')
    setStocktakeProductQuery('')
    try {
      await loadStocktakeCandidates(selectedSalonId)
      setStocktakeDialogOpen(true)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac listy produktow do remanentu.')
    }
  }

  const commitStocktakeDraft = () => {
    if (!stocktakeDraftCandidate) return
    const parsed = Number(stocktakeDraftValue)
    if (!Number.isFinite(parsed) || parsed < 0) {
      setError('Podaj poprawna wartosc >= 0.')
      return
    }
    const newRow: StocktakeLineDraft =
      stocktakeDraftCandidate.measurement_mode === 'WEIGHT'
        ? { candidate: stocktakeDraftCandidate, countedUnits: '', measuredGrossWeight: String(parsed) }
        : { candidate: stocktakeDraftCandidate, countedUnits: String(parsed), measuredGrossWeight: '' }
    setStocktakeRows((prev) => {
      const existingIndex = prev.findIndex((row) => row.candidate?.product_id === stocktakeDraftCandidate.product_id)
      if (existingIndex === -1) return [...prev, newRow]
      return prev.map((row, idx) => (idx === existingIndex ? newRow : row))
    })
    setStocktakeDraftCandidate(null)
    setStocktakeDraftValue('')
    setStocktakeProductQuery('')
    window.setTimeout(() => {
      stocktakeProductInputRef.current?.focus()
    }, 0)
  }

  const saveStocktakeFromDashboard = async () => {
    if (selectedSalonId === '' || stocktakeLocationId === '') return
    const lines = stocktakeRows
      .filter((line) => line.candidate)
      .map((line) => {
        if (line.candidate!.measurement_mode === 'WEIGHT') {
          return {
            product_id: line.candidate!.product_id,
            measured_gross_weight: Number(line.measuredGrossWeight),
            unit: 'G',
          }
        }
        return {
          product_id: line.candidate!.product_id,
          counted_units: Number(line.countedUnits),
          unit: 'PCS',
        }
      })
      .filter((line: any) => {
        if (line.measured_gross_weight !== undefined) return Number.isFinite(line.measured_gross_weight) && line.measured_gross_weight >= 0
        if (line.counted_units !== undefined) return Number.isFinite(line.counted_units) && line.counted_units >= 0
        return false
      })
    if (!lines.length) {
      setError('Uzupelnij przynajmniej jedna pozycje remanentu.')
      return
    }
    setStocktakeSaving(true)
    setError('')
    try {
      await api.post('/inventory/stock-adjustments/stocktake', {
        salon_id: selectedSalonId,
        stock_location_id: stocktakeLocationId,
        remarks: null,
        lines,
      })
      setStocktakeDialogOpen(false)
      setInfo('Remanent zostal zapisany.')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac remanentu.')
    } finally {
      setStocktakeSaving(false)
    }
  }

  const salonName = salons.find((salon) => salon.id === selectedSalonId)?.name || ''
  const bundlesInSalon = useMemo(
    () =>
      selectedSalonId === ''
        ? []
        : bundles
            .filter((row) => row.salon_id === selectedSalonId)
            .sort((left, right) => `${left.code} ${left.name}`.localeCompare(`${right.code} ${right.name}`, 'pl')),
    [bundles, selectedSalonId],
  )
  const promoBundles = useMemo(() => {
    const rows = bundlesInSalon.filter((row) => /PROM|FORF|PAKIET|BUNDL|VIP|RABAT|SPECJ|AKCJ/i.test(`${row.code} ${row.name}`))
    return rows.length > 0 ? rows : bundlesInSalon
  }, [bundlesInSalon])
  const specialistStaff = useMemo(
    () =>
      salonStaff.filter(
        (row) =>
          row.is_active &&
          row.can_be_booked &&
          ['HAIRDRESSER', 'MANICURIST'].includes((row.role_code || '').toUpperCase()),
      ),
    [salonStaff],
  )
  const stocktakeSelectedCount = useMemo(
    () => stocktakeCandidates.length,
    [stocktakeCandidates],
  )
  const stocktakeCompletedCount = useMemo(
    () => new Set(stocktakeRows.map((line) => line.candidate?.product_id).filter(Boolean)).size,
    [stocktakeRows],
  )
  const stocktakePendingCount = Math.max(stocktakeSelectedCount - stocktakeCompletedCount, 0)
  const filteredStocktakeCandidates = useMemo(() => {
    const q = stocktakeProductQuery.trim().toLowerCase()
    if (!q) return stocktakeCandidates
    return stocktakeCandidates.filter((item) => {
      const code = item.product_code.toLowerCase()
      const name = item.product_name.toLowerCase()
      return code.includes(q) || name.includes(q)
    })
  }, [stocktakeCandidates, stocktakeProductQuery])
  const filteredStocktakeLegacyCandidates = useMemo(() => {
    const q = stocktakeLegacySearch.trim().toLowerCase()
    if (!q) return stocktakeCandidates
    return stocktakeCandidates.filter((item) => {
      const code = item.product_code.toLowerCase()
      const name = item.product_name.toLowerCase()
      return code.includes(q) || name.includes(q)
    })
  }, [stocktakeCandidates, stocktakeLegacySearch])

  useEffect(() => {
    if (!stocktakeDialogOpen) return
    const timer = window.setTimeout(() => stocktakeProductInputRef.current?.focus(), 60)
    return () => window.clearTimeout(timer)
  }, [stocktakeDialogOpen])

  const openStocktakeLegacyDialog = async () => {
    if (selectedSalonId === '') return
    setError('')
    const locationId = stocktakeLocations[0]?.id ?? stocktakeLocationId
    if (!locationId) {
      setError('Brak aktywnej lokalizacji magazynowej. Dodaj lokalizacje w Magazyn -> Lokalizacje.')
      return
    }
    setStocktakeLocationId(locationId)
    setStocktakeLegacySearch('')
    setStocktakeLegacyValues({})
    try {
      await loadStocktakeCandidates(selectedSalonId)
      setStocktakeLegacyDialogOpen(true)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac listy produktow do remanentu legacy.')
    }
  }

  const saveStocktakeLegacy = async () => {
    if (selectedSalonId === '' || stocktakeLocationId === '') return
    const lines = stocktakeCandidates
      .map((candidate) => {
        const raw = (stocktakeLegacyValues[candidate.product_id] || '').trim()
        if (!raw) return null
        const parsed = Number(raw.replace(',', '.'))
        if (!Number.isFinite(parsed) || parsed < 0) return null
        if (candidate.measurement_mode === 'WEIGHT') {
          return {
            product_id: candidate.product_id,
            measured_gross_weight: parsed,
            unit: 'G',
          }
        }
        return {
          product_id: candidate.product_id,
          counted_units: parsed,
          unit: 'PCS',
        }
      })
      .filter(Boolean)
    if (!lines.length) {
      setError('Uzupelnij co najmniej jedna pozycje w tabeli remanentu legacy.')
      return
    }
    setStocktakeLegacySaving(true)
    setError('')
    try {
      await api.post('/inventory/stock-adjustments/stocktake', {
        salon_id: selectedSalonId,
        stock_location_id: stocktakeLocationId,
        remarks: 'Remanent legacy',
        lines,
      })
      setStocktakeLegacyDialogOpen(false)
      setInfo('Remanent legacy zostal zapisany.')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac remanentu legacy.')
    } finally {
      setStocktakeLegacySaving(false)
    }
  }

  const upcomingAppointments = useMemo(() => {
    if (selectedSalonId === '') return []
    const from = startOfDay(tomorrow)
    const to = endOfDay(dayAfterTomorrow)
    return appointments
      .filter((row) => {
        const start = new Date(row.start_at)
        return row.salon_id === selectedSalonId && start >= from && start <= to
      })
      .sort((a, b) => a.start_at.localeCompare(b.start_at))
      .slice(0, 5)
  }, [appointments, selectedSalonId])

  const kpis = stats
    ? [
        { label: 'Wizyty dzis', value: stats.appointments },
        { label: 'W trakcie', value: stats.appointments_in_progress },
        { label: 'Wykonane dzis', value: stats.completed_appointments },
        ...(user?.role === 'receptionist' ? [] : [{ label: 'Przychod dzis', value: `${stats.revenue_today.toFixed(2)} PLN` }]),
      ]
    : []

  const walkInMinStart = useMemo(() => toDateTimeLocalValue(new Date()), [])
  const walkInMaxStart = useMemo(
    () => toDateTimeLocalValue(new Date(Date.now() + WALK_IN_MAX_LEAD_MINUTES * 60 * 1000)),
    [],
  )

  useEffect(() => {
    if (walkInClientId === '') {
      setWalkInVipLabel('')
      setWalkInPromoLabels([])
      return
    }
    let cancelled = false
    const loadClientBenefits = async () => {
      try {
        const [cardResponse, invitationsResponse] = await Promise.all([
          api.get<VipCardInfo | null>(`/payments/clients/${walkInClientId}/card`),
          api.get<InvitationInfo[]>(`/payments/clients/${walkInClientId}/invitations`),
        ])
        if (cancelled) return
        const card = cardResponse.data
        if (!card) {
          setWalkInVipLabel('')
        } else {
          const expiry = card.expiry ? new Date(card.expiry) : null
          const valid = !expiry || Number.isNaN(expiry.getTime()) || expiry >= startOfDay(new Date())
          setWalkInVipLabel(valid ? `VIP ${card.discount_pct}%` : '')
        }
        const invitations = (invitationsResponse.data || []).filter((row) => !row.used_on_payment_id)
        const labels: string[] = []
        if (invitations.length > 0) labels.push(`Zaproszenia/GRUPON: ${invitations.length}`)
        setWalkInPromoLabels(labels)
      } catch {
        if (!cancelled) {
          setWalkInVipLabel('')
          setWalkInPromoLabels([])
        }
      }
    }
    void loadClientBenefits()
    return () => {
      cancelled = true
    }
  }, [walkInClientId])

  useEffect(() => {
    if (walkInStaffId !== '') return
    if (specialistStaff.length) setWalkInStaffId(specialistStaff[0].id)
  }, [specialistStaff, walkInStaffId])

  const resolveClient = (clientId: number) => clients.find((item) => item.id === clientId)?.full_name || `#${clientId}`
  const resolveStaff = (resourceIds: number[]) =>
    resourceIds.map((id) => resources.find((item) => item.id === id)?.name).filter(Boolean).join(', ') || '-'
  const resolveServices = (serviceIds: number[]) =>
    serviceIds.map((id) => services.find((item) => item.id === id)?.name).filter(Boolean).join(', ') || '-'
  const formatOnline = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 0) return `${hours} h ${minutes} min`
    return `${minutes} min`
  }

  const isStaffBusyAt = (staffId: number, startAt: Date, endAt: Date) =>
    todayAppointments.some((appointment) => {
      if (!appointment.resources.includes(staffId)) return false
      const currentStart = new Date(appointment.start_at)
      const currentEnd = new Date(appointment.end_at)
      return currentStart < endAt && currentEnd > startAt
    })

  const freeNow = useMemo(() => {
    const now = new Date()
    const in15 = new Date(now.getTime() + 15 * 60 * 1000)
    return specialistStaff.filter((row) => !isStaffBusyAt(row.id, now, in15))
  }, [specialistStaff, todayAppointments])

  const quickSlots = useMemo(() => {
    const bundleDuration =
      walkInBundleId === ''
        ? 0
        : (bundlesInSalon.find((item) => item.id === walkInBundleId)?.items || []).reduce(
          (sum, item) => sum + (services.find((service) => service.id === item.service_id)?.duration_minutes || 0),
          0,
        )
    const duration = Math.max(10, bundleDuration || 30)
    const base = nextHalfHour()
    const slots: Array<{ staffId: number; startAt: Date }> = []
    for (const staff of specialistStaff) {
      for (let step = 0; step < 8; step += 1) {
        const start = new Date(base.getTime() + step * 30 * 60 * 1000)
        const end = new Date(start.getTime() + duration * 60 * 1000)
        if (!isStaffBusyAt(staff.id, start, end)) {
          slots.push({ staffId: staff.id, startAt: start })
          break
        }
      }
    }
    return slots
      .sort((a, b) => a.startAt.getTime() - b.startAt.getTime())
      .slice(0, 5)
  }, [bundlesInSalon, specialistStaff, todayAppointments, services, walkInBundleId])

  const managerPerformedRows = useMemo(() => {
    const doneRows = todayAppointments.filter((row) => ['done', 'completed'].includes((row.status || '').toLowerCase()))
    const sorted = [...doneRows].sort((a, b) => {
      const left = new Date(a.end_at).getTime()
      const right = new Date(b.end_at).getTime()
      return managerPerformedSort === 'newest' ? right - left : left - right
    })
    return sorted.slice(0, 40)
  }, [managerPerformedSort, todayAppointments])

  const managerOutflowRows = useMemo(() => {
    const sorted = [...inventoryIssuesToday].sort((a, b) => {
      const left = new Date(a.issue_time).getTime()
      const right = new Date(b.issue_time).getTime()
      return managerOutflowSort === 'newest' ? right - left : left - right
    })
    return sorted.slice(0, 40)
  }, [inventoryIssuesToday, managerOutflowSort])

  const saveWalkInAppointment = async () => {
    if (selectedSalonId === '' || walkInStaffId === '') {
      setError('Uzupelnij dane walk-in: pracownik i termin.')
      return
    }
    setError('')
    setInfo('')
    setIsSavingWalkIn(true)
    try {
      const startAt = new Date(walkInStartAt)
      const now = new Date()
      const sameDay =
        startAt.getFullYear() === now.getFullYear()
        && startAt.getMonth() === now.getMonth()
        && startAt.getDate() === now.getDate()
      if (!sameDay) {
        setError('Walk-in dotyczy tylko dzisiejszych wizyt. Termin na inny dzien dodaj w Kalendarzu wizyt.')
        return
      }
      const leadMinutes = (startAt.getTime() - now.getTime()) / 60000
      if (leadMinutes < -5 || leadMinutes > WALK_IN_MAX_LEAD_MINUTES) {
        setError(`Walk-in mozna zapisac tylko na teraz / najblizsze ${WALK_IN_MAX_LEAD_MINUTES} min.`)
        return
      }
      const bundle = walkInBundleId === '' ? null : bundlesInSalon.find((row) => row.id === walkInBundleId) || null
      const bundleDuration = bundle
        ? bundle.items.reduce((sum, item) => sum + (services.find((serviceRow) => serviceRow.id === item.service_id)?.duration_minutes || 0), 0)
        : 0
      const durationMinutes = Math.max(10, bundleDuration || 30)
      const endAt = new Date(startAt.getTime() + durationMinutes * 60 * 1000)
      if (isStaffBusyAt(walkInStaffId, startAt, endAt)) {
        setError('Wybrany pracownik jest zajety w tym terminie.')
        return
      }

      const normalizedPhone = walkInClientPhone.trim()
      const normalizedName = walkInClientName.trim().toLowerCase()
      let client = walkInClientId === '' ? undefined : clients.find((row) => row.id === walkInClientId)
      if (!client) client = clients.find((row) => row.phone === normalizedPhone)
      if (!client) {
        client = clients.find((row) => row.full_name.trim().toLowerCase() === normalizedName)
      }
      if (!client) {
        const fallbackName = walkInClientName.trim() || `WALK-IN ${new Date().toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}`
        const fallbackPhone = normalizedPhone || `WI-${Date.now()}`
        client = await addClient({
          full_name: fallbackName,
          phone: fallbackPhone,
        })
      }

      await addAppointment({
        salon_id: selectedSalonId,
        client_id: client.id,
        start_at: toApiLocalDateTime(startAt),
        end_at: toApiLocalDateTime(endAt),
        resources: [walkInStaffId],
        services: [],
        bundle_id: walkInBundleId === '' ? undefined : walkInBundleId,
      })
      await reload()
      setWalkInStartAt(toDateTimeLocalValue(nextHalfHour()))
      setWalkInClientId('')
      setWalkInClientName('')
      setWalkInClientPhone('')
      setWalkInVipLabel('')
      setWalkInPromoLabels([])
      setWalkInBundleId('')
      setInfo('Wizyta walk-in zostala zapisana.')
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Nie udalo sie zapisac wizyty walk-in.')
    } finally {
      setIsSavingWalkIn(false)
    }
  }

  return (
    <Stack spacing={3}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1.5}>
        <Typography variant="h4">Dashboard operacyjny</Typography>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems={{ xs: 'stretch', md: 'center' }}>
          {canStocktakeFromDashboard && (
            <Button variant="outlined" onClick={openStocktakeDialog}>
              Remanent
            </Button>
          )}
          {canStocktakeFromDashboard && (
            <Button variant="outlined" onClick={openStocktakeLegacyDialog}>
              Remanent legacy
            </Button>
          )}
          {canStocktakeFromDashboard && (
            <Button variant="outlined" onClick={() => navigate('/inventory/stocktake-legacy')}>
              Remanent legacy - strona
            </Button>
          )}
          {!isReceptionist && (
            <FormControl size="small" sx={{ minWidth: 280 }}>
              <InputLabel>Salon</InputLabel>
              <Select label="Salon" value={selectedSalonId} onChange={(e) => setSelectedSalonId(e.target.value === '' ? '' : Number(e.target.value))}>
                {orderedSalons.map((salon) => <MenuItem key={salon.id} value={salon.id}>{salon.name}</MenuItem>)}
              </Select>
            </FormControl>
          )}
        </Stack>
      </Stack>

      {error && <Alert severity="error">{error}</Alert>}
      {info && <Alert severity="success">{info}</Alert>}

      <Grid container spacing={2}>
        {kpis.map((item) => (
          <Grid item xs={12} md={user?.role === 'receptionist' ? 4 : 3} key={item.label}>
            <Card>
              <CardContent>
                <Typography variant="overline">{item.label}</Typography>
                <Typography variant="h4">{item.value}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {user?.role === 'receptionist' && (
        <Grid container spacing={2}>
          <Grid item xs={12} md={5}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 1.5 }}>Nowa wizyta walk-in</Typography>
                <Stack spacing={1.25}>
                  <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
                    <Autocomplete
                      freeSolo
                      fullWidth
                      size="small"
                      options={clients}
                      value={walkInClientId === '' ? null : clients.find((client) => client.id === walkInClientId) || null}
                      inputValue={walkInClientName}
                      getOptionLabel={(option) => (typeof option === 'string' ? option : option.full_name)}
                      isOptionEqualToValue={(option, value) => option.id === value.id}
                      onInputChange={(_, value) => {
                        setWalkInClientName(value)
                        if (!value) {
                          setWalkInClientId('')
                          setWalkInClientPhone('')
                        }
                      }}
                      onChange={(_, value) => {
                        if (typeof value === 'string') {
                          setWalkInClientId('')
                          setWalkInClientName(value)
                          return
                        }
                        if (!value) {
                          setWalkInClientId('')
                          setWalkInVipLabel('')
                          return
                        }
                        setWalkInClientId(value.id)
                        setWalkInClientName(value.full_name)
                        setWalkInClientPhone(value.phone || '')
                      }}
                      renderInput={(params) => <TextField {...params} label="Klient (wyszukaj)" />}
                      renderOption={(props, option) => (
                        <li {...props} key={option.id}>
                          <Stack direction="row" spacing={1} alignItems="center" sx={{ width: '100%', justifyContent: 'space-between' }}>
                            <Typography>{option.full_name}</Typography>
                            <Typography variant="caption" color="text.secondary">{option.phone || '-'}</Typography>
                          </Stack>
                        </li>
                      )}
                    />
                    <TextField
                      label="Telefon"
                      size="small"
                      fullWidth
                      value={walkInClientPhone}
                      onChange={(event) => setWalkInClientPhone(event.target.value)}
                    />
                  </Stack>
                  {(walkInVipLabel || walkInPromoLabels.length > 0) && (
                    <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                      {walkInVipLabel && <Chip color="warning" label={walkInVipLabel} />}
                      {walkInPromoLabels.map((label) => (
                        <Chip key={label} size="small" color="secondary" label={label} />
                      ))}
                    </Stack>
                  )}
                  <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
                    <Autocomplete
                      size="small"
                      fullWidth
                      options={promoBundles}
                      value={walkInBundleId === '' ? null : promoBundles.find((item) => item.id === walkInBundleId) || null}
                      getOptionLabel={(option) => `${option.code} - ${option.name}`}
                      isOptionEqualToValue={(option, value) => option.id === value.id}
                      onChange={(_, value) => {
                        setWalkInBundleId(value?.id ?? '')
                      }}
                      renderOption={(props, option) => (
                        <li {...props} key={option.id}>
                          <Stack direction="row" spacing={1} alignItems="center">
                            <Typography>{option.code} - {option.name}</Typography>
                            {promoBundles.some((row) => row.id === option.id) && <Chip size="small" color="warning" label="PROMO" />}
                          </Stack>
                        </li>
                      )}
                      renderInput={(params) => <TextField {...params} label="Forfet (opcjonalnie, promo)" />}
                    />
                    <TextField
                      label="Start"
                      size="small"
                      type="datetime-local"
                      fullWidth
                      value={walkInStartAt}
                      onChange={(event) => setWalkInStartAt(event.target.value)}
                      inputProps={{ min: walkInMinStart, max: walkInMaxStart }}
                      InputLabelProps={{ shrink: true }}
                    />
                  </Stack>
                  {promoBundles.length > 0 && (
                    <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                      {promoBundles.map((bundle) => (
                        <Chip
                          key={bundle.id}
                          color={walkInBundleId === bundle.id ? 'primary' : 'default'}
                          variant={walkInBundleId === bundle.id ? 'filled' : 'outlined'}
                          label={`PROMO • ${bundle.code} ${bundle.name}`}
                          onClick={() => {
                            setWalkInBundleId(bundle.id)
                          }}
                        />
                      ))}
                    </Stack>
                  )}
                  <Stack direction="row" spacing={1}>
                    <Button variant="contained" disabled={isSavingWalkIn} onClick={saveWalkInAppointment}>
                      {isSavingWalkIn ? 'Zapisywanie...' : 'Zapisz walk-in'}
                    </Button>
                    <Button variant="outlined" onClick={() => navigate('/calendar')}>
                      Otworz kalendarz
                    </Button>
                    <Button variant="outlined" onClick={() => window.open('/public/client-booking', '_blank', 'noopener,noreferrer')}>
                      Rezerwacje online
                    </Button>
                  </Stack>
                  <Typography variant="subtitle2" sx={{ mt: 1, mb: 0.5 }}>Najblizsze wizyty</Typography>
                  <Stack spacing={1}>
                    {upcomingAppointments.map((row) => (
                      <Stack key={row.id} direction="row" justifyContent="space-between" sx={{ border: '1px solid #e5e7eb', borderRadius: 2, p: 1 }}>
                        <Stack spacing={0.25}>
                          <Typography sx={{ fontWeight: 600 }}>{resolveClient(row.client_id)}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            {new Date(row.start_at).toLocaleString('pl-PL', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                          </Typography>
                        </Stack>
                        <Typography variant="body2">{resolveStaff(row.resources)}</Typography>
                      </Stack>
                    ))}
                    {!upcomingAppointments.length && <Typography color="text.secondary">Brak wizyt na jutro i pojutrze.</Typography>}
                  </Stack>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={7}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 1.25 }}>Harmonogram dzis {salonName ? `- ${salonName}` : ''}</Typography>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Godzina</TableCell>
                      <TableCell>Klient</TableCell>
                      <TableCell>Pracownik</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {todayAppointments.slice(0, 8).map((row) => (
                      <TableRow key={row.id} hover onClick={() => navigate(`/calendar?appointment_id=${row.id}`)} sx={{ cursor: 'pointer' }}>
                        <TableCell>{new Date(row.start_at).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}</TableCell>
                        <TableCell>{resolveClient(row.client_id)}</TableCell>
                        <TableCell>{resolveStaff(row.resources)}</TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            color={STATUS_COLOR[(row.status || '').toLowerCase()] || 'default'}
                            label={row.status}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                    {!todayAppointments.length && (
                      <TableRow>
                        <TableCell colSpan={4}>Brak wizyt na dzis.</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
                <Typography variant="subtitle2" sx={{ mt: 2, mb: 1.25 }}>Kto wolny teraz / za 15 min</Typography>
                <Stack spacing={1}>
                  {freeNow.map((row) => {
                    const selected = walkInStaffId === row.id
                    return (
                    <Stack key={row.id} direction="row" justifyContent="space-between" sx={{ border: '1px solid #e5e7eb', borderRadius: 2, p: 1 }}>
                      <Button size="small" variant={selected ? 'contained' : 'text'} onClick={() => setWalkInStaffId(row.id)}>
                        {row.display_name}
                      </Button>
                      <Chip size="small" color={selected ? 'primary' : 'success'} label={selected ? 'Wybrany' : 'Wolny'} />
                    </Stack>
                  )})}
                  {!freeNow.length && <Typography color="text.secondary">Brak wolnych specjalistow na teraz.</Typography>}
                </Stack>
                <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>Najblizsze luki</Typography>
                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                  {quickSlots.map((slot) => {
                    const label = `${new Date(slot.startAt).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })} • ${specialistStaff.find((s) => s.id === slot.staffId)?.display_name || slot.staffId}`
                    return (
                      <Chip
                        key={`${slot.staffId}-${slot.startAt.toISOString()}`}
                        label={label}
                        onClick={() => {
                          setWalkInStaffId(slot.staffId)
                          setWalkInStartAt(toDateTimeLocalValue(slot.startAt))
                        }}
                      />
                    )
                  })}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {user?.role !== 'receptionist' && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Harmonogram dzis {salonName ? `- ${salonName}` : ''}</Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Godzina</TableCell>
                  <TableCell>Klient</TableCell>
                  <TableCell>Pracownik</TableCell>
                  <TableCell>Uslugi</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Snapshot</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {todayAppointments.map((row) => (
                  <TableRow key={row.id} hover onClick={() => navigate(`/calendar?appointment_id=${row.id}`)} sx={{ cursor: 'pointer' }}>
                    <TableCell>{new Date(row.start_at).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}</TableCell>
                    <TableCell>{resolveClient(row.client_id)}</TableCell>
                    <TableCell>{resolveStaff(row.resources)}</TableCell>
                    <TableCell>{resolveServices(row.services)}</TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        color={STATUS_COLOR[(row.status || '').toLowerCase()] || 'default'}
                        label={row.status}
                      />
                    </TableCell>
                    <TableCell align="right">{row.total_price_snapshot.toFixed(2)}</TableCell>
                  </TableRow>
                ))}
                {!todayAppointments.length && (
                  <TableRow>
                    <TableCell colSpan={6}>Brak wizyt na dzis.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {user?.role !== 'receptionist' && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Najblizsze wizyty</Typography>
            <Stack spacing={1.25}>
              {upcomingAppointments.map((row) => (
                <Stack key={row.id} direction="row" justifyContent="space-between" sx={{ border: '1px solid #e5e7eb', borderRadius: 2, p: 1.25 }}>
                  <Stack spacing={0.25}>
                    <Typography sx={{ fontWeight: 600 }}>{resolveClient(row.client_id)}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {new Date(row.start_at).toLocaleString('pl-PL', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                    </Typography>
                  </Stack>
                  <Typography variant="body2">{resolveStaff(row.resources)}</Typography>
                </Stack>
              ))}
              {!upcomingAppointments.length && <Typography color="text.secondary">Brak wizyt na jutro i pojutrze.</Typography>}
            </Stack>
          </CardContent>
        </Card>
      )}

      {(['admin', 'manager', 'manager_main', 'manager_salon'].includes(user?.role || '')) && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              {user?.role === 'admin' ? 'Historia logowan' : 'Recepcja online'}
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Login</TableCell>
                  <TableCell>Rola</TableCell>
                  <TableCell>Salon</TableCell>
                  <TableCell>{user?.role === 'admin' ? 'Logowanie' : 'Online od'}</TableCell>
                  <TableCell>{user?.role === 'admin' ? 'Ostatnia aktywnosc' : 'Status'}</TableCell>
                  <TableCell>{user?.role === 'admin' ? 'IP' : ''}</TableCell>
                  <TableCell align="right">{user?.role === 'admin' ? 'Aktywna' : 'Czas online'}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {activeSessions.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>{row.username}</TableCell>
                    <TableCell>{row.role}</TableCell>
                    <TableCell>{row.salon_name || '-'}</TableCell>
                    <TableCell>{new Date(row.online_since).toLocaleString('pl-PL', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</TableCell>
                    <TableCell>
                      {user?.role === 'admin'
                        ? new Date(row.last_seen).toLocaleString('pl-PL', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
                        : 'online'}
                    </TableCell>
                    <TableCell>{user?.role === 'admin' ? row.ip_address || '-' : ''}</TableCell>
                    <TableCell align="right">
                      {user?.role === 'admin'
                        ? (row.is_active ? 'TAK' : 'NIE')
                        : formatOnline(row.online_seconds)}
                    </TableCell>
                  </TableRow>
                ))}
                {!activeSessions.length && (
                  <TableRow>
                    <TableCell colSpan={7}>{user?.role === 'admin' ? 'Brak historii logowan.' : 'Brak aktywnych sesji.'}</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {isManagerRole && (
        <Grid container spacing={2}>
          <Grid item xs={12} md={isMainManager ? 6 : 12}>
            <Card>
              <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5 }}>
                  <Typography variant="h6">Wykonane uslugi dzis</Typography>
                  <FormControl size="small" sx={{ minWidth: 190 }}>
                    <InputLabel>Sortowanie</InputLabel>
                    <Select
                      label="Sortowanie"
                      value={managerPerformedSort}
                      onChange={(e) => setManagerPerformedSort(e.target.value as 'newest' | 'oldest')}
                    >
                      <MenuItem value="newest">Najnowsze na gorze</MenuItem>
                      <MenuItem value="oldest">Najstarsze na gorze</MenuItem>
                    </Select>
                  </FormControl>
                </Stack>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Godzina</TableCell>
                      <TableCell>Klient</TableCell>
                      <TableCell>Uslugi</TableCell>
                      <TableCell align="right">Snapshot</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {managerPerformedRows.map((row) => (
                      <TableRow key={`performed-${row.id}`}>
                        <TableCell>{new Date(row.end_at).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}</TableCell>
                        <TableCell>{resolveClient(row.client_id)}</TableCell>
                        <TableCell>{resolveServices(row.services)}</TableCell>
                        <TableCell align="right">{row.total_price_snapshot.toFixed(2)} PLN</TableCell>
                      </TableRow>
                    ))}
                    {!managerPerformedRows.length && (
                      <TableRow>
                        <TableCell colSpan={4}>Brak wykonanych uslug dzis.</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={isMainManager ? 6 : 12}>
            <Card>
              <CardContent>
                <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5 }}>
                  <Typography variant="h6">Rozchody magazynowe dzis</Typography>
                  <FormControl size="small" sx={{ minWidth: 190 }}>
                    <InputLabel>Sortowanie</InputLabel>
                    <Select
                      label="Sortowanie"
                      value={managerOutflowSort}
                      onChange={(e) => setManagerOutflowSort(e.target.value as 'newest' | 'oldest')}
                    >
                      <MenuItem value="newest">Najnowsze na gorze</MenuItem>
                      <MenuItem value="oldest">Najstarsze na gorze</MenuItem>
                    </Select>
                  </FormControl>
                </Stack>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Godzina</TableCell>
                      <TableCell align="right">Dokument</TableCell>
                      <TableCell align="right">Pozycje</TableCell>
                      <TableCell align="right">Koszt</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {managerOutflowRows.map((row) => (
                      <TableRow key={`outflow-${row.id}`}>
                        <TableCell>{new Date(row.issue_time).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}</TableCell>
                        <TableCell align="right">#{row.id}</TableCell>
                        <TableCell align="right">{row.lines?.length || 0}</TableCell>
                        <TableCell align="right">
                          {(row.lines || []).reduce((sum, line) => sum + Number(line.total_cost || 0), 0).toFixed(2)} PLN
                        </TableCell>
                      </TableRow>
                    ))}
                    {!managerOutflowRows.length && (
                      <TableRow>
                        <TableCell colSpan={4}>Brak rozchodow magazynowych dzis.</TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <Dialog open={stocktakeDialogOpen} onClose={() => setStocktakeDialogOpen(false)} fullWidth maxWidth="md">
        <DialogTitle>Remanent salonu</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Salon: {salonName || '-'}.
              {' '}
              Remanent zapisze sie do domyslnej lokalizacji technicznej:
              {' '}
              {stocktakeLocations[0]?.name || '-'} ({stocktakeLocations[0]?.location_type || '-'}).
            </Typography>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems={{ xs: 'stretch', md: 'center' }}>
              <Chip color="info" label={`Wszystkie pozycje: ${stocktakeSelectedCount}`} />
              <Chip color="success" label={`Zinwentaryzowane: ${stocktakeCompletedCount}`} />
              <Chip color={stocktakePendingCount === 0 ? 'success' : 'warning'} label={`Oczekuje: ${stocktakePendingCount}`} />
            </Stack>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} alignItems="flex-start">
              <Autocomplete
                options={stocktakeCandidates}
                getOptionLabel={(option) => `${option.product_code} - ${option.product_name}`}
                openOnFocus
                value={stocktakeDraftCandidate}
                inputValue={stocktakeProductQuery}
                onInputChange={(_, value) => setStocktakeProductQuery(value)}
                onChange={(_, value) => {
                  setStocktakeDraftCandidate(value)
                  window.setTimeout(() => stocktakeQuantityInputRef.current?.focus(), 0)
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Dodaj produkt (kod / nazwa)"
                    inputRef={stocktakeProductInputRef}
                    onKeyDown={(event) => {
                      if (event.key === 'Tab' || event.key === 'Enter') {
                        const picked = stocktakeDraftCandidate || filteredStocktakeCandidates[0] || null
                        if (picked) {
                          event.preventDefault()
                          setStocktakeDraftCandidate(picked)
                          setStocktakeProductQuery(`${picked.product_code} - ${picked.product_name}`)
                          window.setTimeout(() => stocktakeQuantityInputRef.current?.focus(), 0)
                        }
                      }
                    }}
                  />
                )}
                sx={{ flex: 1 }}
              />
              <TextField
                label={
                  stocktakeDraftCandidate
                    ? stocktakeDraftCandidate.measurement_mode === 'WEIGHT'
                      ? 'Ilosc: waga brutto (g)'
                      : 'Ilosc: sztuki (opak./szt.)'
                    : 'Ilosc'
                }
                value={stocktakeDraftValue}
                onChange={(event) => setStocktakeDraftValue(event.target.value)}
                helperText={
                  stocktakeDraftCandidate?.measurement_mode === 'WEIGHT'
                    ? `Tara: ${stocktakeDraftCandidate.package_weight ?? '-'} g | Doza: ${stocktakeDraftCandidate.dose_weight ?? '-'} g`
                    : stocktakeDraftCandidate
                      ? 'Wpisz liczbe opakowan/sztuk'
                      : 'Najpierw wybierz produkt'
                }
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === 'Tab') {
                    event.preventDefault()
                    commitStocktakeDraft()
                  }
                }}
                sx={{ width: 260 }}
                inputRef={stocktakeQuantityInputRef}
              />
              <Button variant="contained" onClick={commitStocktakeDraft}>
                Dodaj
              </Button>
            </Stack>

            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Kod</TableCell>
                  <TableCell>Produkt</TableCell>
                  <TableCell>Tryb</TableCell>
                  <TableCell>Wpisana ilosc</TableCell>
                  <TableCell align="right">Akcja</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {stocktakeRows.map((row, index) => (
                  <TableRow key={`${row.candidate?.product_id}-${index}`}>
                    <TableCell>{row.candidate?.product_code}</TableCell>
                    <TableCell>{row.candidate?.product_name}</TableCell>
                    <TableCell>{row.candidate?.measurement_mode === 'WEIGHT' ? 'WAGA' : 'SZTUKI'}</TableCell>
                    <TableCell>
                      {row.candidate?.measurement_mode === 'WEIGHT'
                        ? `${row.measuredGrossWeight} g`
                        : `${row.countedUnits} szt.`}
                    </TableCell>
                    <TableCell align="right">
                      <Button color="error" onClick={() => setStocktakeRows((prev) => prev.filter((_, idx) => idx !== index))}>Usun</Button>
                    </TableCell>
                  </TableRow>
                ))}
                {!stocktakeRows.length && (
                  <TableRow>
                    <TableCell colSpan={5}>Brak dodanych pozycji remanentu.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStocktakeDialogOpen(false)}>Anuluj</Button>
          <Button variant="contained" onClick={saveStocktakeFromDashboard} disabled={stocktakeSaving}>
            {stocktakeSaving ? 'Zapisywanie...' : 'Zapisz remanent'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={stocktakeLegacyDialogOpen} onClose={() => setStocktakeLegacyDialogOpen(false)} fullWidth maxWidth="xl">
        <DialogTitle>Remanent legacy (uklad tabelaryczny)</DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Salon: {salonName || '-'}.
              {' '}
              Wpisz ilosci w tabeli i zapisz.
            </Typography>
            <TextField
              size="small"
              label="Szukaj po kodzie / nazwie"
              value={stocktakeLegacySearch}
              onChange={(event) => setStocktakeLegacySearch(event.target.value)}
            />
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Kod</TableCell>
                  <TableCell>Produkt</TableCell>
                  <TableCell>Tryb</TableCell>
                  <TableCell>Podpowiedz</TableCell>
                  <TableCell>Ilosc do wpisania</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredStocktakeLegacyCandidates.map((row) => (
                  <TableRow key={`legacy-stocktake-${row.product_id}`}>
                    <TableCell>{row.product_code}</TableCell>
                    <TableCell>{row.product_name}</TableCell>
                    <TableCell>{row.measurement_mode === 'WEIGHT' ? 'WAGA' : 'SZTUKI'}</TableCell>
                    <TableCell>
                      {row.measurement_mode === 'WEIGHT'
                        ? `Waga brutto (g), tara: ${row.package_weight ?? '-'} g, doza: ${row.dose_weight ?? '-'} g`
                        : 'Sztuki (opak./szt.)'}
                    </TableCell>
                    <TableCell>
                      <TextField
                        size="small"
                        value={stocktakeLegacyValues[row.product_id] || ''}
                        onChange={(event) =>
                          setStocktakeLegacyValues((prev) => ({
                            ...prev,
                            [row.product_id]: event.target.value,
                          }))
                        }
                        placeholder={row.measurement_mode === 'WEIGHT' ? 'np. 845.5' : 'np. 3'}
                      />
                    </TableCell>
                  </TableRow>
                ))}
                {!filteredStocktakeLegacyCandidates.length && (
                  <TableRow>
                    <TableCell colSpan={5}>Brak pozycji do wyswietlenia.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => navigate('/inventory/stocktake-legacy')}>Pelna strona legacy</Button>
          <Button onClick={() => setStocktakeLegacyDialogOpen(false)}>Anuluj</Button>
          <Button variant="contained" onClick={saveStocktakeLegacy} disabled={stocktakeLegacySaving}>
            {stocktakeLegacySaving ? 'Zapisywanie...' : 'Zapisz remanent legacy'}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}

export default DashboardPage
