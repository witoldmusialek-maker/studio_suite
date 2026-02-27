import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  FormControl,
  FormControlLabel,
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
import { Refresh } from '@mui/icons-material'
import { api } from '../services/api'

type SalonRow = { id: number; code: string; name: string; is_active: boolean }

type ProductRow = {
  product_id: number
  product_code: string
  product_name: string
  product_name_pl?: string | null
  fiscal_code?: string | null
  package_size_g?: number | null
  catalog_net_price?: number | null
  sale_price_gross?: number | null
  stock_100?: number | null
  warehouse?: string | null
  type_code?: string | null
  purchase_price?: number | null
  brand?: string | null
  note?: string | null
  salon_sale_price?: number | null
  family_code?: string | null
  is_locked: boolean
  s_u: boolean
  is_active: boolean
}

type EditableField =
  | 'product_name'
  | 'product_name_pl'
  | 'fiscal_code'
  | 'brand'
  | 'package_size_g'
  | 'catalog_net_price'
  | 'sale_price_gross'
  | 'salon_sale_price'
  | 'warehouse'
  | 'type_code'
  | 'purchase_price'
  | 'family_code'
  | 'note'

type ColumnDef = {
  key: keyof ProductRow
  label: string
  width?: number
  editable?: boolean
  numeric?: boolean
}

const formatValue = (value: unknown) => {
  if (value === null || value === undefined || value === '') return '-'
  if (typeof value === 'number') return Number(value.toFixed(2))
  if (typeof value === 'boolean') return value ? 'TAK' : 'NIE'
  return String(value)
}

const AlertsPage = () => {
  const [salons, setSalons] = useState<SalonRow[]>([])
  const [selectedSalonId, setSelectedSalonId] = useState<number | ''>('')
  const [rows, setRows] = useState<ProductRow[]>([])
  const [query, setQuery] = useState('')
  const [showArchived, setShowArchived] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')

  const [editingCell, setEditingCell] = useState<{ productId: number; field: EditableField } | null>(null)
  const [editingValue, setEditingValue] = useState('')
  const [savingCell, setSavingCell] = useState('')

  const selectedSalon = useMemo(
    () => salons.find((s) => s.id === selectedSalonId),
    [salons, selectedSalonId],
  )

  const stockLabel = useMemo(() => {
    if (!selectedSalon) return 'Stan 100%'
    const code = (selectedSalon.code || '').trim()
    const name = (selectedSalon.name || '').toLowerCase()
    if (code === '05' || name.includes('pulaw')) return 'Stan 100% (MX03)'
    if (code === '12' || name.includes('kras')) return 'Stan 100% (MX04)'
    if (code === '07' || name.includes('odyn')) return 'Stan 100% (MX07)'
    return 'Stan 100%'
  }, [selectedSalon])

  const columns = useMemo<ColumnDef[]>(
    () => [
      { key: 'product_code', label: 'Kod', width: 90 },
      { key: 'product_name', label: 'Nazwa', editable: true, width: 220 },
      { key: 'product_name_pl', label: 'Nazwa PL', editable: true, width: 220 },
      { key: 'brand', label: 'Marka', editable: true, width: 140 },
      { key: 'fiscal_code', label: 'FISK', editable: true, width: 90 },
      { key: 'package_size_g', label: 'Poj.', editable: true, numeric: true, width: 80 },
      { key: 'catalog_net_price', label: 'Cena kat. net', editable: true, numeric: true, width: 120 },
      { key: 'sale_price_gross', label: 'Cena sprz. brutto', editable: true, numeric: true, width: 130 },
      { key: 'salon_sale_price', label: 'Cena salon', editable: true, numeric: true, width: 110 },
      { key: 'purchase_price', label: 'Cena zak.', editable: true, numeric: true, width: 100 },
      { key: 'stock_100', label: stockLabel, width: 110 },
      { key: 'warehouse', label: 'Magazyn', editable: true, width: 110 },
      { key: 'type_code', label: 'Typ', editable: true, width: 100 },
      { key: 'family_code', label: 'Rodzina', editable: true, width: 110 },
      { key: 'note', label: 'Uwagi', editable: true, width: 220 },
      { key: 'is_locked', label: 'Zablokowany', width: 100 },
      { key: 's_u', label: 'S_U', width: 70 },
    ],
    [stockLabel],
  )

  const loadSalons = async () => {
    const res = await api.get<SalonRow[]>('/resources/salons')
    const list = res.data || []
    setSalons(list)
    if (selectedSalonId === '' && list.length) setSelectedSalonId(list[0].id)
  }

  const loadProducts = async (salonId: number) => {
    setLoading(true)
    setError('')
    setInfo('')
    try {
      const res = await api.get<ProductRow[]>('/resources/products', { params: { salon_id: salonId } })
      setRows((res.data || []).sort((a, b) => a.product_code.localeCompare(b.product_code)))
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
      if (!showArchived && !row.is_active) return false
      if (!q) return true
      return (
        `${row.product_code} ${row.product_name} ${row.product_name_pl || ''} ${row.brand || ''} ${row.fiscal_code || ''}`
          .toLowerCase()
          .includes(q)
      )
    })
  }, [rows, query, showArchived])

  const startEdit = (row: ProductRow, field: EditableField) => {
    setEditingCell({ productId: row.product_id, field })
    setEditingValue(String(row[field] ?? ''))
  }

  const cancelEdit = () => {
    setEditingCell(null)
    setEditingValue('')
  }

  const saveEdit = async (row: ProductRow, field: EditableField, numeric: boolean) => {
    const cellKey = `${row.product_id}:${field}`
    const raw = editingValue.trim()
    const payload: Record<string, unknown> = {}

    if (numeric) {
      if (raw === '') {
        payload[field] = null
      } else {
        const parsed = Number(raw.replace(',', '.'))
        if (!Number.isFinite(parsed) || parsed < 0) {
          setError('Niepoprawna wartosc numeryczna.')
          return
        }
        payload[field] = Number(parsed.toFixed(2))
      }
    } else {
      payload[field] = raw === '' ? null : raw
    }

    setSavingCell(cellKey)
    setError('')
    try {
      await api.patch(`/resources/products/${row.product_id}`, payload)
      setRows((prev) =>
        prev.map((item) => (item.product_id === row.product_id ? { ...item, ...payload } : item)),
      )
      setInfo('Zapisano zmiane.')
      cancelEdit()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac zmiany.')
    } finally {
      setSavingCell('')
    }
  }

  const toggleFlag = async (row: ProductRow, field: 'is_locked' | 's_u' | 'is_active') => {
    if (row.is_locked && field !== 'is_locked') {
      setError('Produkt jest zablokowany. Najpierw odblokuj, aby zmieniac pola.')
      return
    }
    const payload = { [field]: !row[field] }
    setError('')
    try {
      await api.patch(`/resources/products/${row.product_id}`, payload)
      setRows((prev) => prev.map((item) => (item.product_id === row.product_id ? { ...item, ...payload } : item)))
      setInfo('Zapisano zmiane.')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac zmiany.')
    }
  }

  return (
    <Box>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent='space-between' sx={{ mb: 2 }} spacing={1.5}>
        <Typography variant='h4'>Farby i kolory</Typography>
        <Button
          variant='outlined'
          startIcon={<Refresh />}
          onClick={() => selectedSalonId !== '' && loadProducts(selectedSalonId)}
        >
          Odswiez
        </Button>
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
          label='Szukaj'
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          sx={{ minWidth: 320 }}
        />
        <FormControlLabel
          control={<Switch checked={showArchived} onChange={(_, checked) => setShowArchived(checked)} />}
          label='Pokaz archiwalne'
        />
      </Stack>

      {error && <Alert severity='error' sx={{ mb: 2 }}>{error}</Alert>}
      {info && <Alert severity='success' sx={{ mb: 2 }}>{info}</Alert>}

      <Typography variant='body2' color='text.secondary' sx={{ mb: 1 }}>
        Podwojne klikniecie w komorke edytowalna otwiera edycje inline. Enter zapisuje, Esc anuluje.
      </Typography>
      <Typography variant='caption' color='text.secondary' sx={{ display: 'block', mb: 1.5 }}>
        Zablokowany = blokada zmian produktu (ceny, nazwy, pola techniczne, status archiwum). Odblokowanie odblokowuje edycje.
      </Typography>

      <TableContainer component={Paper} sx={{ maxHeight: '72vh' }}>
        <Table size='small' stickyHeader>
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableCell key={String(col.key)} sx={{ minWidth: col.width }}>
                  {col.label}
                </TableCell>
              ))}
              <TableCell sx={{ minWidth: 120 }}>Archiwum</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filtered.map((row) => (
              <TableRow
                key={row.product_id}
                hover
                sx={{ opacity: row.is_active ? 1 : 0.55 }}
              >
                {columns.map((col) => {
                  const field = col.key as EditableField
                  const isEditing = editingCell?.productId === row.product_id && editingCell?.field === field
                  const cellKey = `${row.product_id}:${field}`
                  if (col.key === 'is_locked' || col.key === 's_u') {
                    const toggleField: 'is_locked' | 's_u' = col.key
                    const disabled = row.is_locked && toggleField !== 'is_locked'
                    return (
                      <TableCell key={String(col.key)}>
                        <Switch
                          size='small'
                          checked={Boolean(row[col.key])}
                          disabled={disabled}
                          onChange={() => toggleFlag(row, toggleField)}
                        />
                      </TableCell>
                    )
                  }
                  if (col.editable && isEditing) {
                    return (
                      <TableCell key={String(col.key)}>
                        <TextField
                          size='small'
                          autoFocus
                          value={editingValue}
                          disabled={savingCell === cellKey}
                          onChange={(e) => setEditingValue(e.target.value)}
                          onBlur={() => saveEdit(row, field, Boolean(col.numeric))}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault()
                              void saveEdit(row, field, Boolean(col.numeric))
                            }
                            if (e.key === 'Escape') {
                              e.preventDefault()
                              cancelEdit()
                            }
                          }}
                        />
                      </TableCell>
                    )
                  }
                  return (
                    <TableCell
                      key={String(col.key)}
                      onDoubleClick={() => col.editable && !row.is_locked && startEdit(row, field)}
                      sx={{ cursor: col.editable && !row.is_locked ? 'text' : 'default' }}
                    >
                      {formatValue(row[col.key])}
                    </TableCell>
                  )
                })}
                <TableCell>
                  <Button
                    size='small'
                    variant='text'
                    color={row.is_active ? 'warning' : 'success'}
                    disabled={row.is_locked}
                    onClick={() => toggleFlag(row, 'is_active')}
                  >
                    {row.is_active ? 'Archiwizuj' : 'Przywroc'}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {!filtered.length && !loading && (
              <TableRow>
                <TableCell colSpan={columns.length + 1}>Brak produktow.</TableCell>
              </TableRow>
            )}
            {loading && (
              <TableRow>
                <TableCell colSpan={columns.length + 1}>Ladowanie...</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}

export default AlertsPage
