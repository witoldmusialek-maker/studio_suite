import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
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
  unit_count?: number | null
  warehouse?: string | null
  type_code?: string | null
  purchase_price?: number | null
  brand?: string | null
  weight?: number | null
  package_weight?: number | null
  min_unit?: number | null
  note?: string | null
  ean?: string | null
  salon_sale_price?: number | null
  purchase_price_c?: number | null
  family_code?: string | null
  is_locked: boolean
  upsize_ts?: string | null
  catalog_price?: number | null
  s_u: boolean
  is_active: boolean
}

type ColumnDef = { key: keyof ProductRow; label: string }

const AlertsPage = () => {
  const [salons, setSalons] = useState<SalonRow[]>([])
  const [selectedSalonId, setSelectedSalonId] = useState<number | ''>('')
  const [rows, setRows] = useState<ProductRow[]>([])
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const selectedSalon = useMemo(
    () => salons.find((s) => s.id === selectedSalonId),
    [salons, selectedSalonId]
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
      { key: 'product_code', label: 'ID_P' },
      { key: 'product_name', label: 'NAZWA1' },
      { key: 'product_name_pl', label: 'NAZWAPL' },
      { key: 'fiscal_code', label: 'FISK' },
      { key: 'package_size_g', label: 'POJ' },
      { key: 'catalog_net_price', label: 'CENAKATNET' },
      { key: 'sale_price_gross', label: 'CENASPBRT' },
      { key: 'stock_100', label: stockLabel },
      { key: 'unit_count', label: 'IL_JEDN' },
      { key: 'warehouse', label: 'MAGAZYN' },
      { key: 'type_code', label: 'CECHA_RODZINA' },
      { key: 'purchase_price', label: 'CENA_ZAK' },
      { key: 'brand', label: 'GRUPA' },
      { key: 'weight', label: 'WAGA' },
      { key: 'package_weight', label: 'WAGA_OP' },
      { key: 'min_unit', label: 'MIN_JEDN' },
      { key: 'note', label: 'REM' },
      { key: 'ean', label: 'EAN' },
      { key: 'salon_sale_price', label: 'cena_sp_salon' },
      { key: 'purchase_price_c', label: 'cena_zak_c' },
      { key: 'family_code', label: 'rodzina2' },
      { key: 'is_locked', label: 'ISlocked' },
      { key: 'upsize_ts', label: 'upsize_ts' },
      { key: 'catalog_price', label: 'cena_sp_f' },
      { key: 's_u', label: 'S_U' },
      { key: 'is_active', label: 'Aktywny' },
    ],
    [stockLabel]
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
      const globalOk =
        !q ||
        `${row.product_code} ${row.product_name} ${row.product_name_pl || ''} ${row.fiscal_code || ''}`.toLowerCase().includes(q)
      if (!globalOk) return false
      return columns.every((col) => {
        const token = (filters[col.key as string] || '').trim().toLowerCase()
        if (!token) return true
        const raw = row[col.key]
        const normalized =
          typeof raw === 'boolean' ? (raw ? '1 true tak' : '0 false nie') : String(raw ?? '').toLowerCase()
        return normalized.includes(token)
      })
    })
  }, [rows, query, filters, columns])

  return (
    <Box>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent='space-between' sx={{ mb: 2 }} spacing={1.5}>
        <Typography variant='h4'>Farby i kolory</Typography>
        <Button variant='outlined' startIcon={<Refresh />} onClick={() => selectedSalonId !== '' && loadProducts(selectedSalonId)}>
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
        <TextField size='small' label='Szukaj' value={query} onChange={(e) => setQuery(e.target.value)} sx={{ minWidth: 320 }} />
      </Stack>

      {error && <Alert severity='error' sx={{ mb: 2 }}>{error}</Alert>}

      <TableContainer component={Paper}>
        <Table size='small'>
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableCell key={col.key as string}>{col.label}</TableCell>
              ))}
            </TableRow>
            <TableRow>
              {columns.map((col) => (
                <TableCell key={`filter-${String(col.key)}`}>
                  <TextField
                    size='small'
                    value={filters[String(col.key)] || ''}
                    onChange={(e) => setFilters((prev) => ({ ...prev, [String(col.key)]: e.target.value }))}
                    placeholder='Filtr'
                  />
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {filtered.map((row) => (
              <TableRow key={row.product_id}>
                {columns.map((col) => {
                  const raw = row[col.key]
                  const value = typeof raw === 'boolean' ? (raw ? 'TAK' : 'NIE') : (raw ?? '-')
                  return <TableCell key={`${row.product_id}-${String(col.key)}`}>{value}</TableCell>
                })}
              </TableRow>
            ))}
            {!filtered.length && !loading && (
              <TableRow>
                <TableCell colSpan={columns.length}>Brak produktow.</TableCell>
              </TableRow>
            )}
            {loading && (
              <TableRow>
                <TableCell colSpan={columns.length}>Ladowanie...</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}

export default AlertsPage
