import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Grid,
  Chip,
  Button,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert as MuiAlert,
  Snackbar,
} from '@mui/material'
import { ArrowBack as ArrowBackIcon, Send as SendIcon } from '@mui/icons-material'
import { api } from '../services/api'
import { Display, Alert, Content } from '../types'

const DisplayDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [display, setDisplay] = useState<Display | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [contents, setContents] = useState<Content[]>([])
  const [selectedContentId, setSelectedContentId] = useState<number | ''>('')
  const [sending, setSending] = useState(false)
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success'
  })

  useEffect(() => {
    if (id) {
      fetchDisplayData()
      fetchContents()
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

  const fetchContents = async () => {
    try {
      const res = await api.get('/content/')
      setContents(res.data.items || [])
    } catch (error) {
      console.error('Błąd pobierania treści:', error)
    }
  }

  const sendTestContent = async () => {
    if (!selectedContentId || !id) return
    setSending(true)
    try {
      await api.post(`/displays/${id}/test-content/${selectedContentId}`)
      setSnackbar({ open: true, message: 'Treść wysłana na wyświetlacz!', severity: 'success' })
    } catch (error) {
      console.error('Błąd wysyłania treści:', error)
      setSnackbar({ open: true, message: 'Błąd wysyłania treści', severity: 'error' })
    } finally {
      setSending(false)
    }
  }

  const clearTestContent = async () => {
    if (!id) return
    try {
      await api.delete(`/displays/${id}/test-content`)
      setSnackbar({ open: true, message: 'Treść testowa wyczyszczona', severity: 'success' })
    } catch (error) {
      console.error('Błąd czyszczenia treści:', error)
      setSnackbar({ open: true, message: 'Błąd czyszczenia treści', severity: 'error' })
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
        PowrĂłt
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
                    secondary={`${display.resolution_width}Ă—${display.resolution_height}`}
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

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Wyślij treść testową
              </Typography>
              <Typography color="text.secondary" sx={{ mb: 2 }}>
                Treść testowa zostanie natychmiast wyświetlona na tym wyświetlaczu, pomijając harmonogram.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                <FormControl sx={{ minWidth: 250 }}>
                  <InputLabel>Wybierz treść</InputLabel>
                  <Select
                    value={selectedContentId}
                    label="Wybierz treść"
                    onChange={(e) => setSelectedContentId(e.target.value as number)}
                  >
                    {contents.map((content) => (
                      <MenuItem key={content.id} value={content.id}>
                        {content.original_filename || content.filename} ({content.type})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <Button
                  variant="contained"
                  startIcon={<SendIcon />}
                  onClick={sendTestContent}
                  disabled={!selectedContentId || sending}
                >
                  {sending ? 'Wysyłanie...' : 'Wyślij'}
                </Button>
                <Button
                  variant="outlined"
                  color="warning"
                  onClick={clearTestContent}
                >
                  Wyczyść test
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <MuiAlert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </MuiAlert>
      </Snackbar>
    </Box>
  )
}

export default DisplayDetailPage





