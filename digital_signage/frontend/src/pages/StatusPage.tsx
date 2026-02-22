import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material'
import {
  CheckCircle as OnlineIcon,
  Error as OfflineIcon,
  Warning as ErrorIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import { api } from '../services/api'
import { Display } from '../types'
import { connectWebSocket } from '../services/websocket'

const StatusPage = () => {
  const navigate = useNavigate()
  const [displays, setDisplays] = useState<Display[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  useEffect(() => {
    fetchStatus()
    const socket = connectWebSocket()

    socket.on('display_status_update', (data: Display) => {
      setDisplays((prev) =>
        prev.map((d) => (d.id === data.id ? { ...d, ...data } : d))
      )
      setLastUpdate(new Date())
    })

    // OdĹ›wieĹĽanie co 30 sekund
    const interval = setInterval(fetchStatus, 30000)

    return () => {
      clearInterval(interval)
      socket.off('display_status_update')
    }
  }, [])

  const fetchStatus = async () => {
    try {
      const response = await api.get('/displays')
      setDisplays(response.data)
      setLastUpdate(new Date())
    } catch (error) {
      console.error('BĹ‚Ä…d pobierania statusu:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
        return <OnlineIcon color="success" />
      case 'offline':
        return <OfflineIcon color="error" />
      case 'error':
        return <ErrorIcon color="warning" />
      default:
        return null
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'success'
      case 'offline':
        return 'error'
      case 'error':
        return 'warning'
      default:
        return 'default'
    }
  }

  if (loading) {
    return <Typography>Ĺadowanie...</Typography>
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Status WyĹ›wietlaczy</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Ostatnia aktualizacja: {lastUpdate.toLocaleTimeString('pl-PL')}
          </Typography>
          <Tooltip title="OdĹ›wieĹĽ">
            <IconButton onClick={fetchStatus}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Grid container spacing={2}>
        {displays.map((display) => (
          <Grid item xs={12} sm={6} md={4} key={display.id}>
            <Card
              sx={{
                cursor: 'pointer',
                '&:hover': { boxShadow: 4 },
              }}
              onClick={() => navigate(`/displays/${display.id}`)}
            >
              <CardContent>
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'start',
                    mb: 1,
                  }}
                >
                  <Typography variant="h6">{display.name}</Typography>
                  {getStatusIcon(display.status)}
                </Box>
                <Chip
                  label={display.status}
                  color={getStatusColor(display.status) as any}
                  size="small"
                  sx={{ mb: 1 }}
                />
                <Typography variant="body2" color="text.secondary">
                  MAC: {display.mac_address}
                </Typography>
                {display.floor && (
                  <Typography variant="body2" color="text.secondary">
                    PiÄ™tro: {display.floor}
                  </Typography>
                )}
                {display.last_seen && (
                  <Typography variant="body2" color="text.secondary">
                    Ostatnio: {new Date(display.last_seen).toLocaleString('pl-PL')}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {displays.length === 0 && (
        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Typography variant="h6" color="text.secondary">
            Brak wyĹ›wietlaczy
          </Typography>
        </Box>
      )}
    </Box>
  )
}

export default StatusPage




