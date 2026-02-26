import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { Delete, Edit, Refresh } from '@mui/icons-material'
import { api } from '../services/api'

type ServiceRow = {
  service_id: number
  service_code: string
  service_name: string
  salon_id: number
  price: number
  duration_minutes: number
  is_active: boolean
}

type CatalogResponse = {
  service_prices: ServiceRow[]
}

type SalonRow = { id: number; code: string; name: string; is_active: boolean }

type ServiceForm = {
  service_code: string
  service_name: string
  duration_minutes: string
  default_price: string
  is_active: boolean
}

const emptyCreateForm: ServiceForm = {
  service_code: '',
  service_name: '',
  duration_minutes: '0',
  default_price: '0',
  is_active: true,
}

const ServicesPage = () => {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [query, setQuery] = useState('')
  const [services, setServices] = useState<ServiceRow[]>([])
  const [salons, setSalons] = useState<SalonRow[]>([])
  const [selectedSalonId, setSelectedSalonId] = useState<number | ''>('')

  const [createOpen, setCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState<ServiceForm>(emptyCreateForm)

  const [editOpen, setEditOpen] = useState(false)
  const [editServiceId, setEditServiceId] = useState<number | null>(null)
  const [editForm, setEditForm] = useState<ServiceForm>(emptyCreateForm)

  const loadSalons = async () => {
    const res = await api.get<SalonRow[]>('/resources/salons')
    const rows = res.data || []
    setSalons(rows)
    if (selectedSalonId === '' && rows.length) {
      setSelectedSalonId(rows[0].id)
    }
  }

  const loadCatalog = async (salonId: number) => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get<CatalogResponse>('/legacy/catalog', { params: { salon_id: salonId } })
      const rows = [...(res.data?.service_prices || [])].sort((a, b) => a.service_code.localeCompare(b.service_code))
      setServices(rows)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac cennika uslug.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    ;(async () => {
      await loadSalons()
    })()
  }, [])

  useEffect(() => {
    if (selectedSalonId === '') return
    loadCatalog(selectedSalonId)
  }, [selectedSalonId])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return services
    return services.filter((row) => {
      return row.service_code.toLowerCase().includes(q) || row.service_name.toLowerCase().includes(q)
    })
  }, [services, query])

  const openEdit = (row: ServiceRow) => {
    setEditServiceId(row.service_id)
    setEditForm({
      service_code: row.service_code,
      service_name: row.service_name,
      duration_minutes: String(row.duration_minutes),
      default_price: String(row.price),
      is_active: row.is_active,
    })
    setEditOpen(true)
  }

  const createService = async () => {
    if (selectedSalonId === '') return
    setError('')
    setInfo('')
    try {
      await api.post('/legacy/catalog/services', {
        service_code: createForm.service_code.trim(),
        service_name: createForm.service_name.trim(),
        duration_minutes: Number(createForm.duration_minutes),
        default_price: Number(createForm.default_price),
        salon_id: selectedSalonId,
      })
      setInfo('Usluga zostala dodana.')
      setCreateOpen(false)
      setCreateForm(emptyCreateForm)
      await loadCatalog(selectedSalonId)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie dodac uslugi.')
    }
  }

  const saveEdit = async () => {
    if (!editServiceId || selectedSalonId === '') return
    setError('')
    setInfo('')
    try {
      await api.patch('/legacy/catalog/services/' + editServiceId, {
        service_name: editForm.service_name.trim(),
        duration_minutes: Number(editForm.duration_minutes),
        default_price: Number(editForm.default_price),
        is_active: editForm.is_active,
      }, { params: { salon_id: selectedSalonId } })
      setInfo('Usluga zostala zaktualizowana.')
      setEditOpen(false)
      setEditServiceId(null)
      await loadCatalog(selectedSalonId)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac zmian.')
    }
  }

  const toggleActive = async (row: ServiceRow) => {
    if (selectedSalonId === '') return
    setError('')
    setInfo('')
    try {
      await api.patch('/legacy/catalog/services/' + row.service_id, {
        is_active: !row.is_active,
      }, { params: { salon_id: selectedSalonId } })
      setInfo('Status uslugi ' + row.service_code + ' zostal zmieniony.')
      await loadCatalog(selectedSalonId)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zmienic statusu uslugi.')
    }
  }

  const removeService = async (row: ServiceRow) => {
    if (selectedSalonId === '') return
    if (!window.confirm('Usunac usluge ' + row.service_code + ' - ' + row.service_name + '?')) return
    setError('')
    setInfo('')
    try {
      await api.delete('/legacy/catalog/services/' + row.service_id, { params: { salon_id: selectedSalonId } })
      setInfo('Usluga zostala usunieta z salonu.')
      await loadCatalog(selectedSalonId)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie usunac uslugi.')
    }
  }

  return (
    <Box>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent='space-between' spacing={1.5} sx={{ mb: 2 }}>
        <Typography variant='h4'>Cennik uslug</Typography>
        <Stack direction='row' spacing={1}>
          <Button variant='outlined' startIcon={<Refresh />} onClick={() => selectedSalonId !== '' && loadCatalog(selectedSalonId)}>Odswiez</Button>
          <Button variant='contained' onClick={() => setCreateOpen(true)} disabled={selectedSalonId === ''}>Dodaj usluge</Button>
        </Stack>
      </Stack>

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} sx={{ mb: 2 }}>
        <FormControl size='small' sx={{ minWidth: 260 }}>
          <InputLabel>Salon</InputLabel>
          <Select
            label='Salon'
            value={selectedSalonId}
            onChange={(e) => setSelectedSalonId(e.target.value === '' ? '' : Number(e.target.value))}
          >
            {salons.map((s) => (
              <MenuItem key={s.id} value={s.id}>{s.code} - {s.name}</MenuItem>
            ))}
          </Select>
        </FormControl>
        <TextField
          size='small'
          label='Szukaj po kodzie lub nazwie'
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          sx={{ minWidth: 320 }}
        />
      </Stack>

      {error && <Alert severity='error' sx={{ mb: 2 }}>{error}</Alert>}
      {info && <Alert severity='success' sx={{ mb: 2 }}>{info}</Alert>}

      <TableContainer component={Paper}>
        <Table size='small'>
          <TableHead>
            <TableRow>
              <TableCell>Kod</TableCell>
              <TableCell>Nazwa</TableCell>
              <TableCell align='right'>Czas (min)</TableCell>
              <TableCell align='right'>Cena</TableCell>
              <TableCell align='center'>Aktywna</TableCell>
              <TableCell align='right'>Akcje</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filtered.map((row) => (
              <TableRow key={row.service_id}>
                <TableCell>{row.service_code}</TableCell>
                <TableCell>{row.service_name}</TableCell>
                <TableCell align='right'>{row.duration_minutes}</TableCell>
                <TableCell align='right'>{row.price.toFixed(2)}</TableCell>
                <TableCell align='center'>
                  <Switch checked={row.is_active} onChange={() => toggleActive(row)} />
                </TableCell>
                <TableCell align='right'>
                  <IconButton size='small' onClick={() => openEdit(row)}>
                    <Edit fontSize='small' />
                  </IconButton>
                  <IconButton size='small' color='error' onClick={() => removeService(row)}>
                    <Delete fontSize='small' />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {!filtered.length && !loading && (
              <TableRow>
                <TableCell colSpan={6}>Brak danych.</TableCell>
              </TableRow>
            )}
            {loading && (
              <TableRow>
                <TableCell colSpan={6}>Ladowanie...</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} fullWidth maxWidth='sm'>
        <DialogTitle>Nowa usluga</DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 0.5 }}>
            <TextField
              size='small'
              label='Kod uslugi'
              value={createForm.service_code}
              onChange={(e) => setCreateForm((prev) => ({ ...prev, service_code: e.target.value }))}
            />
            <TextField
              size='small'
              label='Nazwa uslugi'
              value={createForm.service_name}
              onChange={(e) => setCreateForm((prev) => ({ ...prev, service_name: e.target.value }))}
            />
            <TextField
              size='small'
              type='number'
              label='Czas trwania (min)'
              value={createForm.duration_minutes}
              onChange={(e) => setCreateForm((prev) => ({ ...prev, duration_minutes: e.target.value }))}
            />
            <TextField
              size='small'
              type='number'
              label='Cena'
              value={createForm.default_price}
              onChange={(e) => setCreateForm((prev) => ({ ...prev, default_price: e.target.value }))}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Anuluj</Button>
          <Button
            variant='contained'
            onClick={createService}
            disabled={
              selectedSalonId === '' ||
              createForm.service_code.trim().length === 0 ||
              createForm.service_name.trim().length === 0 ||
              Number(createForm.duration_minutes) < 0 ||
              Number(createForm.default_price) < 0
            }
          >
            Zapisz
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={editOpen} onClose={() => setEditOpen(false)} fullWidth maxWidth='sm'>
        <DialogTitle>Edycja uslugi</DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 0.5 }}>
            <TextField size='small' label='Kod uslugi' value={editForm.service_code} disabled />
            <TextField
              size='small'
              label='Nazwa uslugi'
              value={editForm.service_name}
              onChange={(e) => setEditForm((prev) => ({ ...prev, service_name: e.target.value }))}
            />
            <TextField
              size='small'
              type='number'
              label='Czas trwania (min)'
              value={editForm.duration_minutes}
              onChange={(e) => setEditForm((prev) => ({ ...prev, duration_minutes: e.target.value }))}
            />
            <TextField
              size='small'
              type='number'
              label='Cena'
              value={editForm.default_price}
              onChange={(e) => setEditForm((prev) => ({ ...prev, default_price: e.target.value }))}
            />
            <Stack direction='row' alignItems='center' spacing={1}>
              <Typography variant='body2'>Aktywna</Typography>
              <Switch
                checked={editForm.is_active}
                onChange={(_, checked) => setEditForm((prev) => ({ ...prev, is_active: checked }))}
              />
            </Stack>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditOpen(false)}>Anuluj</Button>
          <Button
            variant='contained'
            onClick={saveEdit}
            disabled={
              editForm.service_name.trim().length === 0 ||
              Number(editForm.duration_minutes) < 0 ||
              Number(editForm.default_price) < 0
            }
          >
            Zapisz
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default ServicesPage
