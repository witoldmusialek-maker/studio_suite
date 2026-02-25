import { Card, CardContent, Chip, Grid, Stack, Typography } from '@mui/material'
import { useAuth } from '../contexts/AuthContext'
import { useBooking } from '../contexts/BookingContext'

const DashboardPage = () => {
  const { user } = useAuth()
  const { salons, clients, appointments, resources, staffRoles } = useBooking()

  const visibleAppointments = appointments.filter((a) => user?.assigned_salon_ids?.includes(a.salon_id))
  const done = visibleAppointments.filter((a) => a.status === 'done').length
  const planned = visibleAppointments.filter((a) => a.status !== 'done' && a.status !== 'cancelled').length

  const bookableRoleIds = staffRoles
    .filter((role) => role.code === 'FRYZJER' || role.code === 'MANICURZYSTKA')
    .map((role) => role.id)

  const bookableResources = resources.filter((resource) =>
    resource.role_ids.some((roleId) => bookableRoleIds.includes(roleId)),
  )

  return (
    <Stack spacing={3}>
      <Typography variant="h4">Dashboard operacyjny</Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} md={3}>
          <Card><CardContent><Typography variant="overline">Salony</Typography><Typography variant="h4">{salons.length}</Typography></CardContent></Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card><CardContent><Typography variant="overline">Klienci</Typography><Typography variant="h4">{clients.length}</Typography></CardContent></Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card><CardContent><Typography variant="overline">Wizyty aktywne</Typography><Typography variant="h4">{planned}</Typography></CardContent></Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card><CardContent><Typography variant="overline">Wykonane</Typography><Typography variant="h4">{done}</Typography></CardContent></Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>Za³o¿enia MVP (frontend-only)</Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            <Chip label="Role: admin / manager / recepcjonista" />
            <Chip label="Kalendarz multi-resource" />
            <Chip label="Cenniki us³ug i pakietów" />
            <Chip label="Historia klienta i zabiegów" />
            <Chip label="Snapshot cen w czasie" />
          </Stack>
          <Typography sx={{ mt: 2 }} color="text.secondary">
            Dane sa teraz interaktywne w ramach sesji frontendu: mozna dodawac klientow i wizyty.
          </Typography>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>Dostepni pracownicy (fryzjer / manicure)</Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {bookableResources.map((r) => <Chip key={r.id} label={r.name} color="primary" variant="outlined" />)}
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  )
}

export default DashboardPage
