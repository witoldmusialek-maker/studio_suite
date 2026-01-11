import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Alert,
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material'
import { api } from '../services/api'
import { Display } from '../types'
import { useAuth } from '../contexts/AuthContext'

const DisplaysPage = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [displays, setDisplays] = useState<Display[]>([])
  const [loading, setLoading] = useState(true)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingDisplay, setEditingDisplay] = useState<Display | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    mac_address: '',
    orientation: 0,
    floor: '',
    cache_size_mb: 1000,
  })
  const [error, setError] = useState('')

  useEffect(() => {
    fetchDisplays()
  }, [])

  const fetchDisplays = async () => {
    try {
      const response = await api.get('/displays')
      setDisplays(response.data)
    } catch (error) {
      console.error('Błąd pobierania wyświetlaczy:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleOpenDialog = (display?: Display) => {
    if (display) {
      setEditingDisplay(display)
      setFormData({
        name: display.name,
        mac_address: display.mac_address,
        orientation: display.orientation,
        floor: display.floor || '',
        cache_size_mb: display.cache_size_mb,
      })
    } else {
      setEditingDisplay(null)
      setFormData({
        name: '',
        mac_address: '',
        orientation: 0,
        floor: '',
        cache_size_mb: 1000,
      })
    }
    setOpenDialog(true)
    setError('')
  }

  const handleCloseDialog = () => {
    setOpenDialog(false)
    setEditingDisplay(null)
    setError('')
  }

  const handleSubmit = async () => {
    try {
      if (editingDisplay) {
        await api.put(`/displays/${editingDisplay.id}`, formData)
      } else {
        await api.post('/displays', formData)
      }
      handleCloseDialog()
      fetchDisplays()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Błąd zapisu')
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Czy na pewno chcesz usunąć ten wyświetlacz?')) {
      return
    }

    try {
      await api.delete(`/displays/${id}`)
      fetchDisplays()
    } catch (error) {
      console.error('Błąd usuwania:', error)
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

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Wyświetlacze</Typography>
        {user?.role === 'admin' && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Dodaj Wyświetlacz
          </Button>
        )}
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Nazwa</TableCell>
              <TableCell>MAC Address</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Piętro</TableCell>
              <TableCell>Orientacja</TableCell>
              <TableCell>Ostatnio widziany</TableCell>
              <TableCell align="right">Akcje</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {displays.map((display) => (
              <TableRow key={display.id}>
                <TableCell>{display.name}</TableCell>
                <TableCell>{display.mac_address}</TableCell>
                <TableCell>
                  <Chip
                    label={display.status}
                    color={getStatusColor(display.status) as any}
                    size="small"
                  />
                </TableCell>
                <TableCell>{display.floor || '-'}</TableCell>
                <TableCell>{display.orientation}°</TableCell>
                <TableCell>
                  {display.last_seen
                    ? new Date(display.last_seen).toLocaleString('pl-PL')
                    : '-'}
                </TableCell>
                <TableCell align="right">
                  <IconButton
                    size="small"
                    onClick={() => navigate(`/displays/${display.id}`)}
                  >
                    <ViewIcon />
                  </IconButton>
                  {user?.role === 'admin' && (
                    <>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(display)}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(display.id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingDisplay ? 'Edytuj Wyświetlacz' : 'Dodaj Wyświetlacz'}
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <TextField
            fullWidth
            label="Nazwa"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="MAC Address"
            value={formData.mac_address}
            onChange={(e) =>
              setFormData({ ...formData, mac_address: e.target.value })
            }
            margin="normal"
            required
            disabled={!!editingDisplay}
          />
          <TextField
            fullWidth
            select
            label="Orientacja"
            value={formData.orientation}
            onChange={(e) =>
              setFormData({ ...formData, orientation: Number(e.target.value) })
            }
            margin="normal"
          >
            <MenuItem value={0}>0°</MenuItem>
            <MenuItem value={90}>90°</MenuItem>
            <MenuItem value={180}>180°</MenuItem>
            <MenuItem value={270}>270°</MenuItem>
          </TextField>
          <TextField
            fullWidth
            label="Piętro"
            value={formData.floor}
            onChange={(e) => setFormData({ ...formData, floor: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            type="number"
            label="Rozmiar cache (MB)"
            value={formData.cache_size_mb}
            onChange={(e) =>
              setFormData({ ...formData, cache_size_mb: Number(e.target.value) })
            }
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Anuluj</Button>
          <Button onClick={handleSubmit} variant="contained">
            Zapisz
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default DisplaysPage



