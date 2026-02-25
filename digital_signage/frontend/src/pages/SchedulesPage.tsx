import { Card, CardContent, Chip, Grid, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { useMemo, useState } from 'react'
import { mockAppointments, mockClients, mockResources, mockSalons, mockServices } from '../mocks/bookingData'
import { useAuth } from '../contexts/AuthContext'

const SchedulesPage = () => {
  const { user } = useAuth()
  const [selectedSalon, setSelectedSalon] = useState(user?.assigned_salon_ids?.[0] ?? 1)

  const allowedSalons = useMemo(
    () => mockSalons.filter((s) => user?.assigned_salon_ids?.includes(s.id)),
    [user],
  )

  const appointments = mockAppointments.filter((a) => a.salon_id === selectedSalon)

  return (
    <Stack spacing={2}>
      <Typography variant="h4">Kalendarz wizyt</Typography>
      <TextField
        select
        label="Salon"
        value={selectedSalon}
        onChange={(e) => setSelectedSalon(Number(e.target.value))}
        disabled={user?.role === 'receptionist'}
        sx={{ maxWidth: 380 }}
      >
        {allowedSalons.map((salon) => (
          <MenuItem key={salon.id} value={salon.id}>{salon.name}</MenuItem>
        ))}
      </TextField>

      <Grid container spacing={2}>
        {appointments.map((appointment) => {
          const client = mockClients.find((c) => c.id === appointment.client_id)
          const services = appointment.services
            .map((id) => mockServices.find((service) => service.id === id)?.name)
            .filter(Boolean)
            .join(', ')
          const staff = appointment.resources
            .map((id) => mockResources.find((resource) => resource.id === id)?.name)
            .filter(Boolean)
            .join(', ')

          return (
            <Grid item xs={12} md={6} key={appointment.id}>
              <Card>
                <CardContent>
                  <Stack spacing={1}>
                    <Typography variant="h6">{client?.full_name}</Typography>
                    <Typography color="text.secondary">{appointment.start_at.replace('T', ' ')} - {appointment.end_at.replace('T', ' ')}</Typography>
                    <Typography>Uslugi: {services}</Typography>
                    <Typography>Pracownicy: {staff}</Typography>
                    <Stack direction="row" spacing={1}>
                      <Chip size="small" label={appointment.status} color={appointment.status === 'done' ? 'success' : 'default'} />
                      <Chip size="small" label={`Snapshot: ${appointment.total_price_snapshot} PLN`} variant="outlined" />
                    </Stack>
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
