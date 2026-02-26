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
import { Add, Delete, Edit, Refresh } from '@mui/icons-material'
import { api } from '../services/api'

type SalonRow = { id: number; code: string; name: string; is_active: boolean }

type ProductRow = {
  salon_product_id: number
  salon_id: number
  product_id: number
  product_code: string
  product_name: string
  brand?: string | null
  package_size_g?: number | null
  doses_short: number
  doses_medium: number
  doses_long: number
  is_active: boolean
}

type ProductForm = {
  product_code: string
  product_name: string
  brand: string
  package_size_g: string
  doses_short: string
  doses_medium: string
  doses_long: string
  is_active: boolean
}

const emptyForm: ProductForm = {
  product_code: '',
  product_name: '',
  brand: '',
  package_size_g: '100',
  doses_short: '4',
  doses_medium: '2',
  doses_long: '1.25',
  is_active: true,
}

const AlertsPage = () => {
  const [salons, setSalons] = useState<SalonRow[]>([])
  const [selectedSalonId, setSelectedSalonId] = useState<number | ''>('')
  const [rows, setRows] = useState<ProductRow[]>([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')

  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<ProductRow | null>(null)
  const [form, setForm] = useState<ProductForm>(emptyForm)

  const loadSalons = async () => {
    const res = await api.get<SalonRow[]>('/resources/salons')
    const list = res.data || []
    setSalons(list)
    if (selectedSalonId === '' && list.length) {
      setSelectedSalonId(list[0].id)
    }
  }

  const loadProducts = async (salonId: number) => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get<ProductRow[]>('/resources/products', { params: { salon_id: salonId } })
      const data = (res.data || []).sort((a, b) => a.product_code.localeCompare(b.product_code))
      setRows(data)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac bazy produktow.')
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
    loadProducts(selectedSalonId)
  }, [selectedSalonId])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return rows
    return rows.filter((row) => (`${row.product_code} ${row.product_name} ${row.brand || ''}`).toLowerCase().includes(q))
  }, [rows, query])

  const openCreate = () => {
    setEditing(null)
    setForm(emptyForm)
    setOpen(true)
  }

  const openEdit = (row: ProductRow) => {
    setEditing(row)
    setForm({
      product_code: row.product_code,
      product_name: row.product_name,
      brand: row.brand || '',
      package_size_g: String(row.package_size_g ?? 100),
      doses_short: String(row.doses_short),
      doses_medium: String(row.doses_medium),
      doses_long: String(row.doses_long),
      is_active: row.is_active,
    })
    setOpen(true)
  }

  const save = async () => {
    if (selectedSalonId === '') return
    setError('')
    setInfo('')
    try {
      const payload = {
        salon_id: selectedSalonId,
        product_code: form.product_code.trim(),
        product_name: form.product_name.trim(),
        brand: form.brand.trim() || null,
        package_size_g: Number(form.package_size_g),
        doses_short: Number(form.doses_short),
        doses_medium: Number(form.doses_medium),
        doses_long: Number(form.doses_long),
        is_active: form.is_active,
      }
      if (editing) {
        await api.patch(`/resources/products/${editing.salon_product_id}`, {
          product_name: payload.product_name,
          brand: payload.brand,
          package_size_g: payload.package_size_g,
          doses_short: payload.doses_short,
          doses_medium: payload.doses_medium,
          doses_long: payload.doses_long,
          is_active: payload.is_active,
        })
        setInfo('Produkt zaktualizowany.')
      } else {
        await api.post('/resources/products', payload)
        setInfo('Produkt dodany.')
      }
      setOpen(false)
      await loadProducts(selectedSalonId)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac produktu.')
    }
  }

  const remove = async (row: ProductRow) => {
    if (selectedSalonId === '') return
    if (!window.confirm(`Wylaczyc produkt ${row.product_code} - ${row.product_name}?`)) return
    setError('')
    setInfo('')
    try {
      await api.delete(`/resources/products/${row.salon_product_id}`)
      setInfo('Produkt wylaczony.')
      await loadProducts(selectedSalonId)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie usunac produktu.')
    }
  }

  return (
    <Box>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent='space-between' sx={{ mb: 2 }} spacing={1.5}>
        <Typography variant='h4'>Farby i kolory</Typography>
        <Stack direction='row' spacing={1}>
          <Button variant='outlined' startIcon={<Refresh />} onClick={() => selectedSalonId !== '' && loadProducts(selectedSalonId)}>
            Odswiez
          </Button>
          <Button variant='contained' startIcon={<Add />} onClick={openCreate} disabled={selectedSalonId === ''}>
            Dodaj produkt
          </Button>
        </Stack>
      </Stack>

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} sx={{ mb: 2 }}>
        <FormControl size='small' sx={{ minWidth: 280 }}>
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
          label='Szukaj produktu (kod / nazwa / marka)'
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          sx={{ minWidth: 340 }}
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
              <TableCell>Marka</TableCell>
              <TableCell align='right'>Opak. (g)</TableCell>
              <TableCell align='right'>Dawki krotkie</TableCell>
              <TableCell align='right'>Dawki srednie</TableCell>
              <TableCell align='right'>Dawki dlugie</TableCell>
              <TableCell align='center'>Aktywny</TableCell>
              <TableCell align='right'>Akcje</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filtered.map((row) => (
              <TableRow key={row.salon_product_id}>
                <TableCell>{row.product_code}</TableCell>
                <TableCell>{row.product_name}</TableCell>
                <TableCell>{row.brand || '-'}</TableCell>
                <TableCell align='right'>{row.package_size_g ?? '-'}</TableCell>
                <TableCell align='right'>{row.doses_short}</TableCell>
                <TableCell align='right'>{row.doses_medium}</TableCell>
                <TableCell align='right'>{row.doses_long}</TableCell>
                <TableCell align='center'>{row.is_active ? 'TAK' : 'NIE'}</TableCell>
                <TableCell align='right'>
                  <IconButton size='small' onClick={() => openEdit(row)}>
                    <Edit fontSize='small' />
                  </IconButton>
                  <IconButton size='small' color='error' onClick={() => remove(row)}>
                    <Delete fontSize='small' />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {!filtered.length && !loading && (
              <TableRow>
                <TableCell colSpan={9}>Brak produktow.</TableCell>
              </TableRow>
            )}
            {loading && (
              <TableRow>
                <TableCell colSpan={9}>Ladowanie...</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth='sm'>
        <DialogTitle>{editing ? 'Edycja produktu' : 'Nowy produkt'}</DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 0.5 }}>
            <TextField
              size='small'
              label='Kod produktu'
              value={form.product_code}
              onChange={(e) => setForm((prev) => ({ ...prev, product_code: e.target.value }))}
              disabled={!!editing}
            />
            <TextField
              size='small'
              label='Nazwa produktu'
              value={form.product_name}
              onChange={(e) => setForm((prev) => ({ ...prev, product_name: e.target.value }))}
            />
            <TextField
              size='small'
              label='Marka'
              value={form.brand}
              onChange={(e) => setForm((prev) => ({ ...prev, brand: e.target.value }))}
            />
            <TextField
              size='small'
              type='number'
              label='Wielkosc opakowania (g)'
              value={form.package_size_g}
              onChange={(e) => setForm((prev) => ({ ...prev, package_size_g: e.target.value }))}
              inputProps={{ min: 0, step: 0.01 }}
            />
            <TextField
              size='small'
              type='number'
              label='Podzial dawki: krotkie'
              value={form.doses_short}
              onChange={(e) => setForm((prev) => ({ ...prev, doses_short: e.target.value }))}
              inputProps={{ min: 0.01, step: 0.01 }}
            />
            <TextField
              size='small'
              type='number'
              label='Podzial dawki: srednie'
              value={form.doses_medium}
              onChange={(e) => setForm((prev) => ({ ...prev, doses_medium: e.target.value }))}
              inputProps={{ min: 0.01, step: 0.01 }}
            />
            <TextField
              size='small'
              type='number'
              label='Podzial dawki: dlugie'
              value={form.doses_long}
              onChange={(e) => setForm((prev) => ({ ...prev, doses_long: e.target.value }))}
              inputProps={{ min: 0.01, step: 0.01 }}
            />
            <Stack direction='row' alignItems='center' spacing={1}>
              <Typography variant='body2'>Aktywny</Typography>
              <Switch
                checked={form.is_active}
                onChange={(_, checked) => setForm((prev) => ({ ...prev, is_active: checked }))}
              />
            </Stack>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Anuluj</Button>
          <Button
            variant='contained'
            onClick={save}
            disabled={
              selectedSalonId === '' ||
              form.product_code.trim().length === 0 ||
              form.product_name.trim().length === 0 ||
              Number(form.doses_short) <= 0 ||
              Number(form.doses_medium) <= 0 ||
              Number(form.doses_long) <= 0
            }
          >
            Zapisz
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default AlertsPage
