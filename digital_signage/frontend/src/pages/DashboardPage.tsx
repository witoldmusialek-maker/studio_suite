import { useEffect, useState } from 'react'
import { Grid, Paper, Typography, Box, Button } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { Display, Alert } from '../types'

const DashboardPage = () => {
  const navigate = useNavigate()
  const [displays, setDisplays] = useState<Display[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [displaysRes, alertsRes] = await Promise.all([
        api.get('/displays'),
        api.get('/alerts/active'),
      ])
      setDisplays(displaysRes.data)
      setAlerts(alertsRes.data)
    } catch (error) {
      console.error('Błąd pobierania danych:', error)
    } finally {
      setLoading(false)
    }
  }

  const onlineCount = displays.filter((d) => d.status === 'online').length
  const offlineCount = displays.filter((d) => d.status === 'offline').length
  const activeAlertsCount = alerts.length

  if (loading) {
    return <Typography>Ładowanie...</Typography>
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Wyświetlacze</Typography>
            <Typography variant="h4">{displays.length}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Online</Typography>
            <Typography variant="h4" color="success.main">
              {onlineCount}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Offline</Typography>
            <Typography variant="h4" color="error.main">
              {offlineCount}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Aktywne Alerty</Typography>
            <Typography variant="h4" color="warning.main">
              {activeAlertsCount}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      <Paper sx={{ p: 2, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Moduly
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          <Button variant="outlined" onClick={() => navigate('/schedules')}>Harmonogramy</Button>
          <Button variant="outlined" onClick={() => navigate('/groups')}>Grupy</Button>
          <Button variant="outlined" onClick={() => navigate('/bells/schedules')}>Harmonogramy dzwonkow</Button>
          <Button variant="outlined" onClick={() => navigate('/reports')}>Raporty</Button>
          <Button variant="outlined" onClick={() => navigate('/alerts')}>Alerty</Button>
        </Box>
      </Paper>
    </Box>
  )
}

export default DashboardPage



