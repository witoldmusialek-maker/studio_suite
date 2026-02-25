import { Card, CardContent, Chip, Grid, Stack, Typography } from '@mui/material'
import { mockAppointments, mockClients, mockResources, mockSalons } from '../mocks/bookingData'

const DashboardPage = () => {
  const done = mockAppointments.filter((a) => a.status === 'done').length
  const planned = mockAppointments.filter((a) => a.status !== 'done' && a.status !== 'cancelled').length

  return (
    <Stack spacing={3}>
      <Typography variant="h4">Dashboard operacyjny</Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} md={3}>
          <Card><CardContent><Typography variant="overline">Salony</Typography><Typography variant="h4">{mockSalons.length}</Typography></CardContent></Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card><CardContent><Typography variant="overline">Klienci</Typography><Typography variant="h4">{mockClients.length}</Typography></CardContent></Card>
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
            Ten ekran jest makiet¹ do konsultacji przep³ywów. Dane s¹ demonstracyjne i trzymane lokalnie.
          </Typography>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>Dostêpni pracownicy (demo)</Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {mockResources.map((r) => <Chip key={r.id} label={r.name} color="primary" variant="outlined" />)}
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  )
}

export default DashboardPage
