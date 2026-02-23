import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Search as SearchIcon,
} from '@mui/icons-material'
import { api } from '../services/api'
import { Content, Display, Group, Schedule } from '../types'
import { useAuth } from '../contexts/AuthContext'

type ScheduleFormData = {
  name: string
  content_id: string
  display_id: string
  group_id: string
  start_time: string
  end_time: string
  start_date: string
  end_date: string
  days_of_week: string
  priority: string
  display_duration_seconds: string
  active: boolean
}

const defaultFormData: ScheduleFormData = {
  name: '',
  content_id: '',
  display_id: '',
  group_id: '',
  start_time: '08:00',
  end_time: '15:00',
  start_date: '',
  end_date: '',
  days_of_week: '1,2,3,4,5',
  priority: '0',
  display_duration_seconds: '',
  active: true,
}

const dayLabels: Record<number, string> = {
  1: 'Pon',
  2: 'Wt',
  3: 'Śr',
  4: 'Czw',
  5: 'Pt',
  6: 'Sob',
  7: 'Niedz',
}

const toTimeWithSeconds = (value: string) => (value.length === 5 ? `${value}:00` : value)
const formatTimeForInput = (value: string) => (value ? value.slice(0, 5) : '')
const parseCsvNumbers = (value: string) =>
  value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => Number(item))
    .filter((item) => !Number.isNaN(item))

const formatDays = (days?: number[]) => {
  if (!days || days.length === 0) return 'Codziennie'
  return days.map((day) => dayLabels[day] || String(day)).join(', ')
}

const SchedulesPage = () => {
  const { user } = useAuth()
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [contents, setContents] = useState<Content[]>([])
  const [displays, setDisplays] = useState<Display[]>([])
  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(true)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingSchedule, setEditingSchedule] = useState<Schedule | null>(null)
  const [formData, setFormData] = useState<ScheduleFormData>(defaultFormData)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')

  useEffect(() => {
    fetchAll()
  }, [])

  const fetchAll = async () => {
    try {
      const [schedulesRes, contentRes, displayRes, groupRes] = await Promise.all([
        api.get('/schedules'),
        api.get('/content'),
        api.get('/displays'),
        api.get('/groups'),
      ])
      setSchedules(schedulesRes.data || [])
      setContents(contentRes.data.items || [])
      setDisplays(displayRes.data || [])
      setGroups(groupRes.data || [])
    } catch (fetchError) {
      console.error('Schedule data fetch failed:', fetchError)
    } finally {
      setLoading(false)
    }
  }

  const filteredSchedules = useMemo(() => {
    return schedules.filter((schedule) => {
      const normalizedSearch = search.trim().toLowerCase()
      const matchesSearch =
        !normalizedSearch ||
        schedule.name.toLowerCase().includes(normalizedSearch) ||
        String(schedule.content_id).includes(normalizedSearch) ||
        String(schedule.display_id || '').includes(normalizedSearch) ||
        String(schedule.group_id || '').includes(normalizedSearch)

      const matchesStatus =
        statusFilter === 'all' ||
        (statusFilter === 'active' && schedule.active) ||
        (statusFilter === 'inactive' && !schedule.active)

      return matchesSearch && matchesStatus
    })
  }, [schedules, search, statusFilter])

  const stats = useMemo(() => {
    const active = schedules.filter((schedule) => schedule.active).length
    const displayTargets = schedules.filter((schedule) => !!schedule.display_id).length
    const groupTargets = schedules.filter((schedule) => !!schedule.group_id).length
    return {
      total: schedules.length,
      active,
      inactive: schedules.length - active,
      displayTargets,
      groupTargets,
    }
  }, [schedules])

  const handleOpenCreate = () => {
    setEditingSchedule(null)
    setFormData(defaultFormData)
    setError('')
    setOpenDialog(true)
  }

  const handleOpenEdit = (schedule: Schedule) => {
    setEditingSchedule(schedule)
    setFormData({
      name: schedule.name,
      content_id: String(schedule.content_id),
      display_id: schedule.display_id ? String(schedule.display_id) : '',
      group_id: schedule.group_id ? String(schedule.group_id) : '',
      start_time: formatTimeForInput(schedule.start_time),
      end_time: formatTimeForInput(schedule.end_time),
      start_date: schedule.start_date || '',
      end_date: schedule.end_date || '',
      days_of_week: schedule.days_of_week?.join(',') || '',
      priority: String(schedule.priority),
      display_duration_seconds: schedule.display_duration_seconds
        ? String(schedule.display_duration_seconds)
        : '',
      active: schedule.active,
    })
    setError('')
    setOpenDialog(true)
  }

  const handleCloseDialog = () => {
    setOpenDialog(false)
    setEditingSchedule(null)
    setError('')
  }

  const handleSubmit = async () => {
    try {
      if (!formData.display_id && !formData.group_id) {
        setError('Wybierz display lub grupę docelową.')
        return
      }

      const payload: Record<string, unknown> = {
        name: formData.name.trim(),
        content_id: Number(formData.content_id),
        display_id: formData.display_id ? Number(formData.display_id) : null,
        group_id: formData.group_id ? Number(formData.group_id) : null,
        start_time: toTimeWithSeconds(formData.start_time),
        end_time: toTimeWithSeconds(formData.end_time),
        priority: Number(formData.priority || 0),
      }

      if (formData.start_date) payload.start_date = formData.start_date
      if (formData.end_date) payload.end_date = formData.end_date
      if (formData.days_of_week) payload.days_of_week = parseCsvNumbers(formData.days_of_week)
      if (formData.display_duration_seconds) {
        payload.display_duration_seconds = Number(formData.display_duration_seconds)
      }
      if (editingSchedule) payload.active = formData.active

      if (editingSchedule) {
        await api.put(`/schedules/${editingSchedule.id}`, payload)
      } else {
        await api.post('/schedules', payload)
      }

      handleCloseDialog()
      fetchAll()
    } catch (submitError: any) {
      setError(submitError.response?.data?.detail || 'Nie udało się zapisać harmonogramu')
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Usunąć harmonogram?')) return
    try {
      await api.delete(`/schedules/${id}`)
      fetchAll()
    } catch (deleteError) {
      console.error('Schedule delete failed:', deleteError)
    }
  }

  if (loading) {
    return <Typography>Ładowanie harmonogramów...</Typography>
  }

  return (
    <Box>
      <Paper
        sx={{
          mb: 2,
          p: 3,
          borderRadius: 3,
          background: 'linear-gradient(140deg, #f0f7ff 0%, #f8fbff 60%, #ffffff 100%)',
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h4">Harmonogramy treści</Typography>
            <Typography color="text.secondary">Zarządzaj emisją treści na wyświetlaczach i grupach</Typography>
          </Box>
          {user?.role === 'admin' && (
            <Button variant="contained" startIcon={<AddIcon />} onClick={handleOpenCreate}>
              Dodaj harmonogram
            </Button>
          )}
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="body2" color="text.secondary">Wszystkie</Typography>
                <Typography variant="h5">{stats.total}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="body2" color="text.secondary">Aktywne</Typography>
                <Typography variant="h5" color="success.main">{stats.active}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="body2" color="text.secondary">Na wyświetlacze</Typography>
                <Typography variant="h5">{stats.displayTargets}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="body2" color="text.secondary">Na grupy</Typography>
                <Typography variant="h5">{stats.groupTargets}</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 2, mb: 2, borderRadius: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <TextField
            fullWidth
            placeholder="Szukaj po nazwie, content, display, grupie..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
          <TextField
            select
            label="Status"
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(event.target.value as 'all' | 'active' | 'inactive')
            }
            sx={{ minWidth: 180 }}
          >
            <MenuItem value="all">Wszystkie</MenuItem>
            <MenuItem value="active">Aktywne</MenuItem>
            <MenuItem value="inactive">Nieaktywne</MenuItem>
          </TextField>
        </Stack>
      </Paper>

      <TableContainer component={Paper} sx={{ borderRadius: 2 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Nazwa</TableCell>
              <TableCell>Zakres czasu</TableCell>
              <TableCell>Dni</TableCell>
              <TableCell>Cel</TableCell>
              <TableCell>Priorytet</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Akcje</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredSchedules.map((schedule) => (
              <TableRow key={schedule.id} hover>
                <TableCell>
                  <Typography fontWeight={600}>{schedule.name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Content ID: {schedule.content_id}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography>{schedule.start_time.slice(0, 5)} - {schedule.end_time.slice(0, 5)}</Typography>
                  {(schedule.start_date || schedule.end_date) && (
                    <Typography variant="body2" color="text.secondary">
                      {schedule.start_date || '...'} do {schedule.end_date || '...'}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>{formatDays(schedule.days_of_week)}</TableCell>
                <TableCell>
                  {schedule.display_id ? (
                    <Chip size="small" label={`Display #${schedule.display_id}`} />
                  ) : (
                    <Chip size="small" color="secondary" label={`Grupa #${schedule.group_id}`} />
                  )}
                </TableCell>
                <TableCell>{schedule.priority}</TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={schedule.active ? 'Aktywny' : 'Nieaktywny'}
                    color={schedule.active ? 'success' : 'default'}
                  />
                </TableCell>
                <TableCell align="right">
                  {user?.role === 'admin' && (
                    <>
                      <IconButton size="small" onClick={() => handleOpenEdit(schedule)}>
                        <EditIcon />
                      </IconButton>
                      <IconButton size="small" color="error" onClick={() => handleDelete(schedule.id)}>
                        <DeleteIcon />
                      </IconButton>
                    </>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {filteredSchedules.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 5 }}>
                  <Typography variant="body1" color="text.secondary">
                    Brak harmonogramów spełniających filtry.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>{editingSchedule ? 'Edycja harmonogramu treści' : 'Nowy harmonogram treści'}</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <Grid container spacing={2} sx={{ mt: 0 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Nazwa"
                value={formData.name}
                onChange={(event) => setFormData({ ...formData, name: event.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Treść"
                value={formData.content_id}
                onChange={(event) => setFormData({ ...formData, content_id: event.target.value })}
              >
                {contents.map((content) => (
                  <MenuItem key={content.id} value={String(content.id)}>
                    {content.id} - {content.original_filename}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Display (opcjonalnie)"
                value={formData.display_id}
                onChange={(event) => setFormData({ ...formData, display_id: event.target.value })}
              >
                <MenuItem value="">-</MenuItem>
                {displays.map((display) => (
                  <MenuItem key={display.id} value={String(display.id)}>
                    {display.id} - {display.name}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Grupa (opcjonalnie)"
                value={formData.group_id}
                onChange={(event) => setFormData({ ...formData, group_id: event.target.value })}
              >
                <MenuItem value="">-</MenuItem>
                {groups.map((group) => (
                  <MenuItem key={group.id} value={String(group.id)}>
                    {group.id} - {group.name}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                type="time"
                label="Start"
                InputLabelProps={{ shrink: true }}
                value={formData.start_time}
                onChange={(event) => setFormData({ ...formData, start_time: event.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                type="time"
                label="Koniec"
                InputLabelProps={{ shrink: true }}
                value={formData.end_time}
                onChange={(event) => setFormData({ ...formData, end_time: event.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                type="number"
                label="Priorytet"
                value={formData.priority}
                onChange={(event) => setFormData({ ...formData, priority: event.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="date"
                label="Data start (opcjonalnie)"
                InputLabelProps={{ shrink: true }}
                value={formData.start_date}
                onChange={(event) => setFormData({ ...formData, start_date: event.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="date"
                label="Data koniec (opcjonalnie)"
                InputLabelProps={{ shrink: true }}
                value={formData.end_date}
                onChange={(event) => setFormData({ ...formData, end_date: event.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Dni tygodnia (np. 1,2,3,4,5)"
                value={formData.days_of_week}
                onChange={(event) => setFormData({ ...formData, days_of_week: event.target.value })}
                helperText="1=Pon ... 7=Niedz. Puste = codziennie."
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Czas wyświetlania (sekundy, opcjonalnie)"
                value={formData.display_duration_seconds}
                onChange={(event) =>
                  setFormData({ ...formData, display_duration_seconds: event.target.value })
                }
              />
            </Grid>
            {editingSchedule && (
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  select
                  label="Aktywny"
                  value={formData.active ? 'true' : 'false'}
                  onChange={(event) =>
                    setFormData({ ...formData, active: event.target.value === 'true' })
                  }
                >
                  <MenuItem value="true">Tak</MenuItem>
                  <MenuItem value="false">Nie</MenuItem>
                </TextField>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Anuluj</Button>
          <Button variant="contained" onClick={handleSubmit}>
            Zapisz
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default SchedulesPage
