import { useEffect, useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Grid,
} from '@mui/material'
import { api } from '../services/api'
import { Display } from '../types'

type DailyReport = {
  total_displays: number
  average_online_percentage: number
}

type OfflineReport = {
  display_id: number
  offline_percentage: number
  total_offline_seconds: number
}

const ReportsPage = () => {
  const [daily, setDaily] = useState<DailyReport | null>(null)
  const [weekly, setWeekly] = useState<DailyReport | null>(null)
  const [offline, setOffline] = useState<OfflineReport | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchReports()
  }, [])

  const fetchReports = async () => {
    try {
      const [dailyRes, weeklyRes, displaysRes] = await Promise.all([
        api.get('/reports/daily'),
        api.get('/reports/weekly'),
        api.get('/displays'),
      ])

      setDaily(dailyRes.data)
      setWeekly(weeklyRes.data)

      const displays: Display[] = displaysRes.data || []
      if (displays.length > 0) {
        const today = new Date().toISOString().slice(0, 10)
        const offlineRes = await api.get(
          `/reports/offline?display_id=${displays[0].id}&start_date=${today}&end_date=${today}`
        )
        setOffline(offlineRes.data)
      }
    } catch (error) {
      console.error('Błąd pobierania raportów:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <Typography>Ładowanie...</Typography>
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Raporty
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Dzienny</Typography>
            <Typography>Wyświetlacze: {daily?.total_displays ?? '-'}</Typography>
            <Typography>Średni online: {daily?.average_online_percentage ?? '-'}%</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Tygodniowy</Typography>
            <Typography>Wyświetlacze: {weekly?.total_displays ?? '-'}</Typography>
            <Typography>Średni online: {weekly?.average_online_percentage ?? '-'}%</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Offline (1 wyświetlacz)</Typography>
            <Typography>Display ID: {offline?.display_id ?? '-'}</Typography>
            <Typography>Offline: {offline?.offline_percentage ?? '-'}%</Typography>
            <Typography>Czas offline: {offline?.total_offline_seconds ?? '-'} s</Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}

export default ReportsPage
