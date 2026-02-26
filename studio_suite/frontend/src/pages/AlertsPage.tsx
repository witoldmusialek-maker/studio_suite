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
  product_name_pl?: string | null
  fiscal_code?: string | null
  brand?: string | null
  package_size_g?: number | null
  catalog_price?: number | null
  sale_price_gross?: number | null
  s_u: boolean
  doses_short: number
  doses_medium: number
  doses_long: number
  stock_100?: number | null
  is_active: boolean
}

type ProductForm = {
  product_code: string
  product_name: string
  product_name_pl: string
  fiscal_code: string
  brand: string
  package_size_g: string
  catalog_price: string
  sale_price_gross: string
  s_u: boolean
  doses_short: string
  doses_medium: string
  doses_long: string
  is_active: boolean
}

const emptyForm: ProductForm = {
  product_code: '',
  product_name: '',
  product_name_pl: '',
  fiscal_code: '',
  brand: '',
  package_size_g: '100',
  catalog_price: '',
  sale_price_gross: '',
  s_u: false,
  doses_short: '4',
  doses_medium: '2',
  doses_long: '1.25',
  is_active: true,
}

type ProductColumnFilters = {
  product_code: string
  product_name: string
  product_name_pl: string
  fiscal_code: string
  package_size_g: string
  catalog_price: string
  sale_price_gross: string
  stock_100: string
  s_u: 'all' | 'sale' | 'service'
  is_active: 'all' | 'true' | 'false'
}

const emptyFilters: ProductColumnFilters = {
  product_code: '',
  product_name: '',
  product_name_pl: '',
  fiscal_code: '',
  package_size_g: '',
  catalog_price: '',
  sale_price_gross: '',
  stock_100: '',
  s_u: 'all',
  is_active: 'all',
}

const stockLabelForSalon = (salon?: SalonRow): string => {
  if (!salon) return 'Stan 100%'
  const code = (salon.code || '').trim()
  const name = (salon.name || '').toLowerCase()
  if (code === '05' || name.includes('pulaw')) return 'Stan 100% (MX03)'
  if (code === '12' || name.includes('kras')) return 'Stan 100% (MX04)'
  if (code === '07' || name.includes('odyn')) return 'Stan 100% (MX07)'
  return 'Stan 100%'
}

const AlertsPage = () => {
  const [salons, setSalons] = useState<SalonRow[]>([])
  const [selectedSalonId, setSelectedSalonId] = useState<number | ''>('')
  const [rows, setRows] = useState<ProductRow[]>([])
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState<ProductColumnFilters>(emptyFilters)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')

  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<ProductRow | null>(null)
  const [form, setForm] = useState<ProductForm>(emptyForm)

  const selectedSalon = useMemo(
    () => salons.find((item) => item.id === selectedSalonId),
    [salons, selectedSalonId]
  )
  const stockLabel = stockLabelForSalon(selectedSalon)

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
    return rows.filter((row) => {
      const matchesGlobal =
        !q || `${row.product_code} ${row.product_name} ${row.product_name_pl || ''} ${row.fiscal_code || ''}`.toLowerCase().includes(q)
      const matchesCode = !filters.product_code.trim() || row.product_code.toLowerCase().includes(filters.product_code.trim().toLowerCase())
      const matchesName = !filters.product_name.trim() || row.product_name.toLowerCase().includes(filters.product_name.trim().toLowerCase())
      const matchesNamePl =
        !filters.product_name_pl.trim() || (row.product_name_pl || '').toLowerCase().includes(filters.product_name_pl.trim().toLowerCase())
      const matchesFisk =
        !filters.fiscal_code.trim() || (row.fiscal_code || '').toLowerCase().includes(filters.fiscal_code.trim().toLowerCase())
      const matchesPoj = !filters.package_size_g.trim() || String(row.package_size_g ?? '').includes(filters.package_size_g.trim())
      const matchesF = !filters.catalog_price.trim() || String(row.catalog_price ?? '').includes(filters.catalog_price.trim())
      const matchesBrutto =
        !filters.sale_price_gross.trim() || String(row.sale_price_gross ?? '').includes(filters.sale_price_gross.trim())
      const matchesStock100 = !filters.stock_100.trim() || String(row.stock_100 ?? '').includes(filters.stock_100.trim())
      const matchesSU =
        filters.s_u === 'all' ||
        (filters.s_u === 'sale' && row.s_u) ||
        (filters.s_u === 'service' && !row.s_u)
      const matchesActive =
        filters.is_active === 'all' ||
        (filters.is_active === 'true' && row.is_active) ||
        (filters.is_active === 'false' && !row.is_active)
      return (
        matchesGlobal &&
        matchesCode &&
        matchesName &&
        matchesNamePl &&
        matchesFisk &&
        matchesPoj &&
        matchesF &&
        matchesBrutto &&
        matchesStock100 &&
        matchesSU &&
        matchesActive
      )
    })
  }, [rows, query, filters])

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
      product_name_pl: row.product_name_pl || '',
      fiscal_code: row.fiscal_code || '',
      brand: row.brand || '',
      package_size_g: String(row.package_size_g ?? 100),
      catalog_price: row.catalog_price == null ? '' : String(row.catalog_price),
      sale_price_gross: row.sale_price_gross == null ? '' : String(row.sale_price_gross),
      s_u: !!row.s_u,
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
        product_name_pl: form.product_name_pl.trim() || null,
        fiscal_code: form.fiscal_code.trim() || null,
        brand: form.brand.trim() || null,
        package_size_g: Number(form.package_size_g),
        catalog_price: form.catalog_price.trim() === '' ? null : Number(form.catalog_price),
        sale_price_gross: form.sale_price_gross.trim() === '' ? null : Number(form.sale_price_gross),
        s_u: form.s_u,
        doses_short: Number(form.doses_short),
        doses_medium: Number(form.doses_medium),
        doses_long: Number(form.doses_long),
        is_active: form.is_active,
      }
      if (editing) {
        await api.patch(`/resources/products/${editing.salon_product_id}`, {
          product_name: payload.product_name,
          product_name_pl: payload.product_name_pl,
          fiscal_code: payload.fiscal_code,
          brand: payload.brand,
          package_size_g: payload.package_size_g,
          catalog_price: payload.catalog_price,
          sale_price_gross: payload.sale_price_gross,
          s_u: payload.s_u,
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
          label='Szukaj produktu'
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
              <TableCell>ID_P</TableCell>
              <TableCell>NAZWA1</TableCell>
              <TableCell>NAZWAPL</TableCell>
              <TableCell>FISK</TableCell>
              <TableCell align='right'>POJ</TableCell>
              <TableCell align='right'>F</TableCell>
              <TableCell align='right'>CENASPBRT</TableCell>
              <TableCell align='right'>{stockLabel}</TableCell>
              <TableCell align='center'>S_U</TableCell>
              <TableCell align='center'>Aktywny</TableCell>
              <TableCell align='right'>Akcje</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>
                <TextField size='small' value={filters.product_code} onChange={(e) => setFilters((prev) => ({ ...prev, product_code: e.target.value }))} placeholder='Filtr' />
              </TableCell>
              <TableCell>
                <TextField size='small' value={filters.product_name} onChange={(e) => setFilters((prev) => ({ ...prev, product_name: e.target.value }))} placeholder='Filtr' />
              </TableCell>
              <TableCell>
                <TextField size='small' value={filters.product_name_pl} onChange={(e) => setFilters((prev) => ({ ...prev, product_name_pl: e.target.value }))} placeholder='Filtr' />
              </TableCell>
              <TableCell>
                <TextField size='small' value={filters.fiscal_code} onChange={(e) => setFilters((prev) => ({ ...prev, fiscal_code: e.target.value }))} placeholder='Filtr' />
              </TableCell>
              <TableCell>
                <TextField size='small' value={filters.package_size_g} onChange={(e) => setFilters((prev) => ({ ...prev, package_size_g: e.target.value }))} placeholder='Filtr' />
              </TableCell>
              <TableCell>
                <TextField size='small' value={filters.catalog_price} onChange={(e) => setFilters((prev) => ({ ...prev, catalog_price: e.target.value }))} placeholder='Filtr' />
              </TableCell>
              <TableCell>
                <TextField size='small' value={filters.sale_price_gross} onChange={(e) => setFilters((prev) => ({ ...prev, sale_price_gross: e.target.value }))} placeholder='Filtr' />
              </TableCell>
              <TableCell>
                <TextField size='small' value={filters.stock_100} onChange={(e) => setFilters((prev) => ({ ...prev, stock_100: e.target.value }))} placeholder='Filtr' />
              </TableCell>
              <TableCell>
                <Select
                  size='small'
                  value={filters.s_u}
                  onChange={(e) => setFilters((prev) => ({ ...prev, s_u: e.target.value as ProductColumnFilters['s_u'] }))}
                >
                  <MenuItem value='all'>Wszystkie</MenuItem>
                  <MenuItem value='sale'>Sprzedaz</MenuItem>
                  <MenuItem value='service'>Usluga</MenuItem>
                </Select>
              </TableCell>
              <TableCell>
                <Select
                  size='small'
                  value={filters.is_active}
                  onChange={(e) => setFilters((prev) => ({ ...prev, is_active: e.target.value as ProductColumnFilters['is_active'] }))}
                >
                  <MenuItem value='all'>Wszystkie</MenuItem>
                  <MenuItem value='true'>TAK</MenuItem>
                  <MenuItem value='false'>NIE</MenuItem>
                </Select>
              </TableCell>
              <TableCell align='right'>
                <Button size='small' onClick={() => setFilters(emptyFilters)}>Reset</Button>
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filtered.map((row) => (
              <TableRow key={row.salon_product_id}>
                <TableCell>{row.product_code}</TableCell>
                <TableCell>{row.product_name}</TableCell>
                <TableCell>{row.product_name_pl || '-'}</TableCell>
                <TableCell>{row.fiscal_code || '-'}</TableCell>
                <TableCell align='right'>{row.package_size_g ?? '-'}</TableCell>
                <TableCell align='right'>{row.catalog_price ?? '-'}</TableCell>
                <TableCell align='right'>{row.sale_price_gross ?? '-'}</TableCell>
                <TableCell align='right'>{row.stock_100 ?? '-'}</TableCell>
                <TableCell align='center'>{row.s_u ? 'SPRZEDAZ' : 'USLUGA'}</TableCell>
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
                <TableCell colSpan={11}>Brak produktow.</TableCell>
              </TableRow>
            )}
            {loading && (
              <TableRow>
                <TableCell colSpan={11}>Ladowanie...</TableCell>
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
              label='ID_P'
              value={form.product_code}
              onChange={(e) => setForm((prev) => ({ ...prev, product_code: e.target.value }))}
              disabled={!!editing}
            />
            <TextField
              size='small'
              label='NAZWA1'
              value={form.product_name}
              onChange={(e) => setForm((prev) => ({ ...prev, product_name: e.target.value }))}
            />
            <TextField
              size='small'
              label='NAZWAPL'
              value={form.product_name_pl}
              onChange={(e) => setForm((prev) => ({ ...prev, product_name_pl: e.target.value }))}
            />
            <TextField
              size='small'
              label='FISK'
              value={form.fiscal_code}
              onChange={(e) => setForm((prev) => ({ ...prev, fiscal_code: e.target.value }))}
            />
            <TextField
              size='small'
              type='number'
              label='POJ'
              value={form.package_size_g}
              onChange={(e) => setForm((prev) => ({ ...prev, package_size_g: e.target.value }))}
              inputProps={{ min: 0, step: 0.01 }}
            />
            <TextField
              size='small'
              type='number'
              label='F (cena katalogowa)'
              value={form.catalog_price}
              onChange={(e) => setForm((prev) => ({ ...prev, catalog_price: e.target.value }))}
              inputProps={{ min: 0, step: 0.01 }}
            />
            <TextField
              size='small'
              type='number'
              label='CENASPBRT'
              value={form.sale_price_gross}
              onChange={(e) => setForm((prev) => ({ ...prev, sale_price_gross: e.target.value }))}
              inputProps={{ min: 0, step: 0.01 }}
            />
            <Stack direction='row' alignItems='center' spacing={1}>
              <Typography variant='body2'>S_U: Produkt do sprzedazy</Typography>
              <Switch
                checked={form.s_u}
                onChange={(_, checked) => setForm((prev) => ({ ...prev, s_u: checked }))}
              />
            </Stack>
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
            disabled={selectedSalonId === '' || form.product_code.trim().length === 0 || form.product_name.trim().length === 0}
          >
            Zapisz
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default AlertsPage
