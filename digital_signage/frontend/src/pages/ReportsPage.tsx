import { Card, CardContent, Grid, Stack, Typography } from '@mui/material'
import { mockAppointments, mockResources } from '../mocks/bookingData'

const ReportsPage = () => {
  const monthlyRevenue = mockAppointments
    .filter((a) => a.status !== 'cancelled')
    .reduce((sum, appointment) => sum + appointment.total_price_snapshot, 0)

  const perWorker = mockResources.map((resource) => {
    const total = mockAppointments
      .filter((appointment) => appointment.resources.includes(resource.id))
      .reduce((sum, appointment) => sum + appointment.total_price_snapshot, 0)
    return { name: resource.name, total }
  })

  return (
    <Stack spacing={2}>
      <Typography variant="h4">Raporty okresowe</Typography>
      <Card>
        <CardContent>
          <Typography variant="h6">Miesieczne zamkniecie (demo)</Typography>
          <Typography color="text.secondary">Zakres: luty 2026</Typography>
          <Typography variant="h4" sx={{ mt: 1 }}>{monthlyRevenue} PLN</Typography>
        </CardContent>
      </Card>
      <Grid container spacing={2}>
        {perWorker.map((item) => (
          <Grid item xs={12} md={4} key={item.name}>
            <Card>
              <CardContent>
                <Typography variant="overline">Per pracownik</Typography>
                <Typography variant="h6">{item.name}</Typography>
                <Typography>{item.total} PLN</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Stack>
  )
}

export default ReportsPage
