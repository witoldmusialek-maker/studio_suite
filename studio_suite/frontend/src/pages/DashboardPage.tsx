import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Alert,
  Card,
  CardContent,
  Chip,
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

const STATUS_COLOR: Record<string, 'default' | 'primary' | 'success' | 'error'> = {
  planned: 'default',
  started: 'primary',
  in_progress: 'primary',
  done: 'success',
  completed: 'success',
  cancelled: 'error',
}

const startOfDay = (base: Date) => new Date(base.getFullYear(), base.getMonth(), base.getDate(), 0, 0, 0, 0)
const endOfDay = (base: Date) => new Date(base.getFullYear(), base.getMonth(), base.getDate(), 23, 59, 59, 999)

const DashboardPage = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { salons, clients, resources, services, appointments } = useBooking()

  const [selectedSalonId, setSelectedSalonId] = useState<number | ''>('')
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [todayAppointments, setTodayAppointments] = useState<AppointmentRow[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    if (selectedSalonId === '' && salons.length) {
      const nextSalonId = user?.assigned_salon_ids?.[0] ?? salons[0].id
      setSelectedSalonId(nextSalonId)
    }
  }, [salons, selectedSalonId, user?.assigned_salon_ids])

  useEffect(() => {
    if (selectedSalonId === '') return
    const fetchData = async () => {
      setError('')
      try {
        const [statsRes, appointmentsRes] = await Promise.all([
          api.get<StatsResponse>('/booking/stats', { params: { date: 'today', salon_id: selectedSalonId } }),
          api.get<AppointmentRow[]>('/booking/appointments', { params: { date: 'today', salon_id: selectedSalonId, sort: 'start_asc' } }),
        ])
        setStats(statsRes.data)
        setTodayAppointments(appointmentsRes.data || [])
      } catch (err: any) {
        setError(err?.response?.data?.detail || 'Nie udalo sie pobrac danych dashboardu.')
      }
    }
    fetchData()
  }, [selectedSalonId])

  const salonName = salons.find((salon) => salon.id === selectedSalonId)?.name || ''
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(today.getDate() + 1)
  const dayAfterTomorrow = new Date(today)
  dayAfterTomorrow.setDate(today.getDate() + 2)

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
  }, [appointments, dayAfterTomorrow, selectedSalonId, tomorrow])

  const staffToday = useMemo(() => {
    const byStaff = new Map<number, { count: number; revenue: number }>()
    for (const row of todayAppointments) {
      for (const staffId of row.resources) {
        const current = byStaff.get(staffId) || { count: 0, revenue: 0 }
        current.count += 1
        current.revenue += row.total_price_snapshot || 0
        byStaff.set(staffId, current)
      }
    }
    return Array.from(byStaff.entries())
      .map(([staffId, value]) => ({
        staffId,
        name: resources.find((item) => item.id === staffId)?.name || `#${staffId}`,
        count: value.count,
        revenue: value.revenue,
      }))
      .sort((a, b) => b.count - a.count || b.revenue - a.revenue)
  }, [resources, todayAppointments])

  const kpis = stats
    ? [
        { label: 'Wizyty dzis', value: stats.appointments },
        { label: 'W trakcie', value: stats.appointments_in_progress },
        { label: 'Wykonane dzis', value: stats.completed_appointments },
        ...(user?.role === 'receptionist' ? [] : [{ label: 'Przychod dzis', value: `${stats.revenue_today.toFixed(2)} PLN` }]),
      ]
    : []

  const resolveClient = (clientId: number) => clients.find((item) => item.id === clientId)?.full_name || `#${clientId}`
  const resolveStaff = (resourceIds: number[]) =>
    resourceIds.map((id) => resources.find((item) => item.id === id)?.name).filter(Boolean).join(', ') || '-'
  const resolveServices = (serviceIds: number[]) =>
    serviceIds.map((id) => services.find((item) => item.id === id)?.name).filter(Boolean).join(', ') || '-'

  return (
    <Stack spacing={3}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1.5}>
        <Typography variant="h4">Dashboard operacyjny</Typography>
        <FormControl size="small" sx={{ minWidth: 280 }}>
          <InputLabel>Salon</InputLabel>
          <Select label="Salon" value={selectedSalonId} onChange={(e) => setSelectedSalonId(e.target.value === '' ? '' : Number(e.target.value))}>
            {salons.map((salon) => <MenuItem key={salon.id} value={salon.id}>{salon.name}</MenuItem>)}
          </Select>
        </FormControl>
      </Stack>

      {error && <Alert severity="error">{error}</Alert>}

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

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
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
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Pracownicy dzis</Typography>
              <Stack spacing={1.25}>
                {staffToday.map((row) => (
                  <Stack key={row.staffId} direction="row" justifyContent="space-between" sx={{ border: '1px solid #e5e7eb', borderRadius: 2, p: 1.25 }}>
                    <Typography sx={{ fontWeight: 600 }}>{row.name}</Typography>
                    <Stack direction="row" spacing={1}>
                      <Chip size="small" label={`${row.count} wizyt`} />
                      {user?.role !== 'receptionist' && <Chip size="small" color="success" label={`${row.revenue.toFixed(2)} PLN`} />}
                    </Stack>
                  </Stack>
                ))}
                {!staffToday.length && <Typography color="text.secondary">Brak pracownikow z wizytami dzis.</Typography>}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Stack>
  )
}

export default DashboardPage
