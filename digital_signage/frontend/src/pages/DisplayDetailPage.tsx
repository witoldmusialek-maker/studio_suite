import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Paper,
  Grid,
  Chip,
  Button,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
} from '@mui/material'
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material'
import { api } from '../services/api'
import { Display, Alert } from '../types'

const DisplayDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [display, setDisplay] = useState<Display | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (id) {
      fetchDisplayData()
    }
  }, [id])

  const fetchDisplayData = async () => {
    try {
      const [displayRes, alertsRes] = await Promise.all([
        api.get(`/displays/${id}`),
        api.get(`/alerts?display_id=${id}&resolved=false`),
      ])
      setDisplay(displayRes.data)
      setAlerts(alertsRes.data)
    } catch (error) {
      console.error('Błąd pobierania danych:', error)
    } finally {
      setLoading(false)
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
    return <Typography>Ładowanie...</Typography>
  }

  if (!display) {
    return <Typography>Wyświetlacz nie znaleziony</Typography>
  }

  return (
    <Box>
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/displays')}
        sx={{ mb: 2 }}
      >
        Powrót
      </Button>

      <Typography variant="h4" gutterBottom>
        {display.name}
      </Typography>

      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Informacje
              </Typography>
              <List>
                <ListItem>
                  <ListItemText
                    primary="MAC Address"
                    secondary={display.mac_address}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="IP Address"
                    secondary={display.ip_address || '-'}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Status"
                    secondary={
                      <Chip
                        label={display.status}
                        color={getStatusColor(display.status) as any}
                        size="small"
                      />
                    }
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Piętro"
                    secondary={display.floor || '-'}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Orientacja"
                    secondary={`${display.orientation}°`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Rozdzielczość"
                    secondary={`${display.resolution_width}×${display.resolution_height}`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Cache"
                    secondary={`${display.cache_size_mb} MB`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Ostatnio widziany"
                    secondary={
                      display.last_seen
                        ? new Date(display.last_seen).toLocaleString('pl-PL')
                        : '-'
                    }
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Aktywne Alerty
              </Typography>
              {alerts.length === 0 ? (
                <Typography color="text.secondary">
                  Brak aktywnych alertów
                </Typography>
              ) : (
                <List>
                  {alerts.map((alert) => (
                    <ListItem key={alert.id}>
                      <ListItemText
                        primary={alert.message}
                        secondary={
                          <Chip
                            label={alert.severity}
                            color={
                              alert.severity === 'critical'
                                ? 'error'
                                : alert.severity === 'error'
                                ? 'warning'
                                : 'info'
                            }
                            size="small"
                          />
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default DisplayDetailPage



