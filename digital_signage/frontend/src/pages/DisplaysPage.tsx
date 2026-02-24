import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardMedia,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  InputAdornment,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Image as ImageIcon,
  Movie as MovieIcon,
  PictureAsPdf as PdfIcon,
  Search as SearchIcon,
  TableChart as TableChartIcon,
  Tv as TvIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material'
import { api } from '../services/api'
import { Display } from '../types'
import { useAuth } from '../contexts/AuthContext'

type StatusFilter = 'all' | 'online' | 'offline' | 'error'

type DisplayCurrentContent = {
  id: number
  name: string
  type: 'image' | 'video' | 'pdf' | 'excel' | string
  file_path?: string
  thumbnail?: string
}

type DisplayContentResponse = {
  content: DisplayCurrentContent | null
}

const PREVIEW_HEIGHT = 170

const DisplaysPage = () => {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [displays, setDisplays] = useState<Display[]>([])
  const [loading, setLoading] = useState(true)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingDisplay, setEditingDisplay] = useState<Display | null>(null)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [currentContentByDisplay, setCurrentContentByDisplay] = useState<Record<number, DisplayCurrentContent | null>>({})
  const [formData, setFormData] = useState({
    name: '',
    mac_address: '',
    orientation: 0,
    resolution_width: 1920,
    resolution_height: 1080,
    floor: '',
    cache_size_mb: 1000,
  })

  useEffect(() => {
    fetchDisplays()
  }, [])

  const fetchDisplays = async () => {
    try {
      const response = await api.get('/displays')
      const list: Display[] = response.data || []
      setDisplays(list)
      await fetchCurrentContents(list)
    } catch (fetchError) {
      console.error('Display fetch failed:', fetchError)
    } finally {
      setLoading(false)
    }
  }

  const fetchCurrentContents = async (list: Display[]) => {
    if (list.length === 0) {
      setCurrentContentByDisplay({})
      return
    }

    const entries = await Promise.all(
      list.map(async (display) => {
        try {
          const res = await api.get<DisplayContentResponse>(`/displays/${display.id}/test-content`)
          return [display.id, res.data?.content || null] as const
        } catch {
          return [display.id, null] as const
        }
      })
    )

    setCurrentContentByDisplay(Object.fromEntries(entries))
  }

  const handleOpenDialog = (display?: Display) => {
    if (display) {
      setEditingDisplay(display)
      setFormData({
        name: display.name,
        mac_address: display.mac_address,
        orientation: display.orientation,
        resolution_width: display.resolution_width,
        resolution_height: display.resolution_height,
        floor: display.floor || '',
        cache_size_mb: display.cache_size_mb,
      })
    } else {
      setEditingDisplay(null)
      setFormData({
        name: '',
        mac_address: '',
        orientation: 0,
        resolution_width: 1920,
        resolution_height: 1080,
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
    } catch (submitError: any) {
      setError(submitError.response?.data?.detail || 'Nie udało się zapisać wyświetlacza.')
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Usunąć ten wyświetlacz?')) return

    try {
      await api.delete(`/displays/${id}`)
      fetchDisplays()
    } catch (deleteError) {
      console.error('Delete failed:', deleteError)
    }
  }

  const getStatusColor = (status: string): 'success' | 'error' | 'warning' | 'default' => {
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

  const getStatusLabel = (status: Display['status']) => {
    const labels: Record<Display['status'], string> = {
      online: 'Online',
      offline: 'Offline',
      error: 'Błąd',
    }
    return labels[status] || status
  }

  const getTypeLabel = (type?: string) => {
    const labels: Record<string, string> = {
      image: 'Obraz',
      video: 'Wideo',
      pdf: 'PDF',
      excel: 'Excel',
    }
    return labels[type || ''] || (type || '-')
  }

  const getTypeIcon = (type?: string) => {
    switch (type) {
      case 'image':
        return <ImageIcon sx={{ fontSize: 44 }} />
      case 'video':
        return <MovieIcon sx={{ fontSize: 44 }} />
      case 'pdf':
        return <PdfIcon sx={{ fontSize: 44 }} />
      case 'excel':
        return <TableChartIcon sx={{ fontSize: 44 }} />
      default:
        return <TvIcon sx={{ fontSize: 44 }} />
    }
  }

  const mediaUrl = (path?: string) => {
    if (!path) return ''
    if (path.startsWith('http://') || path.startsWith('https://')) return path
    return `${window.location.origin}${path}`
  }

  const filteredDisplays = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()

    return displays.filter((display) => {
      const matchesSearch =
        normalizedSearch.length === 0 ||
        display.name.toLowerCase().includes(normalizedSearch) ||
        display.mac_address.toLowerCase().includes(normalizedSearch) ||
        (display.floor || '').toLowerCase().includes(normalizedSearch)

      const matchesStatus = statusFilter === 'all' || display.status === statusFilter

      return matchesSearch && matchesStatus
    })
  }, [displays, search, statusFilter])

  const stats = useMemo(() => {
    const online = displays.filter((d) => d.status === 'online').length
    const offline = displays.filter((d) => d.status === 'offline').length
    const errorCount = displays.filter((d) => d.status === 'error').length

    return {
      total: displays.length,
      online,
      offline,
      errorCount,
    }
  }, [displays])

  if (loading) {
    return <Typography>Ładowanie...</Typography>
  }

  return (
    <Box>
      <Paper
        sx={{
          mb: 2.5,
          p: 2.5,
          borderRadius: 3,
          background: 'linear-gradient(145deg, #f5f8ff 0%, #ffffff 62%)',
        }}
      >
        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2} sx={{ mb: 1.5 }}>
          <Box>
            <Typography variant="h4">Wyświetlacze</Typography>
            <Typography color="text.secondary">Podgląd statusu urządzeń i aktualnie emitowanej treści</Typography>
          </Box>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button
              variant="outlined"
              component="a"
              href="/download/windows_display_client_v1.0.0-beta.2026-02-24.15.exe?v=2026-02-24.15"
              download="windows_display_client_v1.0.0-beta.2026-02-24.15.exe"
            >
              Pobierz klienta wideo (EXE)
            </Button>
            <Button
              variant="outlined"
              component="a"
              href="/download/android_display_client_v1.0.0-beta.2026-02-24.12.apk?v=2026-02-24.14"
              download="android_display_client_v1.0.0-beta.2026-02-24.12.apk"
            >
              Pobierz Android APK
            </Button>
            <Button
              variant="outlined"
              component="a"
              href="/download/android_tv_client_v1.0.0-beta.2026-02-24.12.apk?v=2026-02-24.14"
              download="android_tv_client_v1.0.0-beta.2026-02-24.12.apk"
            >
              Pobierz Android TV APK
            </Button>
            {user?.role === 'admin' && (
              <Button variant="contained" startIcon={<AddIcon />} size="large" onClick={() => handleOpenDialog()}>
                Dodaj wyświetlacz
              </Button>
            )}
          </Stack>
        </Stack>

        <Grid container spacing={1.5} sx={{ mb: 1.5 }}>
          <Grid item xs={6} md={3}><Card variant="outlined"><CardContent><Typography variant="body2" color="text.secondary">Wszystkie</Typography><Typography variant="h5">{stats.total}</Typography></CardContent></Card></Grid>
          <Grid item xs={6} md={3}><Card variant="outlined"><CardContent><Typography variant="body2" color="text.secondary">Online</Typography><Typography variant="h5" color="success.main">{stats.online}</Typography></CardContent></Card></Grid>
          <Grid item xs={6} md={3}><Card variant="outlined"><CardContent><Typography variant="body2" color="text.secondary">Offline</Typography><Typography variant="h5" color="error.main">{stats.offline}</Typography></CardContent></Card></Grid>
          <Grid item xs={6} md={3}><Card variant="outlined"><CardContent><Typography variant="body2" color="text.secondary">Błędy</Typography><Typography variant="h5" color="warning.main">{stats.errorCount}</Typography></CardContent></Card></Grid>
        </Grid>

        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
          <TextField
            fullWidth
            size="small"
            placeholder="Szukaj po nazwie, MAC, piętrze..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          />
          <TextField
            select
            size="small"
            label="Status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
            sx={{ minWidth: 190 }}
          >
            <MenuItem value="all">Wszystkie</MenuItem>
            <MenuItem value="online">Online</MenuItem>
            <MenuItem value="offline">Offline</MenuItem>
            <MenuItem value="error">Błąd</MenuItem>
          </TextField>
        </Stack>
      </Paper>

      <Grid container spacing={2}>
        {filteredDisplays.map((display) => {
          const current = currentContentByDisplay[display.id] || null
          const previewImage = mediaUrl(current?.thumbnail)

          return (
            <Grid item xs={12} md={6} lg={4} key={display.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: 3,
                  border: '1px solid',
                  borderColor: 'divider',
                  transition: 'transform 160ms ease, box-shadow 160ms ease',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 4,
                  },
                }}
              >
                <Box
                  sx={{
                    height: PREVIEW_HEIGHT,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    bgcolor: '#f4f6fa',
                    overflow: 'hidden',
                  }}
                >
                  {previewImage ? (
                    <CardMedia
                      component="img"
                      image={previewImage}
                      alt={current?.name || 'Podgląd treści'}
                      sx={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  ) : (
                    <Stack alignItems="center" spacing={1} sx={{ color: 'text.secondary' }}>
                      {getTypeIcon(current?.type)}
                      <Typography variant="caption">{current ? 'Brak miniatury' : 'Brak treści testowej'}</Typography>
                    </Stack>
                  )}
                </Box>

                <CardContent sx={{ flexGrow: 1, pb: 1 }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                    <Typography variant="h6" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {display.name}
                    </Typography>
                    <Chip size="small" color={getStatusColor(display.status)} label={getStatusLabel(display.status)} />
                  </Stack>

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                    MAC: {display.mac_address}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                    Piętro: {display.floor || '-'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Ostatnio widziany: {display.last_seen ? new Date(display.last_seen).toLocaleString('pl-PL') : '-'}
                  </Typography>

                  <Paper variant="outlined" sx={{ p: 1.2, borderRadius: 2 }}>
                    <Typography variant="caption" color="text.secondary">Aktualna treść</Typography>
                    <Typography
                      variant="body2"
                      sx={{
                        fontWeight: 600,
                        lineHeight: 1.35,
                        display: '-webkit-box',
                        overflow: 'hidden',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                      }}
                    >
                      {current?.name || 'Brak treści testowej'}
                    </Typography>
                    {current && (
                      <Chip size="small" sx={{ mt: 0.75 }} label={getTypeLabel(current.type)} />
                    )}
                  </Paper>
                </CardContent>

                <Box sx={{ px: 2, pb: 1.5, pt: 0.5, display: 'flex', justifyContent: 'space-between' }}>
                  <Tooltip title="Szczegóły">
                    <IconButton size="small" onClick={() => navigate(`/displays/${display.id}`)}>
                      <ViewIcon />
                    </IconButton>
                  </Tooltip>

                  {user?.role === 'admin' && (
                    <Box>
                      <Tooltip title="Edytuj">
                        <IconButton size="small" onClick={() => handleOpenDialog(display)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Usuń">
                        <IconButton size="small" onClick={() => handleDelete(display.id)} color="error">
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  )}
                </Box>
              </Card>
            </Grid>
          )
        })}
      </Grid>

      {filteredDisplays.length === 0 && (
        <Paper sx={{ textAlign: 'center', mt: 3, p: 4, borderRadius: 3 }}>
          <Typography variant="h6" color="text.secondary">Brak wyświetlaczy dla wybranych filtrów</Typography>
        </Paper>
      )}

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{editingDisplay ? 'Edytuj wyświetlacz' : 'Dodaj wyświetlacz'}</DialogTitle>
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
            label="Adres MAC"
            value={formData.mac_address}
            onChange={(e) => setFormData({ ...formData, mac_address: e.target.value })}
            margin="normal"
            required
            disabled={!!editingDisplay}
          />
          <TextField
            fullWidth
            select
            label="Orientacja"
            value={formData.orientation}
            onChange={(e) => setFormData({ ...formData, orientation: Number(e.target.value) })}
            margin="normal"
          >
            <MenuItem value={0}>0°</MenuItem>
            <MenuItem value={90}>90°</MenuItem>
            <MenuItem value={180}>180°</MenuItem>
            <MenuItem value={270}>270°</MenuItem>
          </TextField>
          <TextField
            fullWidth
            type="number"
            label="Szerokość rozdzielczości"
            value={formData.resolution_width}
            onChange={(e) => setFormData({ ...formData, resolution_width: Number(e.target.value) })}
            margin="normal"
          />
          <TextField
            fullWidth
            type="number"
            label="Wysokość rozdzielczości"
            value={formData.resolution_height}
            onChange={(e) => setFormData({ ...formData, resolution_height: Number(e.target.value) })}
            margin="normal"
          />
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
            label="Cache (MB)"
            value={formData.cache_size_mb}
            onChange={(e) => setFormData({ ...formData, cache_size_mb: Number(e.target.value) })}
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
