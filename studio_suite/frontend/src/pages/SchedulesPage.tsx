import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Card,
  CardContent,
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
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material'
import { Fragment, useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useBooking } from '../contexts/BookingContext'
import { api } from '../services/api'
import type { Appointment } from '../types'

const parseDate = (value: string) => new Date(value)
const overlaps = (startA: Date, endA: Date, startB: Date, endB: Date) => startA < endB && startB < endA
const SLOT_START_HOUR = 8
const SLOT_END_HOUR = 20
const HALF_HOUR_ROW_HEIGHT = 44
const HOUR_ROW_HEIGHT = 64

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

type ExecutionLineDraft = {
  service_id: number | ''
  worker_id: number | ''
  worker_role_id: number | ''
  price_snapshot: number
  color_product_id?: number
}

type SalonStaffOption = {
  id: number
  full_name: string
  role_code?: string | null
  can_be_booked: boolean
}

type CalendarView = 'list' | 'day' | 'week'

type PositionedAppointment = {
  appointment: Appointment
  lane: number
  laneCount: number
}

const STATUS_COLOR: Record<string, 'default' | 'primary' | 'success' | 'error'> = {
  planned: 'default',
  started: 'primary',
  in_progress: 'primary',
  done: 'success',
  completed: 'success',
  cancelled: 'error',
}

const getStatusBackground = (status: string | undefined) => {
  const normalized = (status || '').toLowerCase()
  if (STATUS_COLOR[normalized] === 'success') return '#2e7d32'
  if (STATUS_COLOR[normalized] === 'primary') return '#1565c0'
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

const SchedulesPage = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const {
    appointments,
    salons,
    clients,
    resources,
    services,
    bundles,
    staffRoles,
    priceListItems,
    colorProducts,
    performedServiceLines,
    addAppointment,
    addClient,
    completeAppointment,
    estimateTotal,
    getAppointmentRevenue,
  } = useBooking()

  const defaultSalon = user?.assigned_salon_ids?.[0] ?? salons[0]?.id ?? 1
  const [selectedSalon, setSelectedSalon] = useState(defaultSalon)
  const [clientMode, setClientMode] = useState<'existing' | 'new'>('existing')
  const [clientId, setClientId] = useState<number>(clients[0]?.id ?? 1)
  const [newClientName, setNewClientName] = useState('')
  const [newClientPhone, setNewClientPhone] = useState('')
  const [newClientEmail, setNewClientEmail] = useState('')
  const [startAt, setStartAt] = useState('2026-02-26T15:00')
  const [endAt, setEndAt] = useState('2026-02-26T16:00')
  const [salonStaff, setSalonStaff] = useState<SalonStaffOption[]>([])
  const [loadingStaff, setLoadingStaff] = useState(false)
  const [selectedStaffId, setSelectedStaffId] = useState<number | ''>('')
  const [selectedServices, setSelectedServices] = useState<number[]>([])
  const [bundleId, setBundleId] = useState<number | ''>('')
  const [flash, setFlash] = useState('')
  const [availabilityStatus, setAvailabilityStatus] = useState<{ busy: boolean; message: string } | null>(null)
  const [calendarView, setCalendarView] = useState<CalendarView>(() => {
    if (typeof window === 'undefined') return 'day'
    const saved = window.localStorage.getItem('calendar_view') as CalendarView | null
    return saved === 'list' || saved === 'day' || saved === 'week' ? saved : 'day'
  })
  const [calendarDate, setCalendarDate] = useState(formatDateOnly(new Date()))
  const [detailsAppointmentId, setDetailsAppointmentId] = useState<number | null>(null)
  const [appointmentDialogOpen, setAppointmentDialogOpen] = useState(false)
  const [calendarAppointments, setCalendarAppointments] = useState<Appointment[]>([])
  const [calendarLoading, setCalendarLoading] = useState(false)
  const [expandedWeekCell, setExpandedWeekCell] = useState<string | null>(null)

  const [executionAppointmentId, setExecutionAppointmentId] = useState<number | ''>('')
  const [executionPerformedAt, setExecutionPerformedAt] = useState('2026-02-26T16:00')
  const [executionLines, setExecutionLines] = useState<ExecutionLineDraft[]>([])

  const highlightedAppointmentId = useMemo(() => {
    const raw = new URLSearchParams(location.search).get('appointment_id')
    if (!raw) return null
    const parsed = Number(raw)
    return Number.isFinite(parsed) ? parsed : null
  }, [location.search])

  const allowedSalons = useMemo(() => {
    if (!user?.assigned_salon_ids?.length) return salons
    return salons.filter((s) => user.assigned_salon_ids?.includes(s.id))
  }, [salons, user])
  const appointmentsInSalon = useMemo(
    () => appointments.filter((a) => a.salon_id === selectedSalon),
    [appointments, selectedSalon],
  )

  useEffect(() => {
    if (allowedSalons.length > 0 && !allowedSalons.some((salon) => salon.id === selectedSalon)) {
      setSelectedSalon(allowedSalons[0].id)
    }
  }, [allowedSalons, selectedSalon])

  useEffect(() => {
    if (clients.length > 0 && !clients.some((client) => client.id === clientId)) {
      setClientId(clients[0].id)
    }
  }, [clientId, clients])

  const bookableRoleIds = staffRoles
    .filter((role) => role.code === 'FRYZJER' || role.code === 'MANICURZYSTKA')
    .map((role) => role.id)

  const resourcesInSalon = resources.filter(
    (resource) =>
      resource.salon_id === selectedSalon && resource.role_ids.some((roleId) => bookableRoleIds.includes(roleId)),
  )

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
      const res = await api.get<Array<{ id: number; display_name?: string; first_name?: string | null; last_name?: string | null; can_be_booked: boolean; role_code?: string | null }>>(
        `/booking/salons/${salonId}/staff`,
        { params: { can_take_bookings: true } },
      )
      const rows = (res.data || [])
        .filter((row) => !['RECEPTIONIST', 'MANAGER'].includes((row.role_code || '').toUpperCase()))
        .map((row) => ({
          id: row.id,
          full_name: composeStaffLabel(row.first_name, row.last_name, row.display_name) || `#${row.id}`,
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
    if (calendarView === 'list') {
      setCalendarAppointments([])
      return
    }
    const fetchCalendarAppointments = async () => {
      setCalendarLoading(true)
      try {
        if (calendarView === 'day') {
          const res = await api.get<Appointment[]>('/booking/appointments', {
            params: {
              salon_id: selectedSalon,
              date: calendarDate,
              sort: 'start_asc',
            },
          })
          setCalendarAppointments(res.data || [])
        } else {
          const baseDay = parseDate(`${calendarDate}T00:00`)
          const start = new Date(baseDay)
          start.setDate(baseDay.getDate() - (baseDay.getDay() === 0 ? 6 : baseDay.getDay() - 1))
          start.setHours(0, 0, 0, 0)
          const end = new Date(start)
          end.setDate(start.getDate() + 6)
          end.setHours(23, 59, 59, 999)
          const res = await api.get<Appointment[]>('/booking/appointments', {
            params: {
              salon_id: selectedSalon,
              date_from: start.toISOString(),
              date_to: end.toISOString(),
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
  }, [calendarView, calendarDate, selectedSalon])

  const generateIssues = async (appointmentId: number) => {
    try {
      await api.post(`/appointments/${appointmentId}/generate-issues`)
      setFlash(`Wygenerowano rozchod dla wizyty #${appointmentId}.`)
      navigate(`/inventory/issues?appointment_id=${appointmentId}`)
    } catch (err: any) {
      setFlash(err?.response?.data?.detail || 'Nie udalo sie wygenerowac rozchodu.')
    }
  }

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
      await addAppointment({
        salon_id: selectedSalon,
        client_id: targetClientId,
        start_at: startAt,
        end_at: endAt,
        resources: [Number(selectedStaffId)],
        services: selectedServices,
        bundle_id: bundleId === '' ? undefined : bundleId,
      })
      setFlash('Wizyta dodana.')
      return true
    } catch {
      setFlash('Nie udalo sie dodac wizyty.')
      return false
    }
  }

  const startExecution = (appointmentId: number) => {
    const appointment = appointmentsInSalon.find((item) => item.id === appointmentId)
    if (!appointment) return

    const firstWorker = appointment.resources[0] ?? ''
    const firstService = appointment.services[0] ?? ''
    const worker = resources.find((item) => item.id === firstWorker)
    const firstRole = worker?.role_ids.find((id) => bookableRoleIds.includes(id)) ?? ''
    const firstPrice =
      typeof firstService === 'number'
        ? priceListItems.find((item) => item.salon_id === appointment.salon_id && item.service_id === firstService)?.price ?? 0
        : 0

    setExecutionAppointmentId(appointmentId)
    setExecutionPerformedAt(appointment.end_at.slice(0, 16))
    setExecutionLines([
      {
        service_id: firstService,
        worker_id: firstWorker,
        worker_role_id: firstRole,
        price_snapshot: firstPrice,
      },
    ])
  }

  const addExecutionLine = () => {
    setExecutionLines((prev) => [...prev, { service_id: '', worker_id: '', worker_role_id: '', price_snapshot: 0 }])
  }

  const setExecutionLine = (index: number, patch: Partial<ExecutionLineDraft>) => {
    setExecutionLines((prev) => prev.map((line, i) => (i === index ? { ...line, ...patch } : line)))
  }

  const removeExecutionLine = (index: number) => {
    setExecutionLines((prev) => prev.filter((_, i) => i !== index))
  }

  const saveExecution = async () => {
    if (executionAppointmentId === '') return
    if (executionLines.length === 0) {
      setFlash('Dodaj przynajmniej jedna linie zabiegu.')
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
      setFlash('Uzupelnij komplet danych wykonania: usluga, pracownik, rola, cena.')
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
          color_product_id: line.color_product_id,
        })),
      })
      setExecutionAppointmentId('')
      setExecutionLines([])
      setFlash('Wizyta oznaczona jako wykonana.')
    } catch {
      setFlash('Nie udalo sie zapisac wykonania wizyty.')
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
      overlaps(wantedStart, wantedEnd, parseDate(appointment.start_at), parseDate(appointment.end_at)),
    )

    if (busy) {
      setAvailabilityStatus({ busy: true, message: 'Wybrany pracownik jest zajety w tym terminie.' })
    } else {
      setAvailabilityStatus({ busy: false, message: 'Wybrany pracownik jest wolny w tym terminie.' })
    }
  }, [appointmentsInSalon, endAt, selectedStaffId, startAt])

  const receptionistSalonName = salons.find((salon) => salon.id === selectedSalon)?.name

  const prefillAppointment = (slotStart: Date, staffId?: number) => {
    const duration = totalDuration > 0 ? totalDuration : 60
    const slotEnd = new Date(slotStart.getTime() + duration * 60_000)
    setStartAt(formatDateTimeLocal(slotStart))
    setEndAt(formatDateTimeLocal(slotEnd))
    if (staffId) setSelectedStaffId(staffId)
    setCalendarDate(formatDateOnly(slotStart))
    setAvailabilityStatus(null)
    setAppointmentDialogOpen(true)
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

  const detailAppointment = useMemo(
    () => [...appointmentsInSalon, ...calendarAppointments].find((row) => row.id === detailsAppointmentId) || null,
    [appointmentsInSalon, calendarAppointments, detailsAppointmentId],
  )

  const dayAppointments = useMemo(() => {
    const start = new Date(selectedDay)
    start.setHours(0, 0, 0, 0)
    const end = new Date(selectedDay)
    end.setHours(23, 59, 59, 999)
    return calendarAppointments.filter((row) => {
      const at = parseDate(row.start_at)
      return at >= start && at <= end
    })
  }, [calendarAppointments, selectedDay])

  const weekAppointments = useMemo(() => {
    const start = new Date(weekDays[0])
    start.setHours(0, 0, 0, 0)
    const end = new Date(weekDays[6])
    end.setHours(23, 59, 59, 999)
    return calendarAppointments.filter((row) => {
      const at = parseDate(row.start_at)
      return at >= start && at <= end
    })
  }, [calendarAppointments, weekDays])

  const halfHourSlots = useMemo(
    () => Array.from({ length: (SLOT_END_HOUR - SLOT_START_HOUR) * 2 }, (_, index) => {
      const hour = SLOT_START_HOUR + Math.floor(index / 2)
      const minute = index % 2 === 0 ? 0 : 30
      return { index, label: `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}` }
    }),
    [],
  )

  const hourSlots = useMemo(
    () => Array.from({ length: SLOT_END_HOUR - SLOT_START_HOUR }, (_, index) => ({
      index,
      label: `${String(SLOT_START_HOUR + index).padStart(2, '0')}:00`,
    })),
    [],
  )

  const getClientName = (clientIdValue: number) => clients.find((c) => c.id === clientIdValue)?.full_name || `#${clientIdValue}`
  const getClientLastName = (clientIdValue: number) => {
    const fullName = getClientName(clientIdValue).trim()
    const parts = fullName.split(' ').filter(Boolean)
    return parts.length > 1 ? parts[parts.length - 1] : fullName
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
  const getStaffLabel = (resourceIds: number[]) => resourceIds.map((id) => getResourceName(id)).filter(Boolean).join(', ')

  const renderAppointmentCard = (appointment: Appointment) => {
    const client = clients.find((c) => c.id === appointment.client_id)
    const serviceLabel = getServiceLabel(appointment.services)
    const staffLabel = getStaffLabel(appointment.resources)
    const lines = performedServiceLines.filter((line) => line.appointment_id === appointment.id)
    const highlighted = highlightedAppointmentId === appointment.id

    return (
      <Grid item xs={12} md={6} key={appointment.id}>
        <Card sx={highlighted ? { border: '2px solid #1976d2' } : undefined}>
          <CardContent>
            <Stack spacing={1}>
              <Typography variant="h6">{client?.full_name}</Typography>
              <Typography color="text.secondary">{appointment.start_at.replace('T', ' ')} - {appointment.end_at.replace('T', ' ')}</Typography>
              <Typography>Uslugi: {serviceLabel || 'do ustalenia'}</Typography>
              <Typography>Pracownicy: {staffLabel}</Typography>
              {appointment.bundle_id && (
                <Typography>Pakiet: {bundles.find((b) => b.id === appointment.bundle_id)?.name}</Typography>
              )}
              <Box>
                <Chip size="small" label={appointment.status} color={STATUS_COLOR[(appointment.status || '').toLowerCase()] || 'default'} sx={{ mr: 1 }} />
                <Chip size="small" variant="outlined" label={`Snapshot: ${getAppointmentRevenue(appointment.id)} PLN`} />
              </Box>
              {lines.length > 0 && (
                <Typography variant="body2" color="text.secondary">
                  Rozliczenie: {lines.length} linii zabiegow.
                </Typography>
              )}
              <Stack direction="row" spacing={1} flexWrap="wrap">
                <Button variant="outlined" onClick={() => setDetailsAppointmentId(appointment.id)}>Szczegoly</Button>
                {appointment.status !== 'done' && (
                  <Button variant="outlined" onClick={() => startExecution(appointment.id)}>
                    Oznacz jako wykonana
                  </Button>
                )}
                {appointment.status === 'done' && (
                  <Button variant="outlined" onClick={() => generateIssues(appointment.id)}>
                    Rozchod materialow
                  </Button>
                )}
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      </Grid>
    )
  }

  const renderDayView = () => {
    const columnHeight = halfHourSlots.length * HALF_HOUR_ROW_HEIGHT
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'grid', gridTemplateColumns: `72px repeat(${Math.max(salonStaff.length, 1)}, minmax(180px, 1fr))`, gap: 1 }}>
            <Box />
            {(salonStaff.length ? salonStaff : [{ id: 0, full_name: 'Brak pracownikow', can_be_booked: false }]).map((staff) => (
              <Typography key={staff.id} sx={{ fontWeight: 700, textAlign: 'center' }}>{staff.full_name}</Typography>
            ))}
            <Box sx={{ position: 'relative', height: columnHeight }}>
              {halfHourSlots.map((slot) => (
                <Box key={slot.index} sx={{ height: HALF_HOUR_ROW_HEIGHT, borderTop: '1px solid #e5e7eb', pr: 1 }}>
                  <Typography variant="caption">{slot.label}</Typography>
                </Box>
              ))}
            </Box>
            {(salonStaff.length ? salonStaff : []).map((staff) => {
              const staffAppointments = dayAppointments.filter((appointment) => appointment.resources.includes(staff.id))
              const positionedAppointments = buildDayAppointmentLayout(staffAppointments)
              return (
                <Box key={staff.id} sx={{ position: 'relative', height: columnHeight, border: '1px solid #e5e7eb', borderRadius: 2, overflow: 'hidden' }}>
                  {halfHourSlots.map((slot) => {
                    const slotTime = new Date(selectedDay)
                    slotTime.setHours(SLOT_START_HOUR + Math.floor(slot.index / 2), slot.index % 2 === 0 ? 0 : 30, 0, 0)
                    return (
                      <Box
                        key={`${staff.id}-${slot.index}`}
                        onClick={() => prefillAppointment(slotTime, staff.id)}
                        sx={{ height: HALF_HOUR_ROW_HEIGHT, borderTop: '1px solid #eef2f7', cursor: 'pointer' }}
                      />
                    )
                  })}
                  {positionedAppointments.map(({ appointment, lane, laneCount }) => {
                    const start = parseDate(appointment.start_at)
                    const end = parseDate(appointment.end_at)
                    const minutesFromGridStart = (start.getHours() - SLOT_START_HOUR) * 60 + start.getMinutes()
                    const durationMinutes = Math.max(30, (end.getTime() - start.getTime()) / 60000)
                    const top = (minutesFromGridStart / 30) * HALF_HOUR_ROW_HEIGHT
                    const height = (durationMinutes / 30) * HALF_HOUR_ROW_HEIGHT
                    const gap = 4
                    const widthCalc = `calc((100% - ${(laneCount + 1) * gap}px) / ${laneCount})`
                    const clientLastName = getClientLastName(appointment.client_id)
                    const offerLabel = getAppointmentOfferLabel(appointment)
                    const compactOffer = offerLabel.length > 16 ? `${offerLabel.slice(0, 16)}...` : offerLabel
                    const timeLabel = `${start.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}-${end.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}`
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

  const renderWeekView = () => {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'grid', gridTemplateColumns: '72px repeat(7, minmax(140px, 1fr))', gap: 1 }}>
            <Box />
            {weekDays.map((day) => (
              <Typography key={day.toISOString()} sx={{ fontWeight: 700, textAlign: 'center' }}>
                {day.toLocaleDateString('pl-PL', { weekday: 'short', day: '2-digit', month: '2-digit' })}
              </Typography>
            ))}
            {hourSlots.map((slot) => (
              <Fragment key={`row-${slot.index}`}>
                <Box key={`time-${slot.index}`} sx={{ height: HOUR_ROW_HEIGHT, borderTop: '1px solid #e5e7eb', pr: 1 }}>
                  <Typography variant="caption">{slot.label}</Typography>
                </Box>
                {weekDays.map((day) => {
                  const slotStart = new Date(day)
                  slotStart.setHours(SLOT_START_HOUR + slot.index, 0, 0, 0)
                  const slotEnd = new Date(slotStart)
                  slotEnd.setHours(slotStart.getHours() + 1, 0, 0, 0)
                  const cellKey = `${formatDateOnly(day)}-${slot.index}`
                  const slotAppointments = weekAppointments.filter((appointment) =>
                    overlaps(slotStart, slotEnd, parseDate(appointment.start_at), parseDate(appointment.end_at)),
                  )
                  const firstAppointment = slotAppointments[0]
                  const extraCount = Math.max(slotAppointments.length - 1, 0)
                  return (
                    <Box
                      key={cellKey}
                      onClick={() => {
                        if (!firstAppointment) {
                          prefillAppointment(slotStart)
                        }
                      }}
                      sx={{
                        position: 'relative',
                        height: HOUR_ROW_HEIGHT,
                        border: '1px solid #eef2f7',
                        borderRadius: 2,
                        p: 0.5,
                        cursor: firstAppointment ? 'default' : 'pointer',
                        overflow: 'hidden',
                      }}
                    >
                      {firstAppointment && (
                        <Stack direction="row" spacing={0.5} alignItems="flex-start">
                          <Box
                            onClick={(event) => {
                              event.stopPropagation()
                              setDetailsAppointmentId(firstAppointment.id)
                            }}
                            sx={{
                              flex: 1,
                              minWidth: 0,
                              bgcolor: getStatusBackground(firstAppointment.status),
                              color: '#fff',
                              px: 0.75,
                              py: 0.5,
                              borderRadius: 999,
                              fontSize: 11,
                              lineHeight: 1.2,
                              cursor: 'pointer',
                              whiteSpace: 'nowrap',
                              textOverflow: 'ellipsis',
                              overflow: 'hidden',
                            }}
                          >
                            {getClientLastName(firstAppointment.client_id)}
                          </Box>
                          {extraCount > 0 && (
                            <Chip
                              size="small"
                              label={`+${extraCount}`}
                              onClick={(event) => {
                                event.stopPropagation()
                                setExpandedWeekCell((prev) => (prev === cellKey ? null : cellKey))
                              }}
                              sx={{ height: 22 }}
                            />
                          )}
                        </Stack>
                      )}
                      {expandedWeekCell === cellKey && slotAppointments.length > 1 && (
                        <Box
                          sx={{
                            position: 'absolute',
                            top: 30,
                            left: 4,
                            right: 4,
                            zIndex: 2,
                            bgcolor: '#fff',
                            border: '1px solid #cbd5e1',
                            borderRadius: 1,
                            boxShadow: 3,
                            p: 0.5,
                            maxHeight: 140,
                            overflowY: 'auto',
                          }}
                        >
                          <Stack spacing={0.5}>
                            {slotAppointments.map((appointment) => (
                              <Button
                                key={appointment.id}
                                size="small"
                                variant="text"
                                onClick={(event) => {
                                  event.stopPropagation()
                                  setDetailsAppointmentId(appointment.id)
                                  setExpandedWeekCell(null)
                                }}
                                sx={{ justifyContent: 'flex-start', textTransform: 'none', px: 0.5 }}
                              >
                                {getClientLastName(appointment.client_id)} {parseDate(appointment.start_at).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}
                              </Button>
                            ))}
                          </Stack>
                        </Box>
                      )}
                    </Box>
                  )
                })}
              </Fragment>
            ))}
          </Box>
        </CardContent>
      </Card>
    )
  }

  const moveCalendar = (days: number) => {
    const next = new Date(selectedDay)
    next.setDate(selectedDay.getDate() + days)
    setCalendarDate(formatDateOnly(next))
  }

  return (
    <Stack spacing={2}>
      <Typography variant="h4">Kalendarz wizyt</Typography>

      {calendarView === 'list' && (
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Nowa wizyta</Typography>
          {flash && <Alert severity="info" sx={{ mb: 2 }}>{flash}</Alert>}

          {user?.role === 'receptionist' && (
            <Alert severity="success" sx={{ mb: 2 }}>
              Rejestracja dotyczy Twojego salonu: {receptionistSalonName}
            </Alert>
          )}

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
                      {staff.full_name}{staff.role_code ? ` (${staff.role_code})` : ''}
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

      {executionAppointmentId !== '' && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Rozliczenie wykonanej wizyty #{executionAppointmentId}
            </Typography>
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
                  <Button variant="outlined" onClick={addExecutionLine}>Dodaj linie zabiegu</Button>
                  <Button variant="contained" onClick={saveExecution}>Zapisz wykonanie</Button>
                </Stack>
              </Grid>
            </Grid>

            <Stack spacing={2} sx={{ mt: 2 }}>
              {executionLines.map((line, index) => (
                <Grid container spacing={2} key={`exec-line-${index}`}>
                  <Grid item xs={12} md={3}>
                    <TextField
                      select
                      fullWidth
                      label="Usluga"
                      value={line.service_id}
                      onChange={(e) => {
                        const serviceId = Number(e.target.value)
                        const appointment = appointments.find((item) => item.id === executionAppointmentId)
                        const defaultPrice = appointment
                          ? priceListItems.find((item) => item.salon_id === appointment.salon_id && item.service_id === serviceId)?.price ?? 0
                          : 0
                        setExecutionLine(index, { service_id: serviceId, price_snapshot: defaultPrice })
                      }}
                    >
                      {services.map((service) => <MenuItem key={service.id} value={service.id}>{service.code} - {service.name}</MenuItem>)}
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <TextField
                      select
                      fullWidth
                      label="Pracownik"
                      value={line.worker_id}
                      onChange={(e) => {
                        const workerId = Number(e.target.value)
                        const worker = resources.find((item) => item.id === workerId)
                        const roleId = worker?.role_ids.find((id) => bookableRoleIds.includes(id))
                        setExecutionLine(index, { worker_id: workerId, worker_role_id: roleId ?? '' })
                      }}
                    >
                      {resourcesInSalon
                        .filter((item) => appointments.find((a) => a.id === executionAppointmentId)?.resources.includes(item.id) ?? false)
                        .map((resource) => (
                          <MenuItem key={resource.id} value={resource.id}>{getResourceName(resource.id)}</MenuItem>
                        ))}
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <TextField
                      select
                      fullWidth
                      label="Rola"
                      value={line.worker_role_id}
                      onChange={(e) => setExecutionLine(index, { worker_role_id: Number(e.target.value) })}
                    >
                      {staffRoles
                        .filter((role) => bookableRoleIds.includes(role.id))
                        .map((role) => <MenuItem key={role.id} value={role.id}>{role.name}</MenuItem>)}
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <TextField
                      type="number"
                      fullWidth
                      label="Cena snapshot"
                      value={line.price_snapshot}
                      onChange={(e) => setExecutionLine(index, { price_snapshot: Number(e.target.value) })}
                    />
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <TextField
                      select
                      fullWidth
                      label="Kolor (opcjonalnie)"
                      value={line.color_product_id ?? ''}
                      onChange={(e) => {
                        const value = e.target.value
                        setExecutionLine(index, { color_product_id: value === '' ? undefined : Number(value) })
                      }}
                    >
                      <MenuItem value="">Brak</MenuItem>
                      {colorProducts.map((color) => <MenuItem key={color.id} value={color.id}>{color.code}</MenuItem>)}
                    </TextField>
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
                </Grid>
              ))}
            </Stack>
          </CardContent>
        </Card>
      )}

      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" alignItems={{ xs: 'stretch', md: 'center' }} spacing={1.5}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems={{ xs: 'stretch', md: 'center' }}>
          <TextField
            select
            size="small"
            label="Salon"
            value={selectedSalon}
            onChange={(e) => setSelectedSalon(Number(e.target.value))}
            disabled={user?.role === 'receptionist'}
            sx={{ minWidth: 220 }}
          >
            {allowedSalons.map((salon) => <MenuItem key={salon.id} value={salon.id}>{salon.name}</MenuItem>)}
          </TextField>
          <ToggleButtonGroup
            exclusive
            value={calendarView}
            onChange={(_, value) => { if (value) setCalendarView(value) }}
            size="small"
          >
            <ToggleButton value="list">Lista</ToggleButton>
            <ToggleButton value="day">Dzien</ToggleButton>
            <ToggleButton value="week">Tydzien</ToggleButton>
          </ToggleButtonGroup>
        </Stack>
        {calendarView !== 'list' && (
          <Stack direction="row" spacing={1} alignItems="center">
            <Button size="small" variant="outlined" onClick={() => moveCalendar(calendarView === 'day' ? -1 : -7)}>
              ←
            </Button>
            <TextField size="small" type="date" value={calendarDate} onChange={(e) => setCalendarDate(e.target.value)} />
            <Button size="small" variant="outlined" onClick={() => setCalendarDate(formatDateOnly(new Date()))}>
              Dzis
            </Button>
            <Button size="small" variant="outlined" onClick={() => moveCalendar(calendarView === 'day' ? 1 : 7)}>
              →
            </Button>
          </Stack>
        )}
      </Stack>

      {calendarView === 'day' && renderDayView()}
      {calendarView === 'week' && renderWeekView()}
      {calendarView === 'list' && (
        <Grid container spacing={2}>
          {appointmentsInSalon.map((appointment) => renderAppointmentCard(appointment))}
        </Grid>
      )}

      {calendarView !== 'list' && calendarLoading && <Alert severity="info">Ladowanie wizyt...</Alert>}

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
                  {staff.full_name}
                </MenuItem>
              ))}
            </TextField>
            {availabilityStatus && (
              <Alert severity={availabilityStatus.busy ? 'warning' : 'success'}>
                {availabilityStatus.message}
              </Alert>
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

      <Dialog open={detailsAppointmentId !== null} onClose={() => setDetailsAppointmentId(null)} fullWidth maxWidth="sm">
        <DialogTitle>Szczegoly wizyty</DialogTitle>
        <DialogContent>
          {detailAppointment && (
            <Stack spacing={1.25} sx={{ mt: 1 }}>
              <Typography><strong>Klient:</strong> {getClientName(detailAppointment.client_id)}</Typography>
              <Typography><strong>Termin:</strong> {detailAppointment.start_at.replace('T', ' ')} - {detailAppointment.end_at.replace('T', ' ')}</Typography>
              <Typography><strong>Pracownik:</strong> {getStaffLabel(detailAppointment.resources) || '-'}</Typography>
              <Typography><strong>Uslugi:</strong> {getServiceLabel(detailAppointment.services) || '-'}</Typography>
              <Typography><strong>Status:</strong> {detailAppointment.status}</Typography>
              <Typography><strong>Snapshot:</strong> {detailAppointment.total_price_snapshot.toFixed(2)} PLN</Typography>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          {detailAppointment && detailAppointment.status === 'done' && (
            <Button onClick={() => generateIssues(detailAppointment.id)}>Rozchod materialow</Button>
          )}
          <Button onClick={() => setDetailsAppointmentId(null)}>Zamknij</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}

export default SchedulesPage
