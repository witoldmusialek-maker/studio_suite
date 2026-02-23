import { useEffect, useState } from 'react'
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Button,
  Chip,
} from '@mui/material'
import { api } from '../services/api'
import { Alert } from '../types'
import { useAuth } from '../contexts/AuthContext'

const AlertsPage = () => {
  const { user } = useAuth()
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAlerts()
  }, [])

  const fetchAlerts = async () => {
    try {
      const response = await api.get('/alerts')
      setAlerts(response.data || [])
    } catch (error) {
      console.error('Błąd pobierania alertów:', error)
    } finally {
      setLoading(false)
    }
  }

  const resolveAlert = async (id: number) => {
    try {
      await api.put(`/alerts/${id}/resolve`)
      fetchAlerts()
    } catch (error) {
      console.error('Błąd rozwiązania alertu:', error)
    }
  }

  if (loading) {
    return <Typography>Ładowanie...</Typography>
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Alerty
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Display ID</TableCell>
              <TableCell>Typ</TableCell>
              <TableCell>Severity</TableCell>
              <TableCell>Wiadomość</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Akcja</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {alerts.map((alert) => (
              <TableRow key={alert.id}>
                <TableCell>{alert.id}</TableCell>
                <TableCell>{alert.display_id}</TableCell>
                <TableCell>{alert.alert_type}</TableCell>
                <TableCell>{alert.severity}</TableCell>
                <TableCell>{alert.message}</TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={alert.resolved ? 'Rozwiązany' : 'Aktywny'}
                    color={alert.resolved ? 'success' : 'warning'}
                  />
                </TableCell>
                <TableCell>
                  {user?.role === 'admin' && !alert.resolved && (
                    <Button size="small" variant="outlined" onClick={() => resolveAlert(alert.id)}>
                      Oznacz jako rozwiązany
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}

export default AlertsPage
