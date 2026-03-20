import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Grid,
  MenuItem,
  Radio,
  RadioGroup,
  Stack,
  FormControl,
  InputLabel,
  Select,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useBooking } from '../contexts/BookingContext'
import { api } from '../services/api'
import type { Appointment } from '../types'

const parseDate = (value: string) => new Date(value)
const overlaps = (startA: Date, endA: Date, startB: Date, endB: Date) => startA < endB && startB < endA
const readCalendarNumber = (raw: string | undefined, fallback: number) => {
  const parsed = Number(raw)
  return Number.isFinite(parsed) ? parsed : fallback
}

const CALENDAR_SETTINGS = {
  CALENDAR_START_HOUR: readCalendarNumber(import.meta.env.VITE_CALENDAR_START_HOUR, 7),
  CALENDAR_END_HOUR: readCalendarNumber(import.meta.env.VITE_CALENDAR_END_HOUR, 21),
  SLOT_DURATION_MINUTES: readCalendarNumber(import.meta.env.VITE_CALENDAR_SLOT_MINUTES, 30),
} as const
const SLOT_START_HOUR = CALENDAR_SETTINGS.CALENDAR_START_HOUR
const SLOT_END_HOUR = CALENDAR_SETTINGS.CALENDAR_END_HOUR + 1
const SLOT_DURATION_MINUTES = CALENDAR_SETTINGS.SLOT_DURATION_MINUTES
const HALF_HOUR_ROW_HEIGHT = 44
const WEEK_SLOT_ROW_HEIGHT = 34
const ROLLING30_SLOT_ROW_HEIGHT = 16

const formatDateTimeLocal = (value: Date) => {
  const yyyy = value.getFullYear()
  const mm = String(value.getMonth() + 1).padStart(2, '0')
  const dd = String(value.getDate()).padStart(2, '0')
  const hh = String(value.getHours()).padStart(2, '0')
  const mi = String(value.getMinutes()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}T${hh}:${mi}`
}

const formatDateOnly = (value: Date) => {
  const yyyy = value.getFullYear()
  const mm = String(value.getMonth() + 1).padStart(2, '0')
  const dd = String(value.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

const parseTimeToDate = (dateKey: string, timeValue: string) => {
  const normalized = (timeValue || '').slice(0, 5) || '00:00'
  return new Date(`${dateKey}T${normalized}`)
}

const subtractIntervalsTs = (
  intervals: Array<[number, number]>,
  blockStart: number,
  blockEnd: number,
) => {
  if (blockEnd <= blockStart) return intervals
  const result: Array<[number, number]> = []
  for (const [start, end] of intervals) {
    if (blockEnd <= start || blockStart >= end) {
      result.push([start, end])
      continue
    }
    if (blockStart > start) result.push([start, blockStart])
    if (blockEnd < end) result.push([blockEnd, end])
  }
  return result
}

type ExecutionLineDraft = {
  service_id: number | ''
  worker_id: number | ''
  worker_role_id: number | ''
  price_snapshot: number
  resources: ExecutionLineResourceDraft[]
}

type ExecutionLineResourceDraft = {
  recipe_item_id: number
  product_id: number | ''
  quantity_used: number
}

type ExecutionProductOption = {
  id: number
  code: string
  name: string
  family_code?: string | null
}

type ServiceRecipeInfo = {
  id: number
  product_id?: number | null
  product_family?: string | null
  product_name?: string | null
  product_label_snapshot?: string | null
  is_required?: boolean
  quantity_mode?: string | null
  planned_quantity?: number | null
  planned_min?: number | null
  planned_default?: number | null
  planned_max?: number | null
  unit?: string | null
  recipe_unit_label?: string | null
  inventory_mode?: string | null
  note?: string | null
  total_label?: string | null
}

type PerformedResourceDetail = {
  performed_line_id: number
  service_id: number
  service_name?: string | null
  worker_id: number
  worker_name?: string | null
  worker_role_id: number
  worker_role_name?: string | null
  product_id: number
  product_family?: string | null
  product_name?: string | null
  quantity_used: number
  quantity_unit?: string | null
  unit_cost_snapshot?: number | null
  total_cost_snapshot?: number | null
}

type SalonStaffOption = {
  id: number
  displayName: string
  role_code?: string | null
  can_be_booked: boolean
}

type StaffMonthlyScheduleApi = {
  id: number
  staff_id: number
  salon_id: number
  work_date: string
  time_from: string
  time_to: string
  is_active: boolean
}

type StaffWeeklyScheduleApi = {
  id: number
  staff_id: number
  salon_id: number
  weekday: number
  time_from: string
  time_to: string
  is_active: boolean
}

type StaffTimeOffApi = {
  id: number
  staff_id: number
  salon_id: number
  start_datetime: string
  end_datetime: string
  reason?: string | null
}

type RetailProductOption = {
  id: number
  code: string
  name: string
  price: number
}

type InvoiceItem = {
  service_id?: number | null
  product_id?: number | null
  kind: string
  label: string
  quantity: number
  unit_price: number
  total_gross: number
  discount_value: number
}

type ClientCardInfo = {
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

type InvoicePreview = {
  appointment_id: number
  client_id: number
  service_gross: number
  retail_gross: number
  card_discount: number
  invitation_discount: number
  total_discount: number
  net_total: number
  eligible_card?: ClientCardInfo | null
  available_invitations: InvitationInfo[]
  items: InvoiceItem[]
}

type RetailDraft = {
  product_id: number | ''
  quantity: number
}

type PaymentAllocationDraft = {
  method: 'cash' | 'card' | 'voucher' | 'transfer'
  amount: number
  voucher_reference: string
}

type PromotionOption = {
  id: number
  name: string
  promotion_type: string
  value: number
  salon_id?: number | null
  service_id?: number | null
  bundle_id?: number | null
}

type CalendarView = 'day' | 'week' | 'rolling30'

type PositionedAppointment = {
  appointment: Appointment
  lane: number
  laneCount: number
}

const getRecipeInventoryMode = (item: ServiceRecipeInfo) => (item.inventory_mode || 'PER_SERVICE').toUpperCase()
const isRecipeStocktakeOnly = (item: ServiceRecipeInfo) => getRecipeInventoryMode(item) === 'STOCKTAKE_ONLY'
const isRecipeRequiredPerService = (item: ServiceRecipeInfo) =>
  (item.is_required ?? true) && getRecipeInventoryMode(item) === 'PER_SERVICE'
const getRecipePlannedQuantity = (item: ServiceRecipeInfo) =>
  Number(item.planned_default ?? item.planned_quantity ?? 0)
const getRecipeUnitLabel = (item: ServiceRecipeInfo) => (item.recipe_unit_label || item.unit || 'PCS').toUpperCase()

const STATUS_COLOR: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning'> = {
  pending: 'warning',
  planned: 'default',
  started: 'primary',
  in_progress: 'primary',
  done: 'success',
  completed: 'success',
  cancelled: 'error',
  no_show: 'error',
}

const STATUS_LABEL: Record<string, string> = {
  pending: 'Oczekuje na potwierdzenie',
  planned: 'Zaplanowana',
  confirmed: 'Potwierdzona',
  started: 'W trakcie',
  in_progress: 'W trakcie',
  done: 'Wykonana',
  completed: 'Wykonana',
  cancelled: 'Anulowana',
  no_show: 'Klient nie przyszedl',
}

const getStatusBackground = (status: string | undefined) => {
  const normalized = (status || '').toLowerCase()
  if (STATUS_COLOR[normalized] === 'success') return '#2e7d32'
  if (STATUS_COLOR[normalized] === 'primary') return '#1565c0'
  if (STATUS_COLOR[normalized] === 'warning') return '#ed6c02'
  if (STATUS_COLOR[normalized] === 'error') return '#c62828'
  return '#6b7280'
}

const normalizeRepeatedLabel = (value?: string | null) => {
  const normalized = (value || '').replace(/\s+/g, ' ').trim()
  if (!normalized) return ''
  const parts = normalized.split(' ')
  if (parts.length >= 4 && parts.length % 2 === 0) {
    const half = parts.length / 2
    const left = parts.slice(0, half).join(' ')
    const right = parts.slice(half).join(' ')
    if (left.toLowerCase() === right.toLowerCase()) return left
  }
  if (parts.length > 2) {
    const secondLast = parts[parts.length - 2]
    const last = parts[parts.length - 1]
    if (parts[0].toLowerCase() === secondLast.toLowerCase()) {
      return `${last} ${secondLast}`
    }
    return `${secondLast} ${last}`
  }
  return normalized
}

const composeStaffLabel = (firstName?: string | null, lastName?: string | null, fallback?: string | null) => {
  const joined = [firstName, lastName].filter(Boolean).join(' ').trim()
  if (joined) return normalizeRepeatedLabel(joined)
  return normalizeRepeatedLabel(fallback)
}

const buildDayAppointmentLayout = (appointments: Appointment[]) => {
  const sorted = [...appointments].sort(
    (left, right) => parseDate(left.start_at).getTime() - parseDate(right.start_at).getTime(),
  )
  const groups: Appointment[][] = []

  sorted.forEach((appointment) => {
    const start = parseDate(appointment.start_at)
    const end = parseDate(appointment.end_at)
    const lastGroup = groups[groups.length - 1]
    if (!lastGroup) {
      groups.push([appointment])
      return
    }
    const groupEnd = Math.max(...lastGroup.map((item) => parseDate(item.end_at).getTime()))
    if (start.getTime() < groupEnd && end.getTime() > parseDate(lastGroup[0].start_at).getTime()) {
      lastGroup.push(appointment)
      return
    }
    groups.push([appointment])
  })

  const positioned: PositionedAppointment[] = []
  groups.forEach((group) => {
    const laneEnds: number[] = []
    const laneById = new Map<number, number>()

    group.forEach((appointment) => {
      const start = parseDate(appointment.start_at).getTime()
      const end = parseDate(appointment.end_at).getTime()
      let lane = laneEnds.findIndex((laneEnd) => laneEnd <= start)
      if (lane === -1) {
        lane = laneEnds.length
        laneEnds.push(end)
      } else {
        laneEnds[lane] = end
      }
      laneById.set(appointment.id, lane)
    })

    const laneCount = Math.max(laneEnds.length, 1)
    group.forEach((appointment) => {
      positioned.push({
        appointment,
        lane: laneById.get(appointment.id) ?? 0,
        laneCount,
      })
    })
  })

  return positioned
}

const formatTimeRange = (start: Date, end: Date) =>
  `${start.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}-${end.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}`

const SALON_ORDER_CODES = ['05', '12', '02', '07'] as const
const SPECIALIST_ROLE_CODES = new Set(['FRYZJER', 'MANICURZYSTKA', 'HAIRDRESSER', 'MANICURIST'])

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

const getStaffRoleColor = (roleCode?: string | null) => {
  const normalized = (roleCode || '').toUpperCase()
  if (normalized.includes('MANICUR')) return '#7c3aed'
  return '#0f766e'
}

const isHairdresserRole = (roleCode?: string | null) => {
  const normalized = (roleCode || '').toUpperCase()
  return normalized.includes('FRYZJER') || normalized.includes('HAIRDRESSER')
}

const isManicureRole = (roleCode?: string | null) => {
  const normalized = (roleCode || '').toUpperCase()
  return normalized.includes('MANICUR')
}

const clampAppointmentToGrid = (start: Date, end: Date) => {
  const gridStart = new Date(start)
  gridStart.setHours(SLOT_START_HOUR, 0, 0, 0)
  const gridEnd = new Date(start)
  gridEnd.setHours(SLOT_END_HOUR, 0, 0, 0)
  const clampedStart = start < gridStart ? gridStart : start
  const clampedEnd = end > gridEnd ? gridEnd : end
  if (clampedEnd <= clampedStart) return null
  const minutesFromGridStart = (clampedStart.getHours() - SLOT_START_HOUR) * 60 + clampedStart.getMinutes()
  const durationMinutes = Math.max(SLOT_DURATION_MINUTES, (clampedEnd.getTime() - clampedStart.getTime()) / 60000)
  return { minutesFromGridStart, durationMinutes }
}

const SchedulesPage = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const {
    appointments,
    salons,
    clients,
    resources,
    services,
    bundles,
    staffRoles,
    priceListItems,
    addAppointment,
    addClient,
    completeAppointment,
    reload,
    estimateTotal,
  } = useBooking()

  const defaultSalon =
    sortSalonsPreferred(salons).find((salon) => user?.assigned_salon_ids?.includes(salon.id))?.id ??
    sortSalonsPreferred(salons)[0]?.id ??
    1
  const [selectedSalon, setSelectedSalon] = useState(defaultSalon)
  const [clientMode, setClientMode] = useState<'existing' | 'new'>('existing')
  const [clientId, setClientId] = useState<number>(clients[0]?.id ?? 1)
  const [newClientName, setNewClientName] = useState('')
  const [newClientPhone, setNewClientPhone] = useState('')
  const [newClientEmail, setNewClientEmail] = useState('')
  const [startAt, setStartAt] = useState('2026-02-26T15:00')
  const [endAt, setEndAt] = useState('2026-02-26T16:00')
  const [salonStaff, setSalonStaff] = useState<SalonStaffOption[]>([])
  const [staffWorkWindowsByKey, setStaffWorkWindowsByKey] = useState<Record<string, Array<[number, number]>>>({})
  const [loadingStaff, setLoadingStaff] = useState(false)
  const [selectedStaffId, setSelectedStaffId] = useState<number | ''>('')
  const [selectedServices, setSelectedServices] = useState<number[]>([])
  const [bundleId, setBundleId] = useState<number | ''>('')
  const [allowOverlap, setAllowOverlap] = useState(false)
  const [flash, setFlash] = useState('')
  const [smsSuggestedAppointmentId, setSmsSuggestedAppointmentId] = useState<number | null>(null)
  const [smsSending, setSmsSending] = useState(false)
  const [availabilityStatus, setAvailabilityStatus] = useState<{ busy: boolean; message: string } | null>(null)
  const [calendarView, setCalendarView] = useState<CalendarView>(() => {
    if (typeof window === 'undefined') return 'day'
    const saved = window.localStorage.getItem('calendar_view') as CalendarView | null
    return saved === 'day' || saved === 'week' || saved === 'rolling30' ? saved : 'day'
  })
  const [calendarDate, setCalendarDate] = useState(formatDateOnly(new Date()))
  const [detailsAppointmentId, setDetailsAppointmentId] = useState<number | null>(null)
  const [appointmentDialogOpen, setAppointmentDialogOpen] = useState(false)
  const [calendarAppointments, setCalendarAppointments] = useState<Appointment[]>([])
  const [calendarLoading, setCalendarLoading] = useState(false)
  const [rollingRoleFilter, setRollingRoleFilter] = useState<'all' | 'hairdresser' | 'manicure'>('all')
  const [rollingStaffFilter, setRollingStaffFilter] = useState<number | ''>('')
  const [settlementAppointmentId, setSettlementAppointmentId] = useState<number | null>(null)
  const [settlementOpen, setSettlementOpen] = useState(false)
  const [settlementLoading, setSettlementLoading] = useState(false)
  const [settlementError, setSettlementError] = useState('')
  const [settlementUseCard, setSettlementUseCard] = useState(false)
  const [settlementInvitationIds, setSettlementInvitationIds] = useState<number[]>([])
  const [settlementRetailRows, setSettlementRetailRows] = useState<RetailDraft[]>([])
  const [settlementProducts, setSettlementProducts] = useState<RetailProductOption[]>([])
  const [settlementPromotions, setSettlementPromotions] = useState<PromotionOption[]>([])
  const [settlementPromotionId, setSettlementPromotionId] = useState<number | ''>('')
  const [settlementAllocations, setSettlementAllocations] = useState<PaymentAllocationDraft[]>([
    { method: 'cash', amount: 0, voucher_reference: '' },
  ])
  const [invoicePreview, setInvoicePreview] = useState<InvoicePreview | null>(null)
  const [settledAppointmentIds, setSettledAppointmentIds] = useState<number[]>([])

  const [executionAppointmentId, setExecutionAppointmentId] = useState<number | ''>('')
  const [executionPerformedAt, setExecutionPerformedAt] = useState('2026-02-26T16:00')
  const [executionLines, setExecutionLines] = useState<ExecutionLineDraft[]>([])
  const [executionProducts, setExecutionProducts] = useState<ExecutionProductOption[]>([])
  const [executionProductsByFamily, setExecutionProductsByFamily] = useState<Record<string, ExecutionProductOption[]>>({})
  const [executionRecipesByService, setExecutionRecipesByService] = useState<Record<number, ServiceRecipeInfo[]>>({})
  const [executionError, setExecutionError] = useState('')
  const [detailResources, setDetailResources] = useState<PerformedResourceDetail[]>([])
  const canCreateAppointments = !!user && user.role !== 'employee'
  const canUseOverlap = ['admin', 'manager', 'manager_main', 'manager_salon', 'receptionist'].includes(user?.role || '')

  const allowedSalons = useMemo(() => {
    if (!user) return salons
    if (user.role === 'admin' || user.role === 'manager' || user.role === 'manager_main') return salons
    if (!user.assigned_salon_ids?.length) return salons
    return salons.filter((s) => user.assigned_salon_ids?.includes(s.id))
  }, [salons, user])
  const orderedAllowedSalons = useMemo(() => sortSalonsPreferred(allowedSalons), [allowedSalons])
  const appointmentsInSalon = useMemo(
    () => appointments.filter((a) => a.salon_id === selectedSalon),
    [appointments, selectedSalon],
  )

  useEffect(() => {
    if (orderedAllowedSalons.length > 0 && !orderedAllowedSalons.some((salon) => salon.id === selectedSalon)) {
      setSelectedSalon(orderedAllowedSalons[0].id)
    }
  }, [orderedAllowedSalons, selectedSalon])

  useEffect(() => {
    if (clients.length > 0 && !clients.some((client) => client.id === clientId)) {
      setClientId(clients[0].id)
    }
  }, [clientId, clients])

  const bookableRoleIds = staffRoles
    .filter((role) => role.code === 'FRYZJER' || role.code === 'MANICURZYSTKA')
    .map((role) => role.id)

  const bundlesInSalon = bundles.filter((b) => b.salon_id === selectedSalon)
  const selectedBundle = bundleId === '' ? null : bundlesInSalon.find((item) => item.id === bundleId) || null
  const estimated = estimateTotal(selectedSalon, selectedServices, bundleId === '' ? undefined : bundleId)
  const totalDuration = useMemo(() => {
    if (bundleId !== '') {
      const bundle = bundlesInSalon.find((item) => item.id === bundleId)
      if (!bundle) return 0
      return bundle.items.reduce((sum, item) => sum + (services.find((row) => row.id === item.service_id)?.duration_minutes ?? 0), 0)
    }
    return selectedServices.reduce((sum, serviceId) => sum + (services.find((row) => row.id === serviceId)?.duration_minutes ?? 0), 0)
  }, [bundleId, bundlesInSalon, selectedServices, services])

  const loadSalonStaff = async (salonId: number) => {
    setLoadingStaff(true)
    try {
      const res = await api.get<Array<{ id: number; first_name?: string | null; last_name?: string | null; can_be_booked: boolean; role_code?: string | null }>>(
        `/booking/salons/${salonId}/staff`,
        { params: { can_take_bookings: true } },
      )
      const rows = (res.data || [])
        .filter((row) => SPECIALIST_ROLE_CODES.has((row.role_code || '').toUpperCase()))
        .map((row) => ({
          id: row.id,
          displayName: composeStaffLabel(row.first_name, row.last_name) || `#${row.id}`,
          role_code: row.role_code,
          can_be_booked: row.can_be_booked,
        }))
      setSalonStaff(rows)
      setSelectedStaffId((prev) => {
        if (prev !== '' && rows.some((row) => row.id === prev)) return prev
        return rows[0]?.id ?? ''
      })
    } catch (err: any) {
      setSalonStaff([])
      setSelectedStaffId('')
      setFlash(err?.response?.data?.detail || 'Nie udalo sie pobrac listy pracownikow.')
    } finally {
      setLoadingStaff(false)
    }
  }

  useEffect(() => {
    setAvailabilityStatus(null)
    if (!selectedSalon) return
    loadSalonStaff(selectedSalon).catch(() => undefined)
  }, [selectedSalon])

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('calendar_view', calendarView)
    }
  }, [calendarView])

  useEffect(() => {
    const fetchCalendarAppointments = async () => {
      setCalendarLoading(true)
      try {
        if (!selectedSalon) {
          setCalendarAppointments([])
          return
        }
        if (calendarView === 'day') {
          const rangeStart = `${calendarDate}T00:00`
          const rangeEnd = `${calendarDate}T23:59`
          const res = await api.get<Appointment[]>('/booking/appointments', {
            params: {
              salon_id: selectedSalon,
              datefrom: rangeStart,
              dateto: rangeEnd,
              sort: 'start_asc',
            },
          })
          setCalendarAppointments(res.data || [])
        } else if (calendarView === 'week') {
          const baseDay = parseDate(`${calendarDate}T00:00`)
          const start = new Date(baseDay)
          start.setDate(baseDay.getDate() - (baseDay.getDay() === 0 ? 6 : baseDay.getDay() - 1))
          start.setHours(0, 0, 0, 0)
          const end = new Date(start)
          end.setDate(start.getDate() + 6)
          end.setHours(23, 59, 0, 0)
          const res = await api.get<Appointment[]>('/booking/appointments', {
            params: {
              salon_id: selectedSalon,
              datefrom: formatDateTimeLocal(start),
              dateto: formatDateTimeLocal(end),
              sort: 'start_asc',
            },
          })
          setCalendarAppointments(res.data || [])
        } else {
          const start = new Date(parseDate(`${calendarDate}T00:00`))
          start.setHours(0, 0, 0, 0)
          const end = new Date(start)
          end.setDate(start.getDate() + 29)
          end.setHours(23, 59, 59, 999)
          const res = await api.get<Appointment[]>('/booking/appointments', {
            params: {
              salon_id: selectedSalon,
              datefrom: formatDateTimeLocal(start),
              dateto: formatDateTimeLocal(end),
              sort: 'start_asc',
            },
          })
          setCalendarAppointments(res.data || [])
        }
      } catch (err: any) {
        setFlash(err?.response?.data?.detail || 'Nie udalo sie pobrac wizyt do widoku kalendarza.')
        setCalendarAppointments([])
      } finally {
        setCalendarLoading(false)
      }
    }
    fetchCalendarAppointments().catch(() => undefined)
  }, [appointments, calendarView, calendarDate, selectedSalon])

  const generateIssues = async (appointmentId: number) => {
    try {
      await api.post(`/appointments/${appointmentId}/generate-issues`)
      setFlash(`Wygenerowano rozchod dla wizyty #${appointmentId}.`)
      navigate(`/inventory/issues?appointment_id=${appointmentId}`)
    } catch (err: any) {
      setFlash(err?.response?.data?.detail || 'Nie udalo sie wygenerowac rozchodu.')
    }
  }

  const retailTotal = useMemo(
    () =>
      settlementRetailRows.reduce((sum, row) => {
        if (row.product_id === '') return sum
        const product = settlementProducts.find((item) => item.id === row.product_id)
        if (!product) return sum
        return sum + product.price * row.quantity
      }, 0),
    [settlementProducts, settlementRetailRows],
  )

  const settlementTotal = (invoicePreview?.net_total || 0) + retailTotal
  const settlementAllocationTotal = settlementAllocations.reduce((sum, row) => sum + (Number.isFinite(row.amount) ? row.amount : 0), 0)

  const loadSettlementProducts = async (salonId: number) => {
    const res = await api.get<Array<{ id: number; code: string; name: string; sale_price_gross?: number | null; salon_sale_price?: number | null }>>(
      '/legacy/catalog/products',
      { params: { salon_id: salonId } },
    )
    setSettlementProducts(
      (res.data || []).map((row) => ({
        id: row.id,
        code: row.code,
        name: row.name,
        price: Number(row.sale_price_gross ?? row.salon_sale_price ?? 0),
      })),
    )
  }

  const loadSettlementPromotions = async (salonId: number, appointmentId: number) => {
    const res = await api.get<PromotionOption[]>('/payments/promotions', {
      params: { salon_id: salonId, appointment_id: appointmentId },
    })
    setSettlementPromotions(res.data || [])
  }

  const loadInvoicePreview = async (appointmentId: number, useCard: boolean, invitationIds: number[]) => {
    const params = new URLSearchParams()
    params.set('use_card', String(useCard))
    invitationIds.forEach((id) => params.append('invitation_ids', String(id)))
    const res = await api.get<InvoicePreview>(`/appointments/${appointmentId}/invoice?${params.toString()}`)
    setInvoicePreview(res.data)
  }

  const openSettlement = async (appointmentId: number) => {
    const appointment = appointments.find((row) => row.id === appointmentId)
    if (!appointment) return
    setSettlementAppointmentId(appointmentId)
    setSettlementOpen(true)
    setSettlementLoading(true)
    setSettlementError('')
    setSettlementUseCard(false)
    setSettlementInvitationIds([])
    setSettlementRetailRows([])
    setSettlementPromotions([])
    setSettlementPromotionId('')
    setSettlementAllocations([{ method: 'cash', amount: 0, voucher_reference: '' }])
    try {
      await Promise.all([
        loadInvoicePreview(appointmentId, false, []),
        loadSettlementProducts(appointment.salon_id),
        loadSettlementPromotions(appointment.salon_id, appointmentId),
      ])
    } catch (err: any) {
      setSettlementError(err?.response?.data?.detail || 'Nie udalo sie pobrac danych rozliczenia.')
    } finally {
      setSettlementLoading(false)
    }
  }

  const addRetailRow = () => {
    setSettlementRetailRows((prev) => [...prev, { product_id: '', quantity: 1 }])
  }

  const updateRetailRow = (index: number, patch: Partial<RetailDraft>) => {
    setSettlementRetailRows((prev) => prev.map((row, rowIndex) => (rowIndex === index ? { ...row, ...patch } : row)))
  }

  const removeRetailRow = (index: number) => {
    setSettlementRetailRows((prev) => prev.filter((_, rowIndex) => rowIndex !== index))
  }

  const addSettlementAllocation = () => {
    setSettlementAllocations((prev) => [...prev, { method: 'card', amount: 0, voucher_reference: '' }])
  }

  const updateSettlementAllocation = (index: number, patch: Partial<PaymentAllocationDraft>) => {
    setSettlementAllocations((prev) => prev.map((row, rowIndex) => (rowIndex === index ? { ...row, ...patch } : row)))
  }

  const removeSettlementAllocation = (index: number) => {
    setSettlementAllocations((prev) => (prev.length <= 1 ? prev : prev.filter((_, rowIndex) => rowIndex !== index)))
  }

  const fillLastSettlementAllocation = () => {
    setSettlementAllocations((prev) => {
      if (!prev.length) return prev
      const totalWithoutLast = prev.slice(0, -1).reduce((sum, row) => sum + (Number.isFinite(row.amount) ? row.amount : 0), 0)
      const remainder = Math.max(0, Number((settlementTotal - totalWithoutLast).toFixed(2)))
      return prev.map((row, index) => (
        index === prev.length - 1 ? { ...row, amount: remainder } : row
      ))
    })
  }

  useEffect(() => {
    setSettlementAllocations((prev) => {
      if (prev.length !== 1) return prev
      const current = prev[0]
      if (Number(current.amount.toFixed(2)) === Number(settlementTotal.toFixed(2))) return prev
      return [{ ...current, amount: Number(settlementTotal.toFixed(2)) }]
    })
  }, [settlementTotal])

  const submitSettlement = async () => {
    if (!settlementAppointmentId || !invoicePreview) return
    const normalizedAllocations = settlementAllocations
      .map((row) => ({
        method: row.method,
        amount: Number(row.amount),
        voucher_reference: row.voucher_reference.trim(),
      }))
      .filter((row) => Number.isFinite(row.amount) && row.amount > 0)
    if (!normalizedAllocations.length) {
      setSettlementError('Podaj przynajmniej jedna alokacje platnosci.')
      return
    }
    if (Number(settlementAllocationTotal.toFixed(2)) !== Number(settlementTotal.toFixed(2))) {
      setSettlementError('Suma alokacji platnosci musi byc rowna kwocie do zaplaty.')
      return
    }
    if (normalizedAllocations.some((row) => row.method === 'voucher' && row.voucher_reference.length === 0)) {
      setSettlementError('Dla platnosci voucherem wpisz numer lub opis vouchera.')
      return
    }
    const selectedPromotion = settlementPromotionId === '' ? null : settlementPromotions.find((row) => row.id === settlementPromotionId) || null
    try {
      const payment = await api.post<{ id: number; pdf_url?: string }>(`/payments/${settlementAppointmentId}`, {
        amount: Number(settlementTotal.toFixed(2)),
        method: normalizedAllocations[0].method,
        use_card: settlementUseCard,
        invitation_ids: settlementInvitationIds,
        allocations: normalizedAllocations,
        promotion_id: selectedPromotion?.id,
        promotion_name: selectedPromotion?.name,
        retail_items: settlementRetailRows
          .filter((row) => row.product_id !== '')
          .map((row) => ({ product_id: Number(row.product_id), quantity: row.quantity })),
      })
      setFlash(`Rozliczono wizyte #${settlementAppointmentId}.`)
      setSettledAppointmentIds((prev) => (prev.includes(settlementAppointmentId) ? prev : [...prev, settlementAppointmentId]))
      setSettlementOpen(false)
      if (payment.data?.pdf_url) {
        window.open(payment.data.pdf_url, '_blank', 'noopener,noreferrer')
      }
    } catch (err: any) {
      setSettlementError(err?.response?.data?.detail || 'Nie udalo sie rozliczyc wizyty.')
    }
  }

  const canSubmitSettlement = !!invoicePreview && Number(settlementAllocationTotal.toFixed(2)) === Number(settlementTotal.toFixed(2))

  const createAppointment = async () => {
    if (selectedStaffId === '') {
      setFlash('Wybierz pracownika.')
      return false
    }
    if (clientMode === 'existing' && !clients.some((client) => client.id === clientId)) {
      setFlash('Wybierz poprawnego klienta.')
      return false
    }

    let targetClientId = clientId
    if (clientMode === 'new') {
      if (!newClientName || !newClientPhone) {
        setFlash('Dla nowego klienta podaj imie i nazwisko oraz telefon.')
        return false
      }
      const created = await addClient({ full_name: newClientName, phone: newClientPhone, email: newClientEmail })
      targetClientId = created.id
      setNewClientName('')
      setNewClientPhone('')
      setNewClientEmail('')
      setClientMode('existing')
      setClientId(created.id)
    }

    try {
      const created = await addAppointment({
        salon_id: selectedSalon,
        client_id: targetClientId,
        start_at: startAt,
        end_at: endAt,
        resources: [Number(selectedStaffId)],
        services: selectedServices,
        allow_overlap: allowOverlap,
        bundle_id: bundleId === '' ? undefined : bundleId,
      })
      setFlash('Wizyta dodana.')
      setSmsSuggestedAppointmentId(created.id)
      setAllowOverlap(false)
      return true
    } catch (err: any) {
      setFlash(err?.response?.data?.detail || 'Nie udalo sie dodac wizyty.')
      return false
    }
  }

  const sendSmsConfirmation = async (appointmentId: number) => {
    setSmsSending(true)
    try {
      await api.post(`/booking/appointments/${appointmentId}/sms-notify`)
      setFlash(`SMS potwierdzenia wyslany dla wizyty #${appointmentId}.`)
      setSmsSuggestedAppointmentId(null)
    } catch (err: any) {
      setFlash(err?.response?.data?.detail || 'Nie udalo sie wyslac SMS.')
    } finally {
      setSmsSending(false)
    }
  }

  const sendTodayBatchSms = async () => {
    setSmsSending(true)
    try {
      const res = await api.post<{ sent: number; failed: number }>('/booking/appointments/sms-notify-today', null, {
        params: { salon_id: selectedSalon },
      })
      setFlash(`Batch SMS: wyslane ${res.data?.sent ?? 0}, bledy ${res.data?.failed ?? 0}.`)
    } catch (err: any) {
      setFlash(err?.response?.data?.detail || 'Nie udalo sie wyslac batch SMS.')
    } finally {
      setSmsSending(false)
    }
  }

  const startExecution = (appointmentId: number) => {
    const appointment = appointmentsInSalon.find((item) => item.id === appointmentId)
    if (!appointment) return
    const bundle = appointment.bundle_id ? bundles.find((item) => item.id === appointment.bundle_id) : null
    const bundleItems = (bundle?.items || []).filter((item) => typeof item.service_id === 'number')
    const bundleServiceIds = bundleItems.map((item) => item.service_id as number)
    const serviceIds = appointment.services.length > 0 ? appointment.services : bundleServiceIds
    const fallbackSalonResources = resources.filter((item) => item.salon_id === appointment.salon_id)
    const defaultWorkerId = appointment.resources[0] ?? fallbackSalonResources[0]?.id ?? ''

    setExecutionAppointmentId(appointmentId)
    setExecutionError('')
    setExecutionPerformedAt(appointment.end_at.slice(0, 16))
    if (bundleItems.length > 0 && appointment.services.length === 0) {
      setExecutionLines(
        bundleItems.map((item) =>
          buildExecutionLineDraft(
            appointment.salon_id,
            item.service_id as number,
            defaultWorkerId,
            item.override_price,
          ),
        ),
      )
      return
    }
    setExecutionLines((serviceIds.length > 0 ? serviceIds : ['']).map((serviceId) => buildExecutionLineDraft(appointment.salon_id, serviceId as number | '', defaultWorkerId)))
  }

  const addExecutionLine = () => {
    if (!executionAppointment) {
      setExecutionLines((prev) => [...prev, { service_id: '', worker_id: '', worker_role_id: '', price_snapshot: 0, resources: [] }])
      return
    }
    const workerId = executionLines[executionLines.length - 1]?.worker_id || executionAppointment.resources[0] || executionWorkerOptions[0]?.id || ''
    setExecutionLines((prev) => [...prev, buildExecutionLineDraft(executionAppointment.salon_id, '', workerId)])
  }

  const setExecutionLine = (index: number, patch: Partial<ExecutionLineDraft>) => {
    setExecutionLines((prev) => prev.map((line, i) => (i === index ? { ...line, ...patch } : line)))
  }

  const setExecutionResource = (
    lineIndex: number,
    resourceIndex: number,
    patch: Partial<ExecutionLineResourceDraft>,
  ) => {
    setExecutionLines((prev) => prev.map((line, currentLineIndex) => {
      if (currentLineIndex !== lineIndex) return line
      return {
        ...line,
        resources: line.resources.map((resource, currentResourceIndex) => (
          currentResourceIndex === resourceIndex ? { ...resource, ...patch } : resource
        )),
      }
    }))
  }

  const removeExecutionLine = (index: number) => {
    setExecutionLines((prev) => prev.filter((_, i) => i !== index))
  }

  const fillExecutionQuantitiesFromPlan = () => {
    setExecutionLines((prev) =>
      prev.map((line) => ({
        ...line,
        resources: line.resources.map((resource) => {
          const recipeItems =
            typeof line.service_id === 'number' ? executionRecipesByService[line.service_id] || [] : []
          const recipeItem = recipeItems.find((item) => item.id === resource.recipe_item_id)
          if (!recipeItem) return resource
          if (Number.isFinite(resource.quantity_used) && resource.quantity_used > 0) return resource
          return {
            ...resource,
            quantity_used: getRecipePlannedQuantity(recipeItem),
          }
        }),
      })),
    )
  }

  const executionAppointment = useMemo(
    () => (executionAppointmentId === '' ? null : appointments.find((item) => item.id === executionAppointmentId) || null),
    [appointments, executionAppointmentId],
  )

  const executionWorkerOptions = useMemo(() => {
    if (!executionAppointment) return []
    const byId = new Map(resources.filter((item) => item.salon_id === executionAppointment.salon_id).map((item) => [item.id, item]))
    return salonStaff
      .map((row) => byId.get(row.id))
      .filter((row): row is NonNullable<typeof row> => Boolean(row))
  }, [executionAppointment, resources, salonStaff])

  const replaceExecutionLinesWithBundle = (bundleId: number, lineIndex = 0) => {
    if (!executionAppointment) return
    const workerId = executionLines[lineIndex]?.worker_id || executionLines[lineIndex - 1]?.worker_id || executionAppointment.resources[0] || executionWorkerOptions[0]?.id || ''
    const bundle = bundlesInSalon.find((item) => item.id === bundleId)
    if (!bundle) return
    const nextLines = bundle.items
      .filter((item) => typeof item.service_id === 'number')
      .map((item) => buildExecutionLineDraft(executionAppointment.salon_id, item.service_id as number, workerId, item.override_price))
    if (!nextLines.length) return
    setExecutionLines((prev) => [...prev.slice(0, lineIndex), ...nextLines, ...prev.slice(lineIndex + 1)])
  }

  const getServiceBasePrice = (salonId: number, serviceId: number) =>
    priceListItems.find((item) => item.salon_id === salonId && item.service_id === serviceId)?.price ?? 0

  const buildRecipeResourceDrafts = (
    serviceId: number | '',
    existingResources: ExecutionLineResourceDraft[] = [],
  ): ExecutionLineResourceDraft[] => {
    if (typeof serviceId !== 'number') return []
    const recipeItems = (executionRecipesByService[serviceId] || []).filter((item) => !isRecipeStocktakeOnly(item))
    if (!recipeItems.length) return []
    const existingByRecipe = new Map(existingResources.map((item) => [item.recipe_item_id, item]))
    return recipeItems.map((item) => {
      const existing = existingByRecipe.get(item.id)
      return {
        recipe_item_id: item.id,
        product_id: existing?.product_id ?? item.product_id ?? '',
        quantity_used: existing?.quantity_used ?? getRecipePlannedQuantity(item),
      }
    })
  }

  const buildExecutionLineDraft = (
    salonId: number,
    serviceId: number | '',
    workerId: number | '' = '',
    overridePrice?: number,
  ): ExecutionLineDraft => {
    const worker = resources.find((item) => item.id === workerId)
    const roleId = worker?.role_ids.find((id) => bookableRoleIds.includes(id)) ?? worker?.role_ids[0] ?? ''
    return {
      service_id: serviceId,
      worker_id: workerId,
      worker_role_id: roleId,
      price_snapshot:
        typeof serviceId === 'number'
          ? Number(overridePrice ?? getServiceBasePrice(salonId, serviceId))
          : 0,
      resources: buildRecipeResourceDrafts(serviceId),
    }
  }

  const applyExecutionSelection = (index: number, selection: string) => {
    if (!executionAppointment) return
    const workerId = executionLines[index]?.worker_id || executionLines[index - 1]?.worker_id || executionAppointment.resources[0] || executionWorkerOptions[0]?.id || ''

    if (!selection) {
      setExecutionLines((prev) => prev.map((line, lineIndex) => (
        lineIndex === index ? buildExecutionLineDraft(executionAppointment.salon_id, '', workerId) : line
      )))
      return
    }

    const [kind, rawId] = selection.split(':')
    const itemId = Number(rawId)
    if (!Number.isFinite(itemId)) return

    if (kind === 'service') {
      setExecutionLines((prev) => prev.map((line, lineIndex) => (
        lineIndex === index ? buildExecutionLineDraft(executionAppointment.salon_id, itemId, workerId) : line
      )))
      return
    }

    if (kind === 'bundle') {
      replaceExecutionLinesWithBundle(itemId, index)
    }
  }

  useEffect(() => {
    if (!executionAppointment) {
      setExecutionProducts([])
      setExecutionProductsByFamily({})
      setExecutionRecipesByService({})
      return
    }
    api.get<Array<{ id: number; code: string; name: string; family_code?: string | null }>>('/colors', {
      params: { salon_id: executionAppointment.salon_id, backbar: true },
    })
      .then((res) => {
        const rows = (res.data || []).map((row) => ({
          id: row.id,
          code: row.code,
          name: row.name,
          family_code: row.family_code,
        }))
        setExecutionProducts(rows)
        setExecutionProductsByFamily({ __ALL__: rows })
      })
      .catch(() => {
        setExecutionProducts([])
        setExecutionProductsByFamily({})
      })
  }, [executionAppointment])

  useEffect(() => {
    const missingServiceIds = executionLines
      .map((line) => line.service_id)
      .filter((serviceId): serviceId is number => typeof serviceId === 'number' && !(serviceId in executionRecipesByService))
    if (!missingServiceIds.length) return

    Promise.all(
      missingServiceIds.map(async (serviceId) => {
        const res = await api.get<Array<{
          id: number
          product_id?: number | null
          product_family?: string | null
          product_name?: string | null
          product_label_snapshot?: string | null
          is_required?: boolean
          quantity_mode?: string | null
          planned_quantity?: number | null
          planned_min?: number | null
          planned_default?: number | null
          planned_max?: number | null
          unit?: string | null
          recipe_unit_label?: string | null
          inventory_mode?: string | null
          note?: string | null
          total_label?: string | null
        }>>(`/services/${serviceId}/recipe`)
        return [serviceId, res.data || []] as const
      }),
    )
      .then((pairs) => {
        setExecutionRecipesByService((prev) => {
          const next = { ...prev }
          pairs.forEach(([serviceId, rows]) => {
            next[serviceId] = rows
          })
          return next
        })
      })
      .catch(() => undefined)
  }, [executionLines, executionRecipesByService])

  useEffect(() => {
    if (!Object.keys(executionRecipesByService).length) return
    setExecutionLines((prev) => prev.map((line) => ({
      ...line,
      resources: buildRecipeResourceDrafts(line.service_id, line.resources),
    })))
  }, [executionRecipesByService])

  useEffect(() => {
    if (!executionAppointment) return
    const families = [...new Set(
      Object.values(executionRecipesByService)
        .flat()
        .map((item) => (item.product_family || '').trim())
        .filter(Boolean),
    )]
    const missingFamilies = families.filter((family) => !(family.toUpperCase() in executionProductsByFamily))
    if (!missingFamilies.length) return

    Promise.all(
      missingFamilies.map(async (family) => {
        const res = await api.get<Array<{ id: number; code: string; name: string; family_code?: string | null }>>('/colors', {
          params: { salon_id: executionAppointment.salon_id, family, backbar: true },
        })
        return [family.toUpperCase(), (res.data || []).map((row) => ({
          id: row.id,
          code: row.code,
          name: row.name,
          family_code: row.family_code,
        }))] as const
      }),
    )
      .then((pairs) => {
        setExecutionProductsByFamily((prev) => {
          const next = { ...prev }
          pairs.forEach(([family, items]) => {
            next[family] = items
          })
          return next
        })
      })
      .catch(() => undefined)
  }, [executionAppointment, executionProductsByFamily, executionRecipesByService])

  const saveExecution = async () => {
    setExecutionError('')
    if (executionAppointmentId === '') return
    if (executionLines.length === 0) {
      setExecutionError('Dodaj przynajmniej jedna linie zabiegu.')
      return
    }

    const invalid = executionLines.some(
      (line) =>
        line.service_id === '' ||
        line.worker_id === '' ||
        line.worker_role_id === '' ||
        !Number.isFinite(line.price_snapshot) ||
        line.price_snapshot < 0,
    )
    if (invalid) {
      setExecutionError('Uzupelnij komplet danych wykonania: usluga/forfet, pracownik i cena.')
      return
    }

    const missingRecipeProduct = executionLines.some((line) => {
      if (typeof line.service_id !== 'number') return false
      const recipeItems = (executionRecipesByService[line.service_id] || []).filter((item) => !isRecipeStocktakeOnly(item))
      const requiredItems = recipeItems.filter(isRecipeRequiredPerService)
      if (!requiredItems.length) return false
      const resourceByRecipeId = new Map(line.resources.map((resource) => [resource.recipe_item_id, resource]))
      return requiredItems.some((recipeItem) => {
        const resource = resourceByRecipeId.get(recipeItem.id)
        return !resource || resource.product_id === '' || !Number.isFinite(resource.quantity_used) || resource.quantity_used <= 0
      })
    })
    if (missingRecipeProduct) {
      setExecutionError('Uzupelnij wszystkie wymagane zasoby z receptury wraz z iloscia zuzycia.')
      return
    }

    try {
      await completeAppointment({
        appointment_id: executionAppointmentId,
        performed_at: executionPerformedAt,
        lines: executionLines.map((line) => ({
          service_id: Number(line.service_id),
          worker_id: Number(line.worker_id),
          worker_role_id: Number(line.worker_role_id),
          price_snapshot: Number(line.price_snapshot),
          color_product_id: (() => {
            const firstResourceProductId = line.resources.find((resource) => resource.product_id !== '')?.product_id
            return typeof firstResourceProductId === 'number' ? firstResourceProductId : undefined
          })(),
          resources: line.resources
            .filter((resource) => resource.product_id !== '' && Number.isFinite(resource.quantity_used) && resource.quantity_used > 0)
            .map((resource) => ({
              recipe_item_id: resource.recipe_item_id,
              product_id: Number(resource.product_id),
              quantity_used: Number(resource.quantity_used),
            })),
        })),
      })
      setExecutionAppointmentId('')
      setExecutionLines([])
      setExecutionError('')
      setFlash('Wizyta oznaczona jako wykonana.')
      await openSettlement(executionAppointmentId)
    } catch {
      setExecutionError('Nie udalo sie zapisac wykonania wizyty.')
    }
  }

  useEffect(() => {
    if (selectedStaffId === '' || !startAt || !endAt) {
      setAvailabilityStatus(null)
      return
    }

    const wantedStart = parseDate(startAt)
    const wantedEnd = parseDate(endAt)
    if (Number.isNaN(wantedStart.getTime()) || Number.isNaN(wantedEnd.getTime()) || wantedStart >= wantedEnd) {
      setAvailabilityStatus({ busy: true, message: 'Sprawdz termin: koniec musi byc po starcie.' })
      return
    }

    const resourceAppointments = appointmentsInSalon.filter((appointment) =>
      appointment.resources.includes(Number(selectedStaffId)),
    )
    const busy = resourceAppointments.some((appointment) =>
      !appointment.allow_overlap &&
      overlaps(wantedStart, wantedEnd, parseDate(appointment.start_at), parseDate(appointment.end_at)),
    )

    if (busy && !allowOverlap) {
      setAvailabilityStatus({ busy: true, message: 'Wybrany pracownik jest zajety w tym terminie.' })
    } else if (busy && allowOverlap) {
      setAvailabilityStatus({ busy: false, message: 'Termin koliduje, ale zostanie zapisany jako wizyta na zakladke.' })
    } else {
      setAvailabilityStatus({ busy: false, message: 'Wybrany pracownik jest wolny w tym terminie.' })
    }
  }, [allowOverlap, appointmentsInSalon, endAt, selectedStaffId, startAt])

  useEffect(() => {
    if (!settlementOpen || settlementAppointmentId === null) return
    loadInvoicePreview(settlementAppointmentId, settlementUseCard, settlementInvitationIds).catch((err: any) => {
      setSettlementError(err?.response?.data?.detail || 'Nie udalo sie odswiezyc rozliczenia.')
    })
  }, [settlementAppointmentId, settlementInvitationIds, settlementOpen, settlementUseCard])

  const showInlineForm = false

  const prefillAppointment = (slotStart: Date, staffId?: number) => {
    if (!canCreateAppointments) return
    const duration = totalDuration > 0 ? totalDuration : 60
    const slotEnd = new Date(slotStart.getTime() + duration * 60_000)
    setStartAt(formatDateTimeLocal(slotStart))
    setEndAt(formatDateTimeLocal(slotEnd))
    const preferredStaffId = staffId ?? salonStaff[0]?.id
    if (preferredStaffId) setSelectedStaffId(preferredStaffId)
    setCalendarDate(formatDateOnly(slotStart))
    setAvailabilityStatus(null)
    setAllowOverlap(false)
    setAppointmentDialogOpen(true)
  }

  const isPastSlot = (slotStart: Date) => {
    const now = new Date()
    return slotStart.getTime() < now.getTime()
  }

  const selectedDay = useMemo(() => {
    const parsed = parseDate(`${calendarDate}T00:00`)
    return Number.isNaN(parsed.getTime()) ? new Date() : parsed
  }, [calendarDate])

  const weekDays = useMemo(() => {
    const base = new Date(selectedDay)
    const jsDay = base.getDay()
    const diffToMonday = jsDay === 0 ? -6 : 1 - jsDay
    const monday = new Date(base)
    monday.setDate(base.getDate() + diffToMonday)
    return Array.from({ length: 7 }, (_, index) => {
      const value = new Date(monday)
      value.setDate(monday.getDate() + index)
      return value
    })
  }, [selectedDay])

  useEffect(() => {
    const loadScheduleWindows = async () => {
      if (!selectedSalon || salonStaff.length === 0) {
        setStaffWorkWindowsByKey({})
        return
      }

      const rangeStart = new Date(selectedDay)
      rangeStart.setHours(0, 0, 0, 0)
      const rangeEnd = new Date(rangeStart)
      if (calendarView === 'day') {
        rangeEnd.setDate(rangeStart.getDate())
      } else if (calendarView === 'week') {
        rangeEnd.setDate(rangeStart.getDate() + 6)
      } else {
        rangeEnd.setDate(rangeStart.getDate() + 34)
      }

      const dateFrom = formatDateOnly(rangeStart)
      const dateTo = formatDateOnly(rangeEnd)
      const dateKeys: string[] = []
      const cursor = new Date(rangeStart)
      while (cursor <= rangeEnd) {
        dateKeys.push(formatDateOnly(cursor))
        cursor.setDate(cursor.getDate() + 1)
      }

      try {
        const perStaff = await Promise.all(
          salonStaff.map(async (staff) => {
            const [monthlyRes, weeklyRes, timeOffRes] = await Promise.all([
              api.get<StaffMonthlyScheduleApi[]>(`/booking/staff/${staff.id}/monthly-schedule`, {
                params: { date_from: dateFrom, date_to: dateTo },
              }),
              api.get<StaffWeeklyScheduleApi[]>(`/booking/staff/${staff.id}/schedule`),
              api.get<StaffTimeOffApi[]>(`/booking/staff/${staff.id}/time-off`),
            ])
            return {
              staffId: staff.id,
              monthly: (monthlyRes.data || []).filter((row) => row.is_active && row.salon_id === selectedSalon),
              weekly: (weeklyRes.data || []).filter((row) => row.is_active && row.salon_id === selectedSalon),
              timeOff: (timeOffRes.data || []).filter((row) => row.salon_id === selectedSalon),
            }
          }),
        )

        const next: Record<string, Array<[number, number]>> = {}
        perStaff.forEach((staffData) => {
          const monthlyByDate = new Map<string, StaffMonthlyScheduleApi[]>()
          staffData.monthly.forEach((row) => {
            const dateKey = String(row.work_date).slice(0, 10)
            const list = monthlyByDate.get(dateKey) || []
            list.push(row)
            monthlyByDate.set(dateKey, list)
          })
          const weeklyByWeekday = new Map<number, StaffWeeklyScheduleApi[]>()
          staffData.weekly.forEach((row) => {
            const list = weeklyByWeekday.get(row.weekday) || []
            list.push(row)
            weeklyByWeekday.set(row.weekday, list)
          })

          dateKeys.forEach((dateKey) => {
            const day = new Date(`${dateKey}T00:00`)
            const monthlyRows = monthlyByDate.get(dateKey) || []
            const sourceRows = monthlyRows.length > 0 ? monthlyRows : (weeklyByWeekday.get((day.getDay() + 6) % 7) || [])

            let intervals: Array<[number, number]> = sourceRows.map((row) => {
              const start = parseTimeToDate(dateKey, row.time_from).getTime()
              const end = parseTimeToDate(dateKey, row.time_to).getTime()
              return [start, end]
            })

            const dayStart = new Date(`${dateKey}T00:00:00`).getTime()
            const dayEnd = new Date(`${dateKey}T23:59:59`).getTime()
            staffData.timeOff.forEach((row) => {
              const offStart = new Date(row.start_datetime).getTime()
              const offEnd = new Date(row.end_datetime).getTime()
              if (offEnd <= dayStart || offStart >= dayEnd) return
              intervals = subtractIntervalsTs(intervals, offStart, offEnd)
            })
            next[`${staffData.staffId}|${dateKey}`] = intervals
          })
        })
        setStaffWorkWindowsByKey(next)
      } catch {
        setStaffWorkWindowsByKey({})
      }
    }
    loadScheduleWindows().catch(() => undefined)
  }, [calendarView, salonStaff, selectedDay, selectedSalon])

  const isSlotWithinStaffSchedule = (staffId: number, slotStart: Date, slotEnd: Date) => {
    const dateKey = formatDateOnly(slotStart)
    const intervals = staffWorkWindowsByKey[`${staffId}|${dateKey}`] || []
    const startTs = slotStart.getTime()
    const endTs = slotEnd.getTime()
    return intervals.some(([windowStart, windowEnd]) => startTs >= windowStart && endTs <= windowEnd)
  }

  const specialistStaffIds = useMemo(() => new Set(salonStaff.map((row) => row.id)), [salonStaff])
  const rollingVisibleStaffIds = useMemo(() => {
    let filtered = salonStaff
    if (rollingRoleFilter === 'hairdresser') filtered = filtered.filter((row) => isHairdresserRole(row.role_code))
    if (rollingRoleFilter === 'manicure') filtered = filtered.filter((row) => isManicureRole(row.role_code))
    if (rollingStaffFilter !== '') filtered = filtered.filter((row) => row.id === rollingStaffFilter)
    return new Set(filtered.map((row) => row.id))
  }, [rollingRoleFilter, rollingStaffFilter, salonStaff])

  const detailAppointment = useMemo(
    () => [...appointmentsInSalon, ...calendarAppointments].find((row) => row.id === detailsAppointmentId) || null,
    [appointmentsInSalon, calendarAppointments, detailsAppointmentId],
  )

  useEffect(() => {
    if (detailsAppointmentId === null) {
      setDetailResources([])
      return
    }
    api.get<PerformedResourceDetail[]>(`/booking/appointments/${detailsAppointmentId}/performed-resources`)
      .then((res) => setDetailResources(res.data || []))
      .catch(() => setDetailResources([]))
  }, [detailsAppointmentId])

  const dayAppointments = useMemo(() => {
    const start = new Date(selectedDay)
    start.setHours(0, 0, 0, 0)
    const end = new Date(selectedDay)
    end.setHours(23, 59, 59, 999)
    return calendarAppointments.filter((row) => {
      const rowStart = parseDate(row.start_at)
      const rowEnd = parseDate(row.end_at)
      const hasVisibleSpecialist = row.resources.some((staffId) => specialistStaffIds.has(staffId))
      return overlaps(start, end, rowStart, rowEnd) && hasVisibleSpecialist
    })
  }, [calendarAppointments, selectedDay, specialistStaffIds])

  const weekAppointments = useMemo(() => {
    const start = new Date(weekDays[0])
    start.setHours(0, 0, 0, 0)
    const end = new Date(weekDays[6])
    end.setHours(23, 59, 59, 999)
    return calendarAppointments.filter((row) => {
      const rowStart = parseDate(row.start_at)
      const rowEnd = parseDate(row.end_at)
      const hasVisibleSpecialist = row.resources.some((staffId) => specialistStaffIds.has(staffId))
      return overlaps(start, end, rowStart, rowEnd) && hasVisibleSpecialist
    })
  }, [calendarAppointments, specialistStaffIds, weekDays])

  const rolling30Weeks = useMemo(() => {
    const start = new Date(selectedDay)
    start.setHours(0, 0, 0, 0)
    return Array.from({ length: 5 }, (_, weekIndex) =>
      Array.from({ length: 7 }, (_, dayIndex) => {
        const value = new Date(start)
        value.setDate(start.getDate() + weekIndex * 7 + dayIndex)
        return value
      }),
    )
  }, [selectedDay])

  const rolling30AppointmentsFiltered = useMemo(
    () => calendarAppointments.filter((row) => row.resources.some((staffId) => rollingVisibleStaffIds.has(staffId))),
    [calendarAppointments, rollingVisibleStaffIds],
  )

  const halfHourSlots = useMemo(
    () => Array.from({ length: ((SLOT_END_HOUR - SLOT_START_HOUR) * 60) / SLOT_DURATION_MINUTES }, (_, index) => {
      const totalMinutes = index * SLOT_DURATION_MINUTES
      const hour = SLOT_START_HOUR + Math.floor(totalMinutes / 60)
      const minute = totalMinutes % 60
      return { index, label: `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}` }
    }),
    [],
  )

  const getClientName = (clientIdValue: number) => clients.find((c) => c.id === clientIdValue)?.full_name || `#${clientIdValue}`
  const getClientLastName = (clientIdValue: number) => {
    const fullName = getClientName(clientIdValue).trim()
    const parts = fullName.split(' ').filter(Boolean)
    return parts.length > 1 ? parts[parts.length - 1] : fullName
  }
  const getClientLastFirst = (clientIdValue: number) => {
    const fullName = getClientName(clientIdValue).trim()
    const parts = fullName.split(' ').filter(Boolean)
    if (parts.length < 2) return fullName
    return `${parts[parts.length - 1]} ${parts[0]}`
  }
  const getResourceName = (resourceId: number) =>
    normalizeRepeatedLabel(resources.find((resource) => resource.id === resourceId)?.name) || `#${resourceId}`
  const getServiceLabel = (serviceIds: number[]) => serviceIds.map((id) => services.find((service) => service.id === id)?.name).filter(Boolean).join(', ')
  const getPackageLabel = (appointment: Appointment) =>
    appointment.bundle_id ? bundles.find((bundle) => bundle.id === appointment.bundle_id)?.name || '' : ''
  const getAppointmentOfferLabel = (appointment: Appointment) => {
    const packageLabel = getPackageLabel(appointment)
    if (packageLabel) return packageLabel
    const serviceLabel = getServiceLabel(appointment.services)
    return serviceLabel || 'Bez uslugi'
  }
  const getCompactOfferLabel = (appointment: Appointment, maxLength = 18) => {
    const value = getAppointmentOfferLabel(appointment)
    return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value
  }
  const getStaffLabel = (resourceIds: number[]) => resourceIds.map((id) => getResourceName(id)).filter(Boolean).join(', ')
  const getAppointmentRoleColor = (appointment: Appointment) => {
    const specialistId = appointment.resources.find((id) => specialistStaffIds.has(id))
    const roleCode = salonStaff.find((staff) => staff.id === specialistId)?.role_code
    return getStaffRoleColor(roleCode)
  }

  const renderDayView = () => {
    const columnHeight = halfHourSlots.length * HALF_HOUR_ROW_HEIGHT
    const majorLineColor = '#cbd5e1'
    const minorLineColor = '#e5e7eb'
    return (
      <Card>
        <CardContent>
          <Stack direction="row" spacing={1} sx={{ mb: 1 }} alignItems="center">
            <Chip size="small" label="Poza grafikiem" sx={{ bgcolor: '#fca5a5' }} />
            <Chip size="small" label="Godzina miniona" sx={{ bgcolor: '#9ca3af', color: '#fff' }} />
          </Stack>
          <Box sx={{ display: 'grid', gridTemplateColumns: `72px repeat(${Math.max(salonStaff.length, 1)}, minmax(180px, 1fr))`, gap: 1 }}>
            <Box />
            {(salonStaff.length ? salonStaff : [{ id: 0, displayName: 'Brak pracownikow', can_be_booked: false }]).map((staff) => (
              <Typography
                key={staff.id}
                sx={{
                  fontWeight: 700,
                  textAlign: 'center',
                  color: staff.id ? getStaffRoleColor(staff.role_code) : 'text.primary',
                }}
              >
                {staff.displayName}
              </Typography>
            ))}
            <Box sx={{ position: 'relative', height: columnHeight }}>
              {halfHourSlots.map((slot) => (
                <Box
                  key={slot.index}
                  sx={{
                    height: HALF_HOUR_ROW_HEIGHT,
                    borderTop: `1px solid ${slot.index % 2 === 0 ? majorLineColor : minorLineColor}`,
                    pr: 1,
                    bgcolor: slot.index % 2 === 0 ? '#f8fafc' : 'transparent',
                  }}
                >
                  <Typography variant="caption" sx={{ fontWeight: slot.index % 2 === 0 ? 700 : 500 }}>{slot.label}</Typography>
                </Box>
              ))}
            </Box>
            {(salonStaff.length ? salonStaff : []).map((staff) => {
              const staffAppointments = dayAppointments.filter((appointment) => appointment.resources.includes(staff.id))
              const positionedAppointments = buildDayAppointmentLayout(staffAppointments)
              return (
                <Box key={staff.id} sx={{ position: 'relative', height: columnHeight, border: `1px solid ${majorLineColor}`, borderRadius: 2, overflow: 'hidden' }}>
                  {halfHourSlots.map((slot) => {
                    const slotTime = new Date(selectedDay)
                    slotTime.setHours(SLOT_START_HOUR + Math.floor(slot.index / 2), slot.index % 2 === 0 ? 0 : 30, 0, 0)
                    const slotEnd = new Date(slotTime.getTime() + SLOT_DURATION_MINUTES * 60_000)
                    const past = isPastSlot(slotTime)
                    const inSchedule = isSlotWithinStaffSchedule(staff.id, slotTime, slotEnd)
                    return (
                      <Box
                        key={`${staff.id}-${slot.index}`}
                        onClick={() => {
                          if (past || !canCreateAppointments || !inSchedule) return
                          prefillAppointment(slotTime, staff.id)
                        }}
                        sx={{
                          height: HALF_HOUR_ROW_HEIGHT,
                          borderTop: `1px solid ${slot.index % 2 === 0 ? majorLineColor : minorLineColor}`,
                          cursor: (past || !canCreateAppointments || !inSchedule) ? 'default' : 'pointer',
                          bgcolor: !inSchedule
                            ? (slot.index % 2 === 0 ? '#fca5a5' : '#fecaca')
                            : (past ? '#9ca3af' : (slot.index % 2 === 0 ? '#f8fafc' : 'transparent')),
                        }}
                      />
                    )
                  })}
                  {positionedAppointments.filter(({ lane }) => lane < 3).map(({ appointment, lane, laneCount }) => {
                    const start = parseDate(appointment.start_at)
                    const end = parseDate(appointment.end_at)
                    const placement = clampAppointmentToGrid(start, end)
                    if (!placement) return null
                    const top = (placement.minutesFromGridStart / SLOT_DURATION_MINUTES) * HALF_HOUR_ROW_HEIGHT
                    const height = (placement.durationMinutes / SLOT_DURATION_MINUTES) * HALF_HOUR_ROW_HEIGHT
                    const gap = 4
                    const widthCalc = `calc((100% - ${(laneCount + 1) * gap}px) / ${laneCount})`
                    const clientLastName = getClientLastName(appointment.client_id)
                    const offerLabel = getAppointmentOfferLabel(appointment)
                    const compactOffer = getCompactOfferLabel(appointment, 16)
                    const timeLabel = formatTimeRange(start, end)
                    const canSettleInline = appointment.status === 'done' && !settledAppointmentIds.includes(appointment.id)
                    return (
                      <Box
                        key={`${staff.id}-${appointment.id}`}
                        onClick={(event) => {
                          event.stopPropagation()
                          setDetailsAppointmentId(appointment.id)
                        }}
                        sx={{
                          position: 'absolute',
                          left: `calc(${gap}px + (${lane} * (${widthCalc} + ${gap}px)))`,
                          width: widthCalc,
                          top,
                          height,
                          bgcolor: getStatusBackground(appointment.status),
                          color: '#fff',
                          borderRadius: 1,
                          p: 0.75,
                          fontSize: 12,
                          overflow: 'hidden',
                          cursor: 'pointer',
                          border: laneCount > 1 ? '2px solid #ef4444' : '1px solid transparent',
                          boxShadow: `inset 0 0 0 1px ${getAppointmentRoleColor(appointment)}99`,
                        }}
                      >
                        <Typography variant="caption" sx={{ color: '#fff', display: 'block', fontWeight: 700 }}>
                          {clientLastName}
                        </Typography>
                        <Typography variant="caption" sx={{ color: '#fff', display: 'block' }}>
                          {height < 72 ? compactOffer : offerLabel}
                        </Typography>
                        <Typography variant="caption" sx={{ color: '#fff', display: 'block' }}>
                          {timeLabel}
                        </Typography>
                        {canSettleInline && height >= 84 && (
                          <Button
                            size="small"
                            variant="contained"
                            onClick={(event) => {
                              event.stopPropagation()
                              openSettlement(appointment.id).catch(() => undefined)
                            }}
                            sx={{
                              mt: 0.5,
                              minWidth: 0,
                              px: 0.75,
                              py: 0.25,
                              fontSize: 10,
                              lineHeight: 1.1,
                              bgcolor: 'rgba(255,255,255,0.18)',
                              color: '#fff',
                              border: '1px solid rgba(255,255,255,0.45)',
                              '&:hover': { bgcolor: 'rgba(255,255,255,0.28)' },
                            }}
                          >
                            Rozlicz
                          </Button>
                        )}
                      </Box>
                    )
                  })}
                </Box>
              )
            })}
          </Box>
          {!salonStaff.length && <Alert severity="info" sx={{ mt: 2 }}>Brak pracownikow dla wybranego salonu.</Alert>}
        </CardContent>
      </Card>
    )
  }

  const renderWeekGrid = (
    days: Date[],
    sourceAppointments: Appointment[],
    keyPrefix: string,
    options?: { rowHeight?: number; compact?: boolean; hideEverySecondLabel?: boolean; scrollMaxHeight?: number | string; stickyHeader?: boolean },
  ) => {
    const rowHeight = options?.rowHeight ?? WEEK_SLOT_ROW_HEIGHT
    const compact = options?.compact ?? false
    const hideEverySecondLabel = options?.hideEverySecondLabel ?? true
    const stickyHeader = options?.stickyHeader ?? false
    const columnHeight = halfHourSlots.length * rowHeight
    const majorLineColor = '#cbd5e1'
    const minorLineColor = '#e5e7eb'
    return (
      <Box sx={{ overflow: options?.scrollMaxHeight ? 'auto' : 'visible', maxHeight: options?.scrollMaxHeight ?? 'none' }}>
      <Box sx={{ display: 'grid', gridTemplateColumns: '72px repeat(7, minmax(180px, 1fr))', gap: 1, minWidth: 1200 }}>
        <Box />
        {days.map((day) => (
          <Typography
            key={`${keyPrefix}-head-${day.toISOString()}`}
            sx={{
              fontWeight: 700,
              textAlign: 'center',
              ...(stickyHeader ? { position: 'sticky', top: 0, zIndex: 2, bgcolor: '#f8fafc', py: 0.25 } : undefined),
            }}
          >
            {day.toLocaleDateString('pl-PL', { weekday: 'short', day: '2-digit', month: '2-digit' })}
          </Typography>
        ))}
        <Box sx={{ position: 'relative', height: columnHeight, ...(stickyHeader ? { position: 'sticky', left: 0, zIndex: 1, bgcolor: '#f8fafc' } : undefined) }}>
          {halfHourSlots.map((slot) => (
            <Box
              key={`${keyPrefix}-time-${slot.index}`}
              sx={{
                height: rowHeight,
                borderTop: `1px solid ${slot.index % 2 === 0 ? majorLineColor : minorLineColor}`,
                pr: 1,
                bgcolor: slot.index % 2 === 0 ? '#f8fafc' : 'transparent',
              }}
            >
              <Typography variant="caption" sx={{ fontWeight: slot.index % 2 === 0 ? 700 : 500 }}>
                {hideEverySecondLabel ? (slot.index % 2 === 0 ? slot.label : '') : slot.label}
              </Typography>
            </Box>
          ))}
        </Box>
        {days.map((day) => {
          const dayStart = new Date(day)
          dayStart.setHours(0, 0, 0, 0)
          const dayEnd = new Date(day)
          dayEnd.setHours(23, 59, 59, 999)
          const dayRows = sourceAppointments.filter((appointment) =>
            overlaps(dayStart, dayEnd, parseDate(appointment.start_at), parseDate(appointment.end_at)),
          )
          const positionedAppointments = buildDayAppointmentLayout(dayRows)
          return (
            <Box key={`${keyPrefix}-day-${day.toISOString()}`} sx={{ position: 'relative', height: columnHeight, border: `1px solid ${majorLineColor}`, borderRadius: 2, overflow: 'hidden' }}>
              {halfHourSlots.map((slot) => {
                const slotTime = new Date(day)
                const totalMinutes = slot.index * SLOT_DURATION_MINUTES
                slotTime.setHours(SLOT_START_HOUR + Math.floor(totalMinutes / 60), totalMinutes % 60, 0, 0)
                const past = isPastSlot(slotTime)
                return (
                  <Box
                    key={`${keyPrefix}-${day.toISOString()}-${slot.index}`}
                    onClick={() => {
                      if (past || !canCreateAppointments) return
                      prefillAppointment(slotTime)
                    }}
                    sx={{
                      height: rowHeight,
                      borderTop: `1px solid ${slot.index % 2 === 0 ? majorLineColor : minorLineColor}`,
                      cursor: (past || !canCreateAppointments) ? 'default' : 'pointer',
                      bgcolor: past ? '#9ca3af' : (slot.index % 2 === 0 ? '#f8fafc' : 'transparent'),
                    }}
                  />
                )
              })}
              {positionedAppointments.map(({ appointment, lane, laneCount }) => {
                const start = parseDate(appointment.start_at)
                const end = parseDate(appointment.end_at)
                const placement = clampAppointmentToGrid(start, end)
                if (!placement) return null
                const displayLane = lane
                const displayLaneCount = Math.min(laneCount, 3)
                const gap = 4
                const widthCalc = `calc((100% - ${(displayLaneCount + 1) * gap}px) / ${displayLaneCount})`
                const top = (placement.minutesFromGridStart / SLOT_DURATION_MINUTES) * rowHeight
                const height = (placement.durationMinutes / SLOT_DURATION_MINUTES) * rowHeight
                return (
                  <Box
                    key={`${keyPrefix}-appointment-${appointment.id}`}
                    onClick={(event) => {
                      event.stopPropagation()
                      setDetailsAppointmentId(appointment.id)
                    }}
                    sx={{
                      position: 'absolute',
                      left: `calc(${gap}px + (${displayLane} * (${widthCalc} + ${gap}px)))`,
                      width: widthCalc,
                      top,
                      height,
                      bgcolor: getStatusBackground(appointment.status),
                      color: '#fff',
                      borderRadius: 1,
                      p: compact ? 0.5 : 0.75,
                      fontSize: compact ? 10 : 11,
                      overflow: 'hidden',
                      cursor: 'pointer',
                      border: laneCount > 1 ? '1px solid rgba(255,255,255,0.7)' : '1px solid transparent',
                      boxShadow: `inset 0 0 0 1px ${getAppointmentRoleColor(appointment)}99`,
                      opacity: lane >= 3 ? 0.9 : 1,
                    }}
                  >
                    <Typography variant="caption" sx={{ color: '#fff', display: 'block', fontWeight: 700 }}>
                      {compact ? getClientLastName(appointment.client_id) : getClientLastFirst(appointment.client_id)}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#fff', display: 'block' }}>
                      {getCompactOfferLabel(appointment, compact ? 12 : (height < 70 ? 12 : 18))}
                    </Typography>
                    {compact && (
                      <Typography variant="caption" sx={{ color: '#fff', display: 'block' }}>
                        {start.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}
                      </Typography>
                    )}
                    {!compact && (
                      <Typography variant="caption" sx={{ color: '#fff', display: 'block' }}>
                        {formatTimeRange(start, end)}
                      </Typography>
                    )}
                    {laneCount > 3 && lane === 2 && (
                      <Typography variant="caption" sx={{ color: '#fff', display: 'block', fontWeight: 700 }}>
                        N+{laneCount - 3}
                      </Typography>
                    )}
                  </Box>
                )
              })}
            </Box>
          )
        })}
      </Box>
      </Box>
    )
  }

  const renderWeekView = () => (
    <Card>
      <CardContent>
        {renderWeekGrid(weekDays, weekAppointments, 'week', { stickyHeader: true, scrollMaxHeight: '78vh' })}
      </CardContent>
    </Card>
  )

  const renderRolling30View = () => (
    <Stack spacing={2}>
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} flexWrap="wrap" alignItems={{ xs: 'stretch', md: 'center' }}>
        <Chip size="small" label="Fryzjer" sx={{ bgcolor: '#0f766e', color: '#fff' }} />
        <Chip size="small" label="Manicure" sx={{ bgcolor: '#7c3aed', color: '#fff' }} />
        <ToggleButtonGroup
          exclusive
          size="small"
          value={rollingRoleFilter}
          onChange={(_, value) => { if (value) setRollingRoleFilter(value) }}
        >
          <ToggleButton value="all">Wszyscy</ToggleButton>
          <ToggleButton value="hairdresser">Fryzjerzy</ToggleButton>
          <ToggleButton value="manicure">Manicure</ToggleButton>
        </ToggleButtonGroup>
        <FormControl size="small" sx={{ minWidth: 220 }}>
          <InputLabel>Specjalista</InputLabel>
          <Select
            label="Specjalista"
            value={rollingStaffFilter}
            onChange={(e) => setRollingStaffFilter(e.target.value === '' ? '' : Number(e.target.value))}
          >
            <MenuItem value="">Wszyscy</MenuItem>
            {salonStaff
              .filter((row) => rollingRoleFilter === 'all'
                ? true
                : rollingRoleFilter === 'hairdresser'
                  ? isHairdresserRole(row.role_code)
                  : isManicureRole(row.role_code))
              .map((row) => (
                <MenuItem key={`rolling-staff-${row.id}`} value={row.id}>{row.displayName}</MenuItem>
              ))}
          </Select>
        </FormControl>
      </Stack>
      {rolling30Weeks.map((days, index) => (
        <Card key={`rolling-week-${index}`}>
          <CardContent>
            <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 700 }}>
              Tydzien {index + 1}: {days[0].toLocaleDateString('pl-PL')} - {days[days.length - 1].toLocaleDateString('pl-PL')}
            </Typography>
            {renderWeekGrid(days, rolling30AppointmentsFiltered, `rolling-${index}`, {
              rowHeight: ROLLING30_SLOT_ROW_HEIGHT,
              compact: true,
              hideEverySecondLabel: true,
              stickyHeader: true,
              scrollMaxHeight: '52vh',
            })}
          </CardContent>
        </Card>
      ))}
      {!rolling30AppointmentsFiltered.length && (
        <Alert severity="info">Brak wizyt w wybranym zakresie 30 dni.</Alert>
      )}
    </Stack>
  )

  const moveCalendar = (days: number) => {
    const next = new Date(selectedDay)
    next.setDate(selectedDay.getDate() + days)
    setCalendarDate(formatDateOnly(next))
  }

  const updateAppointmentLifecycle = async (appointmentId: number, action: 'cancel' | 'no-show' | 'reopen') => {
    try {
      await api.post(`/booking/appointments/${appointmentId}/${action}`)
      await reload()
      setFlash(
        action === 'cancel'
          ? `Wizyta #${appointmentId} została anulowana.`
          : action === 'no-show'
            ? `Wizyta #${appointmentId} oznaczona jako no-show.`
            : `Wizyta #${appointmentId} przywrócona do planowanych.`,
      )
      setDetailsAppointmentId(appointmentId)
    } catch (err: any) {
      setFlash(err?.response?.data?.detail || 'Nie udało się zmienić statusu wizyty.')
    }
  }

  const updatePendingAppointment = async (appointmentId: number, action: 'confirm' | 'reject') => {
    try {
      await api.post(`/booking/appointments/${appointmentId}/${action}`)
      await reload()
      setFlash(
        action === 'confirm'
          ? `Wizyta #${appointmentId} została potwierdzona.`
          : `Wizyta #${appointmentId} została odrzucona.`,
      )
      setDetailsAppointmentId(appointmentId)
    } catch (err: any) {
      setFlash(err?.response?.data?.detail || 'Nie udało się zmienić statusu rezerwacji.')
    }
  }

  return (
    <Stack spacing={2}>
      <Typography variant="h4">Kalendarz wizyt</Typography>
      {flash && <Alert severity="info">{flash}</Alert>}
      {smsSuggestedAppointmentId !== null && (
        <Alert
          severity="success"
          action={(
            <Stack direction="row" spacing={1}>
              <Button
                color="inherit"
                size="small"
                onClick={() => sendSmsConfirmation(smsSuggestedAppointmentId)}
                disabled={smsSending}
              >
                Wyslij SMS potwierdzenie
              </Button>
              <Button
                color="inherit"
                size="small"
                onClick={() => setSmsSuggestedAppointmentId(null)}
              >
                Pomin
              </Button>
            </Stack>
          )}
        >
          Wizyta zapisana. Mozesz od razu wyslac SMS potwierdzenia.
        </Alert>
      )}

      {showInlineForm && (
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Nowa wizyta</Typography>

          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2">1. Klient</Typography>
            </Grid>
            <Grid item xs={12} md={9}>
              <Stack spacing={1.5}>
                <RadioGroup row value={clientMode} onChange={(e) => setClientMode(e.target.value as 'existing' | 'new')}>
                  <FormControlLabel value="existing" control={<Radio />} label="Istniejacy" />
                  <FormControlLabel value="new" control={<Radio />} label="Nowy" />
                </RadioGroup>
                {clientMode === 'existing' ? (
                  <Autocomplete
                    options={clients}
                    value={clients.find((client) => client.id === clientId) || null}
                    onChange={(_, value) => setClientId(value?.id ?? 0)}
                    getOptionLabel={(option) => option.full_name}
                    renderInput={(params) => <TextField {...params} label="Szukaj po nazwie" fullWidth />}
                  />
                ) : (
                  <Grid container spacing={1.5}>
                    <Grid item xs={12} md={4}>
                      <TextField label="Imie i nazwisko" fullWidth value={newClientName} onChange={(e) => setNewClientName(e.target.value)} />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <TextField label="Telefon" fullWidth value={newClientPhone} onChange={(e) => setNewClientPhone(e.target.value)} />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <TextField label="Email (opcjonalnie)" fullWidth value={newClientEmail} onChange={(e) => setNewClientEmail(e.target.value)} />
                    </Grid>
                  </Grid>
                )}
              </Stack>
            </Grid>

            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2">2. Data i czas</Typography>
            </Grid>
            <Grid item xs={12} md={9}>
              <Grid container spacing={1.5}>
                <Grid item xs={12} md={6}>
                  <TextField label="Start" type="datetime-local" fullWidth value={startAt} onChange={(e) => { setStartAt(e.target.value); setAvailabilityStatus(null) }} />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField label="Koniec" type="datetime-local" fullWidth value={endAt} onChange={(e) => { setEndAt(e.target.value); setAvailabilityStatus(null) }} />
                </Grid>
              </Grid>
            </Grid>

            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2">3. Pracownik</Typography>
            </Grid>
            <Grid item xs={12} md={9}>
              <Stack spacing={1.5}>
                <TextField
                  select
                  label="Pracownik"
                  fullWidth
                  value={selectedStaffId}
                  onChange={(e) => { setSelectedStaffId(e.target.value === '' ? '' : Number(e.target.value)) }}
                >
                  {salonStaff.map((staff) => (
                    <MenuItem key={staff.id} value={staff.id}>
                      {staff.displayName}{staff.role_code ? ` (${staff.role_code})` : ''}
                    </MenuItem>
                  ))}
                </TextField>
                {loadingStaff && <CircularProgress size={20} />}
                {availabilityStatus && (
                  <Alert severity={availabilityStatus.busy ? 'warning' : 'success'} sx={{ flex: 1 }}>
                    {availabilityStatus.message}
                  </Alert>
                )}
              </Stack>
            </Grid>

            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2">4. Uslugi / Pakiet</Typography>
            </Grid>
            <Grid item xs={12} md={9}>
              <Stack spacing={1.5}>
                <Autocomplete
                  multiple
                  options={services}
                  value={services.filter((service) => selectedServices.includes(service.id))}
                  onChange={(_, value) => {
                    setSelectedServices(value.map((item) => item.id))
                    if (value.length > 0) setBundleId('')
                  }}
                  getOptionLabel={(option) => `${option.code} - ${option.name}`}
                  disabled={bundleId !== ''}
                  renderInput={(params) => <TextField {...params} label="Uslugi" fullWidth />}
                />
                <Autocomplete
                  options={bundlesInSalon}
                  value={selectedBundle}
                  onChange={(_, value) => {
                    setBundleId(value?.id ?? '')
                    if (value) setSelectedServices([])
                  }}
                  getOptionLabel={(option) => `${option.code} - ${option.name}`}
                  isOptionEqualToValue={(option, value) => option.id === value.id}
                  disabled={selectedServices.length > 0}
                  renderInput={(params) => <TextField {...params} label="Pakiet (opcjonalnie)" fullWidth />}
                />
                <Typography variant="body2" color="text.secondary">
                  Laczny czas: {totalDuration} min
                </Typography>
              </Stack>
            </Grid>

            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2">Snapshot ceny</Typography>
            </Grid>
            <Grid item xs={12} md={9}>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems={{ xs: 'stretch', md: 'center' }}>
                <Chip label={`Snapshot ceny: ${estimated.toFixed(2)} PLN`} color="secondary" />
                <Button variant="contained" onClick={createAppointment}>Dodaj wizyte</Button>
              </Stack>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
      )}

      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" alignItems={{ xs: 'stretch', md: 'center' }} spacing={1.5}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems={{ xs: 'stretch', md: 'center' }}>
          {user?.role !== 'receptionist' && (
            <TextField
              select
              size="small"
              label="Salon"
              value={selectedSalon}
              onChange={(e) => setSelectedSalon(Number(e.target.value))}
              sx={{ minWidth: 220 }}
            >
              {orderedAllowedSalons.map((salon) => <MenuItem key={salon.id} value={salon.id}>{salon.name}</MenuItem>)}
            </TextField>
          )}
          <ToggleButtonGroup
            exclusive
            value={calendarView}
            onChange={(_, value) => { if (value) setCalendarView(value) }}
            size="small"
          >
            <ToggleButton value="day">Dzien</ToggleButton>
            <ToggleButton value="week">Tydzien</ToggleButton>
            <ToggleButton value="rolling30">30 dni</ToggleButton>
          </ToggleButtonGroup>
          <Button
            size="small"
            variant="outlined"
            onClick={() => sendTodayBatchSms()}
            disabled={smsSending}
          >
            Batch SMS dla dzis
          </Button>
        </Stack>
        <Stack direction="row" spacing={1} alignItems="center">
          <Button
            size="small"
            variant="outlined"
            onClick={() => moveCalendar(calendarView === 'day' ? -1 : calendarView === 'week' ? -7 : -30)}
          >
            ←
          </Button>
          <TextField size="small" type="date" value={calendarDate} onChange={(e) => setCalendarDate(e.target.value)} />
          <Button size="small" variant="outlined" onClick={() => setCalendarDate(formatDateOnly(new Date()))}>
            Dzis
          </Button>
          <Button
            size="small"
            variant="outlined"
            onClick={() => moveCalendar(calendarView === 'day' ? 1 : calendarView === 'week' ? 7 : 30)}
          >
            →
          </Button>
        </Stack>
      </Stack>

      {calendarView === 'day' && renderDayView()}
      {calendarView === 'week' && renderWeekView()}
      {calendarView === 'rolling30' && renderRolling30View()}

      {calendarLoading && <Alert severity="info">Ladowanie wizyt...</Alert>}

      <Dialog open={appointmentDialogOpen} onClose={() => setAppointmentDialogOpen(false)} fullWidth maxWidth="md">
        <DialogTitle>Nowa wizyta</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <RadioGroup row value={clientMode} onChange={(e) => setClientMode(e.target.value as 'existing' | 'new')}>
              <FormControlLabel value="existing" control={<Radio />} label="Istniejacy" />
              <FormControlLabel value="new" control={<Radio />} label="Nowy" />
            </RadioGroup>
            {clientMode === 'existing' ? (
              <Autocomplete
                options={clients}
                value={clients.find((client) => client.id === clientId) || null}
                onChange={(_, value) => setClientId(value?.id ?? 0)}
                getOptionLabel={(option) => option.full_name}
                renderInput={(params) => <TextField {...params} label="Klient" fullWidth />}
              />
            ) : (
              <Stack spacing={1.5}>
                <TextField label="Imie i nazwisko" fullWidth value={newClientName} onChange={(e) => setNewClientName(e.target.value)} />
                <TextField label="Telefon" fullWidth value={newClientPhone} onChange={(e) => setNewClientPhone(e.target.value)} />
                <TextField label="Email (opcjonalnie)" fullWidth value={newClientEmail} onChange={(e) => setNewClientEmail(e.target.value)} />
              </Stack>
            )}
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
              <TextField label="Start" type="datetime-local" fullWidth value={startAt} onChange={(e) => setStartAt(e.target.value)} />
              <TextField label="Koniec" type="datetime-local" fullWidth value={endAt} onChange={(e) => setEndAt(e.target.value)} />
            </Stack>
            <TextField
              select
              label="Pracownik"
              fullWidth
              value={selectedStaffId}
              onChange={(e) => setSelectedStaffId(e.target.value === '' ? '' : Number(e.target.value))}
            >
              {salonStaff.map((staff) => (
                <MenuItem key={staff.id} value={staff.id}>
                  {staff.displayName}
                </MenuItem>
              ))}
            </TextField>
            {availabilityStatus && (
              <Alert severity={availabilityStatus.busy ? 'warning' : 'success'}>
                {availabilityStatus.message}
              </Alert>
            )}
            {canUseOverlap && (
              <FormControlLabel
                control={<Checkbox checked={allowOverlap} onChange={(e) => setAllowOverlap(e.target.checked)} />}
                label="Wizyta na zakladke (dopusc nakladanie czasu)"
              />
            )}
            <Autocomplete
              multiple
              options={services}
              value={services.filter((service) => selectedServices.includes(service.id))}
              onChange={(_, value) => {
                setSelectedServices(value.map((item) => item.id))
                if (value.length > 0) setBundleId('')
              }}
              getOptionLabel={(option) => `${option.code} - ${option.name}`}
              disabled={bundleId !== ''}
              renderInput={(params) => <TextField {...params} label="Uslugi" fullWidth />}
            />
            <Autocomplete
              options={bundlesInSalon}
              value={selectedBundle}
              onChange={(_, value) => {
                setBundleId(value?.id ?? '')
                if (value) setSelectedServices([])
              }}
              getOptionLabel={(option) => `${option.code} - ${option.name}`}
              isOptionEqualToValue={(option, value) => option.id === value.id}
              disabled={selectedServices.length > 0}
              renderInput={(params) => <TextField {...params} label="Pakiet (opcjonalnie)" fullWidth />}
            />
            <Chip label={`Snapshot ceny: ${estimated.toFixed(2)} PLN`} color="secondary" />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAppointmentDialogOpen(false)}>Anuluj</Button>
          <Button
            variant="contained"
            onClick={async () => {
              const ok = await createAppointment()
              if (ok) setAppointmentDialogOpen(false)
            }}
          >
            Dodaj wizyte
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={executionAppointmentId !== ''}
        onClose={() => {
          setExecutionAppointmentId('')
          setExecutionError('')
        }}
        fullWidth
        maxWidth="lg"
      >
        <DialogTitle>Zapisz wykonanie wizyty {executionAppointmentId !== '' ? `#${executionAppointmentId}` : ''}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {executionAppointmentId !== '' && (() => {
              const appointment = executionAppointment
              if (!appointment) return null
              const bundle = appointment.bundle_id ? bundles.find((item) => item.id === appointment.bundle_id) : null
              return (
                <Card variant="outlined">
                  <CardContent>
                    <Stack spacing={0.75}>
                      <Typography variant="subtitle2">Podsumowanie wizyty</Typography>
                      <Typography variant="body2">Klient: {getClientName(appointment.client_id)}</Typography>
                      <Typography variant="body2">Termin: {appointment.start_at.replace('T', ' ')} - {appointment.end_at.replace('T', ' ')}</Typography>
                      {bundle && <Typography variant="body2">Pakiet: {bundle.code} - {bundle.name}</Typography>}
                      {!!appointment.services.length && (
                        <Typography variant="body2">Uslugi z wizyty: {getServiceLabel(appointment.services)}</Typography>
                      )}
                      {bundle && (
                        <Button
                          size="small"
                          sx={{ alignSelf: 'flex-start', mt: 0.5 }}
                          variant="outlined"
                          onClick={() => replaceExecutionLinesWithBundle(bundle.id)}
                        >
                          Wstaw linie z forfetu
                        </Button>
                      )}
                    </Stack>
                  </CardContent>
                </Card>
              )
            })()}
            <Alert severity="info">
              Uzupelnij tylko rzeczywiste wykonanie. Pozycje wymagane musza miec produkt i ilosc. Pozycje szacunkowe sa opcjonalne.
            </Alert>
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <TextField
                  label="Data wykonania"
                  type="datetime-local"
                  fullWidth
                  value={executionPerformedAt}
                  onChange={(e) => setExecutionPerformedAt(e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={8}>
                <Stack direction="row" spacing={1} justifyContent="flex-end">
                  <Button variant="text" onClick={fillExecutionQuantitiesFromPlan}>
                    Uzupelnij ilosci wg norm
                  </Button>
                  <Button variant="outlined" onClick={addExecutionLine}>Dodaj linie zabiegu</Button>
                </Stack>
              </Grid>
            </Grid>

            <Stack spacing={2}>
              {executionError && <Alert severity="error">{executionError}</Alert>}
              {executionLines.map((line, index) => {
                const recipeItems = typeof line.service_id === 'number' ? (executionRecipesByService[line.service_id] || []) : []
                const trackedRecipeItems = recipeItems.filter((item) => !isRecipeStocktakeOnly(item))
                const strictRecipeItems = trackedRecipeItems.filter(isRecipeRequiredPerService)
                const estimateRecipeItems = trackedRecipeItems.filter((item) => !isRecipeRequiredPerService(item))
                const selectionValue = typeof line.service_id === 'number' ? `service:${line.service_id}` : ''
                return (
                  <Card variant="outlined" key={`exec-line-${index}`}>
                    <CardContent>
                      <Grid container spacing={2} alignItems="flex-start">
                        <Grid item xs={12} md={4}>
                          <TextField
                            select
                            fullWidth
                            label="Usluga / Forfet"
                            value={selectionValue}
                            onChange={(e) => applyExecutionSelection(index, e.target.value)}
                            SelectProps={{ displayEmpty: true }}
                          >
                            <MenuItem value="">Wybierz pozycje...</MenuItem>
                            {services.map((service) => <MenuItem key={`service-${service.id}`} value={`service:${service.id}`}>{service.code} - {service.name}</MenuItem>)}
                            {bundlesInSalon.map((bundle) => <MenuItem key={`bundle-${bundle.id}`} value={`bundle:${bundle.id}`}>{bundle.code} - {bundle.name}</MenuItem>)}
                          </TextField>
                        </Grid>
                        <Grid item xs={12} md={4}>
                          <TextField
                            select
                            fullWidth
                            label="Pracownik"
                            value={line.worker_id}
                            onChange={(e) => {
                              const rawValue = e.target.value
                              if (rawValue === '') {
                                setExecutionLine(index, { worker_id: '', worker_role_id: '' })
                                return
                              }
                              const workerId = Number(rawValue)
                              const worker = resources.find((item) => item.id === workerId)
                              const roleId = worker?.role_ids.find((id) => bookableRoleIds.includes(id)) ?? worker?.role_ids[0]
                              setExecutionLine(index, { worker_id: workerId, worker_role_id: roleId ?? '' })
                            }}
                            SelectProps={{ displayEmpty: true }}
                            helperText="Wybieraj po kodzie pracownika."
                          >
                            <MenuItem value="">Wybierz pracownika...</MenuItem>
                            {executionWorkerOptions.map((resource) => (
                              <MenuItem key={resource.id} value={resource.id}>{resource.id} - {getResourceName(resource.id)}</MenuItem>
                            ))}
                          </TextField>
                        </Grid>
                        <Grid item xs={12} md={3}>
                          <TextField
                            type="number"
                            fullWidth
                            label="Cena snapshot"
                            value={line.price_snapshot}
                            onChange={(e) => setExecutionLine(index, { price_snapshot: Number(e.target.value) })}
                          />
                        </Grid>
                        <Grid item xs={12} md={1}>
                          <Button
                            color="error"
                            variant="outlined"
                            onClick={() => removeExecutionLine(index)}
                            disabled={executionLines.length === 1}
                          >
                            Usun
                          </Button>
                        </Grid>
                        {trackedRecipeItems.length > 0 && (
                          <Grid item xs={12}>
                            <Stack spacing={1.5}>
                              <Typography variant="subtitle2">Plan i zuzycie z receptury</Typography>
                              {strictRecipeItems.length > 0 && (
                                <Alert severity="info">
                                  Pozycje wymagane musza byc rozliczone. Pozycje szacunkowe mozna uzupelnic opcjonalnie.
                                </Alert>
                              )}
                              {strictRecipeItems.length > 0 && (
                                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                  Pozycje wymagane
                                </Typography>
                              )}
                              {trackedRecipeItems.map((recipeItem) => {
                                const recipeIndex = line.resources.findIndex((resource) => resource.recipe_item_id === recipeItem.id)
                                const resourceDraft = line.resources[recipeIndex]
                                const productValue =
                                  typeof resourceDraft?.product_id === 'number'
                                    ? executionProducts.find((item) => item.id === resourceDraft.product_id) || null
                                    : null
                                const familyKey = (recipeItem.product_family || '').trim().toUpperCase() || '__ALL__'
                                const filteredFamilyProducts = executionProductsByFamily[familyKey] || []
                                const familyProducts = filteredFamilyProducts.length
                                  ? filteredFamilyProducts
                                  : executionProductsByFamily.__ALL__ || executionProducts
                                const exactProductIds = typeof recipeItem.product_id === 'number' ? [recipeItem.product_id] : []
                                const productOptions = exactProductIds.length > 0
                                  ? familyProducts.filter((item) => exactProductIds.includes(item.id)).concat(
                                    executionProducts.filter((item) => exactProductIds.includes(item.id) && !familyProducts.some((familyItem) => familyItem.id === item.id)),
                                  )
                                  : familyProducts
                                const familyLabel = recipeItem.product_family || 'wlasciwej rodziny'
                                const plannedQuantity = getRecipePlannedQuantity(recipeItem)
                                const unitLabel = getRecipeUnitLabel(recipeItem)
                                const variance = Number(resourceDraft?.quantity_used ?? 0) - plannedQuantity
                                const helperParts = [
                                  recipeItem.quantity_mode ? `Tryb: ${recipeItem.quantity_mode}` : null,
                                  recipeItem.total_label || `${plannedQuantity} ${unitLabel}`,
                                  recipeItem.note || null,
                                ].filter(Boolean)
                                return (
                                  <Grid
                                    container
                                    spacing={2}
                                    key={`exec-line-${index}-recipe-${recipeItem.id}`}
                                    sx={{
                                      border: '1px solid',
                                      borderColor: recipeItem.is_required === false ? 'divider' : 'primary.light',
                                      borderRadius: 1,
                                      p: 0.5,
                                      m: 0,
                                      backgroundColor: recipeItem.is_required === false ? 'transparent' : 'rgba(25,118,210,0.04)',
                                    }}
                                  >
                                    {recipeItem.is_required === false && estimateRecipeItems[0]?.id === recipeItem.id && (
                                      <Grid item xs={12}>
                                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                          Pozycje szacunkowe
                                        </Typography>
                                      </Grid>
                                    )}
                                    <Grid item xs={12} md={4}>
                                      <TextField
                                        fullWidth
                                        label="Pozycja receptury"
                                        value={
                                          recipeItem.product_label_snapshot
                                          || recipeItem.product_name
                                          || recipeItem.product_family
                                          || recipeItem.note
                                          || `Pozycja #${recipeItem.id}`
                                        }
                                        InputProps={{ readOnly: true }}
                                        helperText={helperParts.join(' • ')}
                                      />
                                    </Grid>
                                    <Grid item xs={12} md={5}>
                                      <Autocomplete
                                        options={productOptions}
                                        value={productValue}
                                        onChange={(_, value) => {
                                          setExecutionResource(index, recipeIndex, { product_id: value?.id ?? '' })
                                        }}
                                        getOptionLabel={(option) => `${option.code} - ${option.name}`}
                                        isOptionEqualToValue={(option, value) => option.id === value.id}
                                        renderInput={(params) => (
                                          <TextField
                                            {...params}
                                            required={isRecipeRequiredPerService(recipeItem)}
                                            label="Produkt"
                                            helperText={
                                              exactProductIds.length > 0
                                                ? `Domyslny produkt z receptury. Mozesz zostawic lub zmienic w obrebie ${familyLabel}.`
                                                : isRecipeRequiredPerService(recipeItem)
                                                  ? `Wybierz konkretny produkt z ${familyLabel}: wymagany zasob na wykonaniu`
                                                  : `Wybierz konkretny produkt z ${familyLabel}: zasob opcjonalny`
                                            }
                                          />
                                        )}
                                      />
                                    </Grid>
                                    <Grid item xs={12} md={2}>
                                      <TextField
                                        type="number"
                                        fullWidth
                                        required={isRecipeRequiredPerService(recipeItem)}
                                        label="Ilosc zuzyta"
                                        value={resourceDraft?.quantity_used ?? ''}
                                        onChange={(e) => {
                                          setExecutionResource(index, recipeIndex, { quantity_used: Number(e.target.value) })
                                        }}
                                        helperText={
                                          Number.isFinite(variance)
                                            ? `Plan: ${plannedQuantity} ${unitLabel}`
                                            : `Plan: ${plannedQuantity} ${unitLabel}`
                                        }
                                      />
                                    </Grid>
                                    <Grid item xs={12} md={1}>
                                      <TextField
                                        fullWidth
                                        label="Odch."
                                        value={
                                          Number.isFinite(variance)
                                            ? `${variance > 0 ? '+' : ''}${variance.toFixed(2)}`
                                            : '-'
                                        }
                                        InputProps={{ readOnly: true }}
                                      />
                                    </Grid>
                                  </Grid>
                                )
                              })}
                            </Stack>
                          </Grid>
                        )}
                      </Grid>
                    </CardContent>
                  </Card>
                )
              })}
            </Stack>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setExecutionAppointmentId('')
            setExecutionError('')
          }}
          >
            Anuluj
          </Button>
          <Button variant="contained" onClick={saveExecution}>Zapisz wykonanie</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={settlementOpen} onClose={() => setSettlementOpen(false)} fullWidth maxWidth="md">
        <DialogTitle>Rozliczenie wizyty</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {settlementError && <Alert severity="error">{settlementError}</Alert>}
            {settlementLoading && <Alert severity="info">Ladowanie danych rozliczenia...</Alert>}
            {invoicePreview && (
              <>
                <Card variant="outlined">
                  <CardContent>
                    <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems={{ xs: 'flex-start', md: 'center' }}>
                      <Chip label={`Do zaplaty: ${settlementTotal.toFixed(2)} PLN`} color="secondary" />
                      <Chip
                        label={`Suma platnosci: ${settlementAllocationTotal.toFixed(2)} PLN`}
                        color={canSubmitSettlement ? 'success' : 'warning'}
                      />
                      {!canSubmitSettlement && (
                        <Typography variant="body2" color="warning.main">
                          Kwota platnosci musi zgadzac sie z kwota do zaplaty.
                        </Typography>
                      )}
                    </Stack>
                  </CardContent>
                </Card>
                <Alert severity="info">
                  Platnosc realizujesz w modalu rozliczenia. Integracja z terminalem i kasa fiskalna: do podpiecia API dostawcy.
                </Alert>
                <Card variant="outlined">
                  <CardContent>
                    <Stack spacing={1}>
                      <Typography variant="subtitle1">Snapshot uslug</Typography>
                      {invoicePreview.items.filter((row) => row.kind === 'service').map((row, index) => (
                        <Stack key={`${row.label}-${index}`} direction="row" justifyContent="space-between">
                          <Typography>{row.label}</Typography>
                          <Typography>{row.total_gross.toFixed(2)} PLN</Typography>
                        </Stack>
                      ))}
                      <Typography color="text.secondary">Rabat karta: -{invoicePreview.card_discount.toFixed(2)} PLN</Typography>
                      <Typography color="text.secondary">Zaproszenia: -{invoicePreview.invitation_discount.toFixed(2)} PLN</Typography>
                    </Stack>
                  </CardContent>
                </Card>
                <Card variant="outlined">
                  <CardContent>
                    <Stack spacing={1.5}>
                      <Typography variant="subtitle1">Rabaty i benefity</Typography>
                      <FormControlLabel
                        control={<Checkbox checked={settlementUseCard} onChange={(e) => setSettlementUseCard(e.target.checked)} />}
                        label={invoicePreview.eligible_card ? `Karta stalego klienta (${invoicePreview.eligible_card.discount_pct}%)` : 'Brak aktywnej karty stalego klienta'}
                      />
                      <TextField
                        select
                        label="Promocja (opcjonalnie)"
                        fullWidth
                        value={settlementPromotionId}
                        onChange={(e) => setSettlementPromotionId(e.target.value === '' ? '' : Number(e.target.value))}
                        helperText={
                          settlementPromotions.length
                            ? 'Aktywne promocje pasujace do tej wizyty'
                            : 'Brak aktywnych promocji dla tej wizyty'
                        }
                      >
                        <MenuItem value="">Brak</MenuItem>
                        {settlementPromotions.map((promotion) => (
                          <MenuItem key={promotion.id} value={promotion.id}>
                            {promotion.name} ({promotion.promotion_type}, {promotion.value.toFixed(2)})
                          </MenuItem>
                        ))}
                      </TextField>
                      <Autocomplete
                        multiple
                        options={invoicePreview.available_invitations}
                        value={invoicePreview.available_invitations.filter((item) => settlementInvitationIds.includes(item.id))}
                        onChange={(_, value) => setSettlementInvitationIds(value.map((item) => item.id))}
                        getOptionLabel={(option) => {
                          const serviceName = services.find((service) => service.id === option.service_id)?.name || `Usluga ${option.service_id}`
                          return `${serviceName}${option.expiry ? ` (do ${option.expiry})` : ''}`
                        }}
                        renderInput={(params) => <TextField {...params} label="Zaproszenia darmowe" fullWidth />}
                      />
                    </Stack>
                  </CardContent>
                </Card>
                <Card variant="outlined">
                  <CardContent>
                    <Stack spacing={1.5}>
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Typography variant="subtitle1">Sprzedaz detaliczna</Typography>
                        <Button size="small" onClick={addRetailRow}>Dodaj produkt</Button>
                      </Stack>
                      {settlementRetailRows.map((row, index) => (
                        <Grid container spacing={1.5} key={`retail-${index}`}>
                          <Grid item xs={12} md={7}>
                            <Autocomplete
                              options={settlementProducts}
                              value={settlementProducts.find((item) => item.id === row.product_id) || null}
                              onChange={(_, value) => updateRetailRow(index, { product_id: value?.id ?? '' })}
                              getOptionLabel={(option) => `${option.code} - ${option.name}`}
                              renderInput={(params) => <TextField {...params} label="Produkt" fullWidth />}
                            />
                          </Grid>
                          <Grid item xs={12} md={3}>
                            <TextField
                              type="number"
                              fullWidth
                              label="Ilosc"
                              value={row.quantity}
                              onChange={(e) => updateRetailRow(index, { quantity: Math.max(1, Number(e.target.value) || 1) })}
                            />
                          </Grid>
                          <Grid item xs={12} md={2}>
                            <Button color="error" variant="outlined" onClick={() => removeRetailRow(index)}>Usun</Button>
                          </Grid>
                        </Grid>
                      ))}
                      {!settlementRetailRows.length && <Typography color="text.secondary">Brak detalu do doliczenia.</Typography>}
                    </Stack>
                  </CardContent>
                </Card>
                <Card variant="outlined">
                  <CardContent>
                    <Stack spacing={1.5}>
                      <Stack direction="row" justifyContent="space-between" alignItems="center">
                        <Typography variant="subtitle1">Alokacje platnosci</Typography>
                        <Stack direction="row" spacing={1}>
                          <Button size="small" onClick={fillLastSettlementAllocation}>Dopelnij ostatnia</Button>
                          <Button size="small" onClick={addSettlementAllocation}>Dodaj podzial</Button>
                        </Stack>
                      </Stack>
                      {settlementAllocations.map((row, index) => (
                        <Grid container spacing={1.5} key={`allocation-${index}`} alignItems="center">
                          <Grid item xs={12} md={3}>
                            <TextField
                              select
                              fullWidth
                              label="Metoda"
                              value={row.method}
                              onChange={(e) =>
                                updateSettlementAllocation(index, {
                                  method: e.target.value as 'cash' | 'card' | 'voucher' | 'transfer',
                                  voucher_reference:
                                    e.target.value === 'voucher' ? row.voucher_reference : '',
                                })
                              }
                            >
                              <MenuItem value="cash">Gotowka</MenuItem>
                              <MenuItem value="card">Karta</MenuItem>
                              <MenuItem value="voucher">Voucher</MenuItem>
                              <MenuItem value="transfer">Przelew</MenuItem>
                            </TextField>
                          </Grid>
                          <Grid item xs={12} md={3}>
                            <TextField
                              type="number"
                              fullWidth
                              label="Kwota"
                              value={row.amount}
                              onChange={(e) => updateSettlementAllocation(index, { amount: Math.max(0, Number(e.target.value) || 0) })}
                            />
                          </Grid>
                          <Grid item xs={12} md={4}>
                            {row.method === 'voucher' ? (
                              <TextField
                                fullWidth
                                label="Numer / opis vouchera"
                                value={row.voucher_reference}
                                onChange={(e) => updateSettlementAllocation(index, { voucher_reference: e.target.value })}
                              />
                            ) : (
                              <TextField fullWidth label="Uwagi" value="-" disabled />
                            )}
                          </Grid>
                          <Grid item xs={12} md={2}>
                            <Button
                              color="error"
                              variant="outlined"
                              onClick={() => removeSettlementAllocation(index)}
                              disabled={settlementAllocations.length <= 1}
                            >
                              Usun
                            </Button>
                          </Grid>
                        </Grid>
                      ))}
                      <Typography variant="body2" color="text.secondary">
                        Podziel platnosc na metody. Ostatnia pozycja moze zostac automatycznie dopelniona.
                      </Typography>
                    </Stack>
                  </CardContent>
                </Card>
              </>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettlementOpen(false)}>Anuluj</Button>
          <Button variant="contained" onClick={submitSettlement} disabled={!canSubmitSettlement}>
            Zapisz platnosc
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={detailsAppointmentId !== null} onClose={() => setDetailsAppointmentId(null)} fullWidth maxWidth="sm">
        <DialogTitle>Szczegoly wizyty</DialogTitle>
        <DialogContent>
          {detailAppointment && (
            <Stack spacing={1.25} sx={{ mt: 1 }}>
              <Typography><strong>Klient:</strong> {getClientName(detailAppointment.client_id)}</Typography>
              <Typography><strong>Termin:</strong> {detailAppointment.start_at.replace('T', ' ')} - {detailAppointment.end_at.replace('T', ' ')}</Typography>
              <Typography><strong>Pracownik:</strong> {getStaffLabel(detailAppointment.resources) || '-'}</Typography>
              <Typography><strong>Uslugi:</strong> {getServiceLabel(detailAppointment.services) || '-'}</Typography>
              <Typography><strong>Status:</strong> {STATUS_LABEL[detailAppointment.status] || detailAppointment.status}</Typography>
              <Typography><strong>Snapshot:</strong> {detailAppointment.total_price_snapshot.toFixed(2)} PLN</Typography>
              {!!detailResources.length && (
                <Stack spacing={0.5} sx={{ pt: 1 }}>
                  <Typography><strong>Zuzyte zasoby:</strong></Typography>
                  {detailResources.map((resource, index) => (
                    <Typography key={`${resource.performed_line_id}-${resource.product_id}-${index}`} variant="body2" color="text.secondary">
                      {resource.service_name || `Usluga #${resource.service_id}`}: {resource.product_name || `Produkt #${resource.product_id}`}
                      {resource.product_family ? ` [${resource.product_family}]` : ''} ({resource.quantity_used}
                      {resource.quantity_unit ? ` ${resource.quantity_unit}` : ''})
                      {resource.total_cost_snapshot != null ? `, koszt ${resource.total_cost_snapshot.toFixed(2)} PLN` : ''}
                      {' - '}
                      {resource.worker_name || `#${resource.worker_id}`} / {resource.worker_role_name || 'rola'}
                    </Typography>
                  ))}
                </Stack>
              )}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          {detailAppointment && detailAppointment.status === 'pending' && canCreateAppointments && (
            <>
              <Button color="success" variant="contained" onClick={() => updatePendingAppointment(detailAppointment.id, 'confirm')}>
                Potwierdz
              </Button>
              <Button color="error" onClick={() => updatePendingAppointment(detailAppointment.id, 'reject')}>
                Odrzuc
              </Button>
            </>
          )}
          {detailAppointment && detailAppointment.status !== 'done' && detailAppointment.status !== 'cancelled' && detailAppointment.status !== 'no_show' && detailAppointment.status !== 'pending' && (
            <Button onClick={() => startExecution(detailAppointment.id)}>Zapisz wykonanie</Button>
          )}
          {detailAppointment && detailAppointment.status !== 'done' && detailAppointment.status !== 'cancelled' && detailAppointment.status !== 'no_show' && detailAppointment.status !== 'pending' && (
            <>
              <Button color="warning" onClick={() => updateAppointmentLifecycle(detailAppointment.id, 'no-show')}>Klient nie przyszedl</Button>
              <Button color="error" onClick={() => updateAppointmentLifecycle(detailAppointment.id, 'cancel')}>Anuluj</Button>
            </>
          )}
          {detailAppointment && (detailAppointment.status === 'cancelled' || detailAppointment.status === 'no_show') && (
            <Button onClick={() => updateAppointmentLifecycle(detailAppointment.id, 'reopen')}>Przywróć</Button>
          )}
          {detailAppointment && detailAppointment.status === 'done' && (
            <>
              <Button onClick={() => openSettlement(detailAppointment.id)}>Rozlicz</Button>
              <Button onClick={() => generateIssues(detailAppointment.id)}>Rozchod materialow</Button>
            </>
          )}
          <Button onClick={() => setDetailsAppointmentId(null)}>Zamknij</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}

export default SchedulesPage
