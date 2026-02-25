import { Card, CardContent, Grid, MenuItem, Stack, TextField, Typography } from '@mui/material'
import { useMemo, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useBooking } from '../contexts/BookingContext'

const ReportsPage = () => {
  const { user } = useAuth()
  const { appointments, resources } = useBooking()

  const [preset, setPreset] = useState<'month_end' | 'custom'>('month_end')
  const [fromDate, setFromDate] = useState('2026-02-01T00:00')
  const [toDate, setToDate] = useState('2026-02-28T23:59')

  const visible = useMemo(
    () => appointments.filter((a) => user?.assigned_salon_ids?.includes(a.salon_id)),
    [appointments, user],
  )

  const ranged = visible.filter((a) => {
    const stamp = new Date(a.start_at).getTime()
    return stamp >= new Date(fromDate).getTime() && stamp <= new Date(toDate).getTime()
  })

  const total = ranged.filter((a) => a.status !== 'cancelled').reduce((sum, appointment) => sum + appointment.total_price_snapshot, 0)

  const perWorker = resources
    .filter((resource) => user?.assigned_salon_ids?.includes(resource.salon_id))
    .map((resource) => {
      const subtotal = ranged
        .filter((appointment) => appointment.resources.includes(resource.id))
        .reduce((sum, appointment) => sum + appointment.total_price_snapshot, 0)
      return { name: resource.name, total: subtotal }
    })

  return (
    <Stack spacing={2}>
      <Typography variant="h4">Raporty okresowe</Typography>

      <Card>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
              <TextField
                select
                fullWidth
                label="Tryb"
                value={preset}
                onChange={(e) => {
                  const value = e.target.value as 'month_end' | 'custom'
                  setPreset(value)
                  if (value === 'month_end') {
                    setFromDate('2026-02-01T00:00')
                    setToDate('2026-02-28T23:59')
                  }
                }}
              >
                <MenuItem value="month_end">Koniec miesiaca</MenuItem>
                <MenuItem value="custom">Zakres niestandardowy</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField label="Od" type="datetime-local" fullWidth value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField label="Do" type="datetime-local" fullWidth value={toDate} onChange={(e) => setToDate(e.target.value)} />
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="overline">Liczba wizyt</Typography>
              <Typography variant="h5">{ranged.length}</Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="h6">Przychod w okresie</Typography>
          <Typography color="text.secondary">{fromDate.replace('T', ' ')} - {toDate.replace('T', ' ')}</Typography>
          <Typography variant="h4" sx={{ mt: 1 }}>{total} PLN</Typography>
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
