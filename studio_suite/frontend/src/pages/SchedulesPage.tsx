import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  FormControl,
  FormControlLabel,
  Grid,
  InputLabel,
  MenuItem,
  Radio,
  RadioGroup,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useBooking } from '../contexts/BookingContext'

const parseDate = (value: string) => new Date(value)

const overlaps = (startA: Date, endA: Date, startB: Date, endB: Date) => startA < endB && startB < endA

type ExecutionLineDraft = {
  service_id: number | ''
  worker_id: number | ''
  worker_role_id: number | ''
  price_snapshot: number
  color_product_id?: number
}

const SchedulesPage = () => {
  const { user } = useAuth()
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
  const [selectedResources, setSelectedResources] = useState<number[]>([])
  const [selectedServices, setSelectedServices] = useState<number[]>([])
  const [bundleId, setBundleId] = useState<number | ''>('')
  const [flash, setFlash] = useState('')

  const [availabilityResourceId, setAvailabilityResourceId] = useState<number | ''>('')
  const [availabilityAt, setAvailabilityAt] = useState('2026-02-26T17:00')
  const [availabilityDuration, setAvailabilityDuration] = useState(60)

  const [executionAppointmentId, setExecutionAppointmentId] = useState<number | ''>('')
  const [executionPerformedAt, setExecutionPerformedAt] = useState('2026-02-26T16:00')
  const [executionLines, setExecutionLines] = useState<ExecutionLineDraft[]>([])

  const allowedSalons = useMemo(() => salons.filter((s) => user?.assigned_salon_ids?.includes(s.id)), [salons, user])
  const appointmentsInSalon = appointments.filter((a) => a.salon_id === selectedSalon)

  const bookableRoleIds = staffRoles
    .filter((role) => role.code === 'FRYZJER' || role.code === 'MANICURZYSTKA')
    .map((role) => role.id)

  const resourcesInSalon = resources.filter(
    (resource) =>
      resource.salon_id === selectedSalon && resource.role_ids.some((roleId) => bookableRoleIds.includes(roleId)),
  )

  useEffect(() => {
    if (resourcesInSalon.length > 0 && availabilityResourceId === '') {
      setAvailabilityResourceId(resourcesInSalon[0].id)
    }
    if (availabilityResourceId !== '' && !resourcesInSalon.some((resource) => resource.id === availabilityResourceId)) {
      setAvailabilityResourceId(resourcesInSalon[0]?.id ?? '')
    }
  }, [availabilityResourceId, resourcesInSalon])

  const bundlesInSalon = bundles.filter((b) => b.salon_id === selectedSalon)
  const estimated = estimateTotal(selectedSalon, selectedServices, bundleId === '' ? undefined : bundleId)

  const createAppointment = () => {
    if (selectedResources.length === 0) {
      setFlash('Wybierz przynajmniej jednego pracownika.')
      return
    }

    let targetClientId = clientId
    if (clientMode === 'new') {
      if (!newClientName || !newClientPhone) {
        setFlash('Dla nowego klienta podaj imie i nazwisko oraz telefon.')
        return
      }
      const created = addClient({ full_name: newClientName, phone: newClientPhone, email: newClientEmail })
      targetClientId = created.id
      setNewClientName('')
      setNewClientPhone('')
      setNewClientEmail('')
      setClientMode('existing')
      setClientId(created.id)
    }

    addAppointment({
      salon_id: selectedSalon,
      client_id: targetClientId,
      start_at: startAt,
      end_at: endAt,
      resources: selectedResources,
      services: selectedServices,
      bundle_id: bundleId === '' ? undefined : bundleId,
    })

    setFlash('Wizyta dodana (demo, local state).')
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

  const saveExecution = () => {
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

    completeAppointment({
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
    setFlash('Wizyta oznaczona jako wykonana. Zapisano linie zabiegow z cena snapshot.')
  }

  const availability = useMemo(() => {
    if (availabilityResourceId === '' || !availabilityAt) return null

    const wantedStart = parseDate(availabilityAt)
    const wantedEnd = new Date(wantedStart.getTime() + availabilityDuration * 60_000)
    const resourceAppointments = appointmentsInSalon.filter((appointment) =>
      appointment.resources.includes(availabilityResourceId),
    )

    const busy = resourceAppointments.some((appointment) =>
      overlaps(wantedStart, wantedEnd, parseDate(appointment.start_at), parseDate(appointment.end_at)),
    )

    const suggestions: Date[] = []
    const cursor = new Date(wantedStart)
    const limit = new Date(wantedStart.getTime() + 7 * 24 * 60 * 60_000)

    while (cursor < limit && suggestions.length < 5) {
      const slotEnd = new Date(cursor.getTime() + availabilityDuration * 60_000)
      const slotBusy = resourceAppointments.some((appointment) =>
        overlaps(cursor, slotEnd, parseDate(appointment.start_at), parseDate(appointment.end_at)),
      )
      if (!slotBusy) suggestions.push(new Date(cursor))
      cursor.setMinutes(cursor.getMinutes() + 30)
    }

    return { busy, suggestions }
  }, [appointmentsInSalon, availabilityAt, availabilityDuration, availabilityResourceId])

  const receptionistSalonName = salons.find((salon) => salon.id === selectedSalon)?.name

  return (
    <Stack spacing={2}>
      <Typography variant="h4">Kalendarz wizyt</Typography>

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Nowa wizyta</Typography>
          {flash && <Alert severity="info" sx={{ mb: 2 }}>{flash}</Alert>}

          {user?.role === 'receptionist' && (
            <Alert severity="success" sx={{ mb: 2 }}>
              Rejestracja dotyczy Twojego salonu: {receptionistSalonName}
            </Alert>
          )}

          <Grid container spacing={2}>
            {user?.role !== 'receptionist' && (
              <Grid item xs={12} md={4}>
                <TextField
                  select
                  label="Salon"
                  fullWidth
                  value={selectedSalon}
                  onChange={(e) => setSelectedSalon(Number(e.target.value))}
                >
                  {allowedSalons.map((salon) => <MenuItem key={salon.id} value={salon.id}>{salon.name}</MenuItem>)}
                </TextField>
              </Grid>
            )}

            <Grid item xs={12} md={user?.role === 'receptionist' ? 12 : 8}>
              <RadioGroup row value={clientMode} onChange={(e) => setClientMode(e.target.value as 'existing' | 'new')}>
                <FormControlLabel value="existing" control={<Radio />} label="Istniejacy klient" />
                <FormControlLabel value="new" control={<Radio />} label="Nowy klient" />
              </RadioGroup>
            </Grid>

            {clientMode === 'existing' ? (
              <Grid item xs={12} md={6}>
                <TextField select label="Klient" fullWidth value={clientId} onChange={(e) => setClientId(Number(e.target.value))}>
                  {clients.map((client) => <MenuItem key={client.id} value={client.id}>{client.full_name}</MenuItem>)}
                </TextField>
              </Grid>
            ) : (
              <>
                <Grid item xs={12} md={4}>
                  <TextField label="Nowy klient - imie i nazwisko" fullWidth value={newClientName} onChange={(e) => setNewClientName(e.target.value)} />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField label="Telefon" fullWidth value={newClientPhone} onChange={(e) => setNewClientPhone(e.target.value)} />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField label="Email (opcjonalnie)" fullWidth value={newClientEmail} onChange={(e) => setNewClientEmail(e.target.value)} />
                </Grid>
              </>
            )}

            <Grid item xs={12} md={4}>
              <TextField
                select
                label="Pakiet (opcjonalnie)"
                fullWidth
                value={bundleId}
                onChange={(e) => setBundleId(e.target.value === '' ? '' : Number(e.target.value))}
              >
                <MenuItem value="">Brak pakietu</MenuItem>
                {bundlesInSalon.map((bundle) => <MenuItem key={bundle.id} value={bundle.id}>{bundle.name}</MenuItem>)}
              </TextField>
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField label="Start" type="datetime-local" fullWidth value={startAt} onChange={(e) => setStartAt(e.target.value)} />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField label="Koniec" type="datetime-local" fullWidth value={endAt} onChange={(e) => setEndAt(e.target.value)} />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel id="resources-label">Pracownicy (fryzjer/manicure)</InputLabel>
                <Select
                  labelId="resources-label"
                  multiple
                  value={selectedResources}
                  label="Pracownicy (fryzjer/manicure)"
                  onChange={(e) => setSelectedResources((e.target.value as number[]))}
                >
                  {resourcesInSalon.map((resource) => <MenuItem key={resource.id} value={resource.id}>{resource.name}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel id="services-label">Uslugi (opcjonalnie)</InputLabel>
                <Select
                  labelId="services-label"
                  multiple
                  value={selectedServices}
                  label="Uslugi (opcjonalnie)"
                  onChange={(e) => setSelectedServices((e.target.value as number[]))}
                >
                  {services.map((service) => <MenuItem key={service.id} value={service.id}>{service.code} - {service.name}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Chip label={`Snapshot ceny: ${estimated} PLN`} color="secondary" />
                <Button variant="contained" onClick={createAppointment}>Dodaj wizyte</Button>
              </Stack>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Szybka dostepnosc pracownika</Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <TextField
                select
                fullWidth
                label="Pracownik"
                value={availabilityResourceId}
                onChange={(e) => setAvailabilityResourceId(Number(e.target.value))}
              >
                {resourcesInSalon.map((resource) => <MenuItem key={resource.id} value={resource.id}>{resource.name}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField label="Termin" type="datetime-local" fullWidth value={availabilityAt} onChange={(e) => setAvailabilityAt(e.target.value)} />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="Czas (min)"
                type="number"
                fullWidth
                value={availabilityDuration}
                onChange={(e) => setAvailabilityDuration(Number(e.target.value))}
              />
            </Grid>
          </Grid>

          {availability && (
            <Box sx={{ mt: 2 }}>
              <Alert severity={availability.busy ? 'warning' : 'success'} sx={{ mb: 2 }}>
                {availability.busy ? 'Ten termin jest zajety.' : 'Ten termin jest wolny.'}
              </Alert>
              {availability.busy && (
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {availability.suggestions.map((slot, index) => (
                    <Chip
                      key={`${slot.toISOString()}-${index}`}
                      label={slot.toLocaleString('pl-PL', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                    />
                  ))}
                </Stack>
              )}
            </Box>
          )}
        </CardContent>
      </Card>

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
                        .filter(
                          (item) =>
                            appointments.find((a) => a.id === executionAppointmentId)?.resources.includes(item.id) ?? false,
                        )
                        .map((resource) => (
                        <MenuItem key={resource.id} value={resource.id}>{resource.name}</MenuItem>
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

      <Grid container spacing={2}>
        {appointmentsInSalon.map((appointment) => {
          const client = clients.find((c) => c.id === appointment.client_id)
          const serviceLabel = appointment.services
            .map((id) => services.find((service) => service.id === id)?.name)
            .filter(Boolean)
            .join(', ')
          const staffLabel = appointment.resources
            .map((id) => resources.find((resource) => resource.id === id)?.name)
            .filter(Boolean)
            .join(', ')
          const lines = performedServiceLines.filter((line) => line.appointment_id === appointment.id)

          return (
            <Grid item xs={12} md={6} key={appointment.id}>
              <Card>
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
                      <Chip size="small" label={appointment.status} color={appointment.status === 'done' ? 'success' : 'default'} sx={{ mr: 1 }} />
                      <Chip size="small" variant="outlined" label={`Snapshot: ${getAppointmentRevenue(appointment.id)} PLN`} />
                    </Box>
                    {lines.length > 0 && (
                      <Typography variant="body2" color="text.secondary">
                        Rozliczenie: {lines.length} linii zabiegow.
                      </Typography>
                    )}
                    {appointment.status !== 'done' && (
                      <Button variant="outlined" onClick={() => startExecution(appointment.id)}>
                        Oznacz jako wykonana
                      </Button>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          )
        })}
      </Grid>
    </Stack>
  )
}

export default SchedulesPage
