import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
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
  is_formula: boolean
  formula_products: FormulaProductRow[]
}

type FormulaProductRow = {
  product_id: number
  product_code: string
  product_name: string
  brand?: string | null
}

type CatalogResponse = {
  service_prices: ServiceRow[]
}

type ProductCatalogRow = {
  salon_product_id: number
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
  const [products, setProducts] = useState<ProductCatalogRow[]>([])
  const [priceDraftByServiceId, setPriceDraftByServiceId] = useState<Record<number, string>>({})
  const [savingPriceByServiceId, setSavingPriceByServiceId] = useState<Record<number, boolean>>({})
  const [salons, setSalons] = useState<SalonRow[]>([])
  const [selectedSalonId, setSelectedSalonId] = useState<number | ''>('')

  const [createOpen, setCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState<ServiceForm>(emptyCreateForm)

  const [editOpen, setEditOpen] = useState(false)
  const [editServiceId, setEditServiceId] = useState<number | null>(null)
  const [editForm, setEditForm] = useState<ServiceForm>(emptyCreateForm)
  const [formulaOpen, setFormulaOpen] = useState(false)
  const [formulaService, setFormulaService] = useState<ServiceRow | null>(null)
  const [formulaSearch, setFormulaSearch] = useState('')
  const [formulaProductIds, setFormulaProductIds] = useState<number[]>([])

  const loadSalons = async () => {
    const res = await api.get<SalonRow[]>('/resources/salons')
    const rows = res.data || []
    setSalons(rows)
    if (selectedSalonId === '' && rows.length) {
      setSelectedSalonId(rows[0].id)
    }
  }

  const loadProducts = async () => {
    if (selectedSalonId === '') return
    try {
      const res = await api.get<ProductCatalogRow[]>('/legacy/catalog/products', { params: { salon_id: selectedSalonId } })
      setProducts(res.data || [])
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac bazy produktow.')
    }
  }

  const loadCatalog = async (salonId: number) => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get<CatalogResponse>('/legacy/catalog', { params: { salon_id: salonId } })
      const rows = [...(res.data?.service_prices || [])].sort((a, b) => a.service_code.localeCompare(b.service_code))
      setServices(rows)
      setPriceDraftByServiceId(
        rows.reduce<Record<number, string>>((acc, row) => {
          acc[row.service_id] = String(Number(row.price).toFixed(2))
          return acc
        }, {})
      )
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
    loadProducts()
  }, [selectedSalonId])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return services
    return services.filter((row) => {
      return row.service_code.toLowerCase().includes(q) || row.service_name.toLowerCase().includes(q)
    })
  }, [services, query])

  const filteredProducts = useMemo(() => {
    const q = formulaSearch.trim().toLowerCase()
    if (!q) return products
    return products.filter((row) => {
      const hay = `${row.product_code} ${row.product_name} ${row.brand || ''}`.toLowerCase()
      return hay.includes(q)
    })
  }, [products, formulaSearch])

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

  const toggleFormula = async (row: ServiceRow, checked: boolean) => {
    if (selectedSalonId === '') return
    setError('')
    try {
      const payload = {
        is_formula: checked,
        product_ids: checked ? row.formula_products.map((item) => item.product_id) : [],
      }
      const res = await api.patch(`/legacy/catalog/services/${row.service_id}/formula`, payload, {
        params: { salon_id: selectedSalonId },
      })
      const nextProducts = (res.data?.formula_products || []) as FormulaProductRow[]
      setServices((prev) =>
        prev.map((item) =>
          item.service_id === row.service_id
            ? { ...item, is_formula: checked, formula_products: nextProducts }
            : item
        )
      )
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zmienic statusu formuly.')
    }
  }

  const openFormulaDialog = (row: ServiceRow) => {
    setFormulaService(row)
    setFormulaProductIds(row.formula_products.map((item) => item.product_id))
    setFormulaSearch('')
    setFormulaOpen(true)
  }

  const saveFormula = async () => {
    if (selectedSalonId === '' || !formulaService) return
    setError('')
    try {
      const res = await api.patch(
        `/legacy/catalog/services/${formulaService.service_id}/formula`,
        { is_formula: true, product_ids: formulaProductIds },
        { params: { salon_id: selectedSalonId } }
      )
      const nextProducts = (res.data?.formula_products || []) as FormulaProductRow[]
      setServices((prev) =>
        prev.map((item) =>
          item.service_id === formulaService.service_id
            ? { ...item, is_formula: nextProducts.length > 0, formula_products: nextProducts }
            : item
        )
      )
      setFormulaOpen(false)
      setFormulaService(null)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac receptury.')
    }
  }

  const saveInlinePrice = async (row: ServiceRow) => {
    if (selectedSalonId === '') return
    const raw = (priceDraftByServiceId[row.service_id] ?? '').trim().replace(',', '.')
    if (raw === '') {
      setPriceDraftByServiceId((prev) => ({ ...prev, [row.service_id]: String(Number(row.price).toFixed(2)) }))
      return
    }
    const parsed = Number(raw)
    if (!Number.isFinite(parsed) || parsed < 0) {
      setError('Niepoprawna cena. Wpisz liczbe >= 0.')
      setPriceDraftByServiceId((prev) => ({ ...prev, [row.service_id]: String(Number(row.price).toFixed(2)) }))
      return
    }
    const normalized = Number(parsed.toFixed(2))
    if (Number(row.price.toFixed(2)) === normalized) return

    setSavingPriceByServiceId((prev) => ({ ...prev, [row.service_id]: true }))
    setError('')
    try {
      await api.patch(`/legacy/catalog/services/${row.service_id}/price`, { price: normalized }, { params: { salon_id: selectedSalonId } })
      setServices((prev) =>
        prev.map((item) => (item.service_id === row.service_id ? { ...item, price: normalized } : item))
      )
      setPriceDraftByServiceId((prev) => ({ ...prev, [row.service_id]: String(normalized.toFixed(2)) }))
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac ceny uslugi.')
      setPriceDraftByServiceId((prev) => ({ ...prev, [row.service_id]: String(Number(row.price).toFixed(2)) }))
    } finally {
      setSavingPriceByServiceId((prev) => ({ ...prev, [row.service_id]: false }))
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
              <TableCell align='center'>Formula</TableCell>
              <TableCell align='right'>Akcje</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filtered.map((row) => (
              <TableRow key={row.service_id}>
                <TableCell>{row.service_code}</TableCell>
                <TableCell>{row.service_name}</TableCell>
                <TableCell align='right'>{row.duration_minutes}</TableCell>
                <TableCell align='right' sx={{ minWidth: 170 }}>
                  <TextField
                    size='small'
                    type='number'
                    inputProps={{ step: 0.01, min: 0 }}
                    value={priceDraftByServiceId[row.service_id] ?? String(Number(row.price).toFixed(2))}
                    disabled={!!savingPriceByServiceId[row.service_id]}
                    onFocus={(event) => event.target.select()}
                    onChange={(event) =>
                      setPriceDraftByServiceId((prev) => ({ ...prev, [row.service_id]: event.target.value }))
                    }
                    onBlur={() => saveInlinePrice(row)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') {
                        event.preventDefault()
                        ;(event.target as HTMLInputElement).blur()
                      }
                    }}
                  />
                </TableCell>
                <TableCell align='center'>
                  <Stack direction='row' spacing={1} justifyContent='center' alignItems='center'>
                    <Switch checked={row.is_formula} onChange={(_, checked) => toggleFormula(row, checked)} />
                    <Button
                      size='small'
                      variant='outlined'
                      disabled={!row.is_formula}
                      onClick={() => openFormulaDialog(row)}
                    >
                      Receptura
                    </Button>
                  </Stack>
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

      <Dialog
        open={formulaOpen}
        onClose={() => {
          setFormulaOpen(false)
          setFormulaService(null)
        }}
        fullWidth
        maxWidth='md'
      >
        <DialogTitle>
          Receptura uslugi {formulaService ? `${formulaService.service_code} - ${formulaService.service_name}` : ''}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 0.5 }}>
            <TextField
              size='small'
              label='Szukaj produktu (kod / nazwa / marka)'
              value={formulaSearch}
              onChange={(e) => setFormulaSearch(e.target.value)}
            />
            <Paper variant='outlined' sx={{ maxHeight: 420, overflowY: 'auto' }}>
              <List dense>
                {filteredProducts.map((product) => {
                  const checked = formulaProductIds.includes(product.product_id)
                  return (
                    <ListItem key={product.product_id} disablePadding>
                      <ListItemButton
                        onClick={() =>
                          setFormulaProductIds((prev) =>
                            prev.includes(product.product_id)
                              ? prev.filter((id) => id !== product.product_id)
                              : [...prev, product.product_id]
                          )
                        }
                      >
                        <Checkbox edge='start' checked={checked} tabIndex={-1} disableRipple />
                          <ListItemText
                            primary={`${product.product_code} - ${product.product_name}`}
                            secondary={`${product.brand || ''}${product.brand ? ' | ' : ''}opak.: ${product.package_size_g ?? '-'}g | dawki S:${product.doses_short} M:${product.doses_medium} L:${product.doses_long}`}
                          />
                      </ListItemButton>
                    </ListItem>
                  )
                })}
                {!filteredProducts.length && (
                  <ListItem>
                    <ListItemText primary='Brak produktow.' />
                  </ListItem>
                )}
              </List>
            </Paper>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setFormulaOpen(false)
              setFormulaService(null)
            }}
          >
            Anuluj
          </Button>
          <Button variant='contained' onClick={saveFormula}>
            Zapisz recepture
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default ServicesPage
