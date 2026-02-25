import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useMemo, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useBooking } from '../contexts/BookingContext'

const SchedulesPage = () => {
  const { user } = useAuth()
  const { appointments, salons, clients, resources, services, bundles, addAppointment, estimateTotal } = useBooking()

  const defaultSalon = user?.assigned_salon_ids?.[0] ?? salons[0]?.id ?? 1
  const [selectedSalon, setSelectedSalon] = useState(defaultSalon)
  const [clientId, setClientId] = useState<number>(clients[0]?.id ?? 1)
  const [startAt, setStartAt] = useState('2026-02-26T15:00')
  const [endAt, setEndAt] = useState('2026-02-26T16:00')
  const [selectedResources, setSelectedResources] = useState<number[]>([])
  const [selectedServices, setSelectedServices] = useState<number[]>([])
  const [bundleId, setBundleId] = useState<number | ''>('')
  const [flash, setFlash] = useState('')

  const allowedSalons = useMemo(() => salons.filter((s) => user?.assigned_salon_ids?.includes(s.id)), [salons, user])
  const appointmentsInSalon = appointments.filter((a) => a.salon_id === selectedSalon)
  const resourcesInSalon = resources.filter((r) => r.salon_id === selectedSalon)
  const bundlesInSalon = bundles.filter((b) => b.salon_id === selectedSalon)

  const estimated = estimateTotal(selectedSalon, selectedServices, bundleId === '' ? undefined : bundleId)

  const createAppointment = () => {
    if (!clientId || selectedResources.length === 0 || (selectedServices.length === 0 && bundleId === '')) {
      setFlash('Uzupelnij klienta, zasoby i uslugi/pakiet.')
      return
    }

    addAppointment({
      salon_id: selectedSalon,
      client_id: clientId,
      start_at: startAt,
      end_at: endAt,
      resources: selectedResources,
      services: selectedServices,
      bundle_id: bundleId === '' ? undefined : bundleId,
    })

    setFlash('Wizyta dodana (demo, local state).')
  }

  return (
    <Stack spacing={2}>
      <Typography variant="h4">Kalendarz wizyt</Typography>

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Nowa wizyta</Typography>
          {flash && <Alert severity="info" sx={{ mb: 2 }}>{flash}</Alert>}
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <TextField
                select
                label="Salon"
                fullWidth
                value={selectedSalon}
                onChange={(e) => setSelectedSalon(Number(e.target.value))}
                disabled={user?.role === 'receptionist'}
              >
                {allowedSalons.map((salon) => <MenuItem key={salon.id} value={salon.id}>{salon.name}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField select label="Klient" fullWidth value={clientId} onChange={(e) => setClientId(Number(e.target.value))}>
                {clients.map((client) => <MenuItem key={client.id} value={client.id}>{client.full_name}</MenuItem>)}
              </TextField>
            </Grid>
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

            <Grid item xs={12} md={3}>
              <TextField label="Start" type="datetime-local" fullWidth value={startAt} onChange={(e) => setStartAt(e.target.value)} />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField label="Koniec" type="datetime-local" fullWidth value={endAt} onChange={(e) => setEndAt(e.target.value)} />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel id="resources-label">Pracownicy</InputLabel>
                <Select
                  labelId="resources-label"
                  multiple
                  value={selectedResources}
                  label="Pracownicy"
                  onChange={(e) => setSelectedResources((e.target.value as number[]))}
                >
                  {resourcesInSalon.map((resource) => <MenuItem key={resource.id} value={resource.id}>{resource.name}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel id="services-label">Uslugi</InputLabel>
                <Select
                  labelId="services-label"
                  multiple
                  value={selectedServices}
                  label="Uslugi"
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

          return (
            <Grid item xs={12} md={6} key={appointment.id}>
              <Card>
                <CardContent>
                  <Stack spacing={1}>
                    <Typography variant="h6">{client?.full_name}</Typography>
                    <Typography color="text.secondary">{appointment.start_at.replace('T', ' ')} - {appointment.end_at.replace('T', ' ')}</Typography>
                    <Typography>Uslugi: {serviceLabel || 'z pakietu'}</Typography>
                    <Typography>Pracownicy: {staffLabel}</Typography>
                    {appointment.bundle_id && (
                      <Typography>Pakiet: {bundles.find((b) => b.id === appointment.bundle_id)?.name}</Typography>
                    )}
                    <Box>
                      <Chip size="small" label={appointment.status} color={appointment.status === 'done' ? 'success' : 'default'} sx={{ mr: 1 }} />
                      <Chip size="small" variant="outlined" label={`Snapshot: ${appointment.total_price_snapshot} PLN`} />
                    </Box>
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
