import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
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
import { Edit, ExpandLess, ExpandMore, Refresh } from '@mui/icons-material'
import { api } from '../services/api'

type SalonRow = { id: number; code: string; name: string; is_active: boolean }

type ProductRow = {
  product_id: number
  product_code: string
  product_name: string
  product_name_pl?: string | null
  fiscal_code?: string | null
  package_size_g?: number | null
  unit_count?: number | null
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
  weight?: number | null
  package_weight?: number | null
  min_unit?: number | null
  is_locked: boolean
  s_u: boolean
  is_active: boolean
}

type ColumnDef = {
  key: keyof ProductRow | 'price_for_mode'
  label: string
  width?: number
  editable?: boolean
  numeric?: boolean
}

type FamilyOption = {
  value: string
  label: string
  product_count?: number
}
type TypeOption = { value: string; label: string }

const SALES_PATTERN = /SPRZEDA/i
const SERVICE_PATTERN = /USŁUGA|USLUGA/i

const formatValue = (value: unknown) => {
  if (value === null || value === undefined || value === '') return '-'
  if (typeof value === 'number') return Number(value.toFixed(2))
  if (typeof value === 'boolean') return value ? 'TAK' : 'NIE'
  return String(value)
}

const renderCellValue = (
  col: ColumnDef,
  row: ProductRow,
  classify: (item: ProductRow) => 'service' | 'sales' | 'other',
) => {
  if (col.key === 'price_for_mode') {
    const category = classify(row)
    if (category === 'service') return formatValue(row.purchase_price)
    if (category === 'sales') return formatValue(row.sale_price_gross)
    return formatValue(row.purchase_price ?? row.sale_price_gross ?? null)
  }
  return formatValue(row[col.key])
}

const columnCellSx = (col: ColumnDef) => {
  if (col.key === 'product_name') {
    return {
      minWidth: 420,
      width: '38%',
      maxWidth: 'none',
      whiteSpace: 'normal',
      wordBreak: 'break-word',
    }
  }
  if (col.key === 'brand') {
    return {
      minWidth: 280,
      width: '24%',
      maxWidth: 'none',
      whiteSpace: 'normal',
      wordBreak: 'break-word',
    }
  }
  if (typeof col.width === 'number') {
    return {
      width: col.width,
      minWidth: col.width,
      maxWidth: col.width,
    }
  }
  return {}
}

type CreateProductKind = 'service' | 'sales'

const AlertsPage = () => {
  const [salons, setSalons] = useState<SalonRow[]>([])
  const [selectedSalonId, setSelectedSalonId] = useState<number | ''>('')
  const [rows, setRows] = useState<ProductRow[]>([])
  const [query, setQuery] = useState('')
  const [showArchived, setShowArchived] = useState(false)
  const [showServiceProducts, setShowServiceProducts] = useState(true)
  const [showSalesProducts, setShowSalesProducts] = useState(false)
  const [showOtherProducts, setShowOtherProducts] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')

  const [familyOptions, setFamilyOptions] = useState<FamilyOption[]>([])
  const [typeOptions, setTypeOptions] = useState<TypeOption[]>([])
  const [editDialogRow, setEditDialogRow] = useState<ProductRow | null>(null)
  const [editDialogDraft, setEditDialogDraft] = useState<Partial<ProductRow>>({})
  const [createKind, setCreateKind] = useState<CreateProductKind>('service')
  const [savingDialog, setSavingDialog] = useState(false)
  const [collapsedFamilies, setCollapsedFamilies] = useState<Record<string, boolean>>({})

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

  const existingProductCodes = useMemo(
    () => new Set(rows.map((r) => (r.product_code || '').trim().toUpperCase()).filter(Boolean)),
    [rows],
  )

  const typedProductCode = ((editDialogDraft.product_code ?? '') as string).trim().toUpperCase()
  const codeAlreadyExists = useMemo(() => {
    if (editDialogRow) return false
    if (!typedProductCode) return false
    return existingProductCodes.has(typedProductCode)
  }, [editDialogRow, typedProductCode, existingProductCodes])

  const columns = useMemo<ColumnDef[]>(
    () => {
      const base: ColumnDef[] = [
        { key: 'product_name', label: 'Nazwa', width: 260 },
        { key: 'brand', label: 'Marka', width: 160 },
        { key: 'package_size_g', label: 'Poj.', numeric: true, width: 90 },
      ]
      const serviceOnly = showServiceProducts && !showSalesProducts && !showOtherProducts
      const salesOnly = showSalesProducts && !showServiceProducts && !showOtherProducts
      const mixedSalesService = showServiceProducts && showSalesProducts

      if (serviceOnly) {
        base.push({ key: 'purchase_price', label: 'Cena zak.', numeric: true, width: 120 })
      } else if (salesOnly) {
        base.push({ key: 'sale_price_gross', label: 'Cena sprz. brutto', numeric: true, width: 140 })
      } else if (mixedSalesService) {
        base.push({ key: 'price_for_mode', label: 'Cena', numeric: true, width: 130 })
      } else {
        base.push({ key: 'purchase_price', label: 'Cena zak.', numeric: true, width: 120 })
      }

      base.push({ key: 'stock_100', label: stockLabel, width: 130 })
      return base
    },
    [stockLabel, showServiceProducts, showSalesProducts, showOtherProducts],
  )

  const loadSalons = async () => {
    const res = await api.get<SalonRow[]>('/resources/salons')
    const list = (res.data || []).slice()
    const preferredCodeOrder: Record<string, number> = { '05': 0, '12': 1, '07': 2 }
    list.sort((a, b) => {
      const aCode = (a.code || '').trim()
      const bCode = (b.code || '').trim()
      const aPreferred = preferredCodeOrder[aCode]
      const bPreferred = preferredCodeOrder[bCode]
      const aRank = aPreferred === undefined ? 999 : aPreferred
      const bRank = bPreferred === undefined ? 999 : bPreferred
      if (aRank !== bRank) return aRank - bRank
      return a.name.localeCompare(b.name)
    })
    setSalons(list)
    if (selectedSalonId === '' && list.length) setSelectedSalonId(list[0].id)
  }

  const loadFamilyOptions = async () => {
    const res = await api.get<FamilyOption[]>('/colors/families', { params: { backbar: true } })
    setFamilyOptions(res.data || [])
  }

  const loadProducts = async (salonId: number) => {
    setLoading(true)
    setError('')
    setInfo('')
    try {
      const res = await api.get<ProductRow[]>('/resources/products', { params: { salon_id: salonId } })
      const list = (res.data || []).sort((a, b) => a.product_code.localeCompare(b.product_code))
      setRows(list)
      const typeSet = new Set(
        list
          .map((row) => (row.type_code || '').trim())
          .filter((v) => Boolean(v)),
      )
      setTypeOptions(Array.from(typeSet).sort((a, b) => a.localeCompare(b)).map((v) => ({ value: v, label: v })))
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac bazy produktow.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    ;(async () => {
      await loadSalons()
      await loadFamilyOptions()
    })()
  }, [])

  useEffect(() => {
    if (selectedSalonId === '') return
    loadProducts(selectedSalonId)
  }, [selectedSalonId])

  const classifyRow = (row: ProductRow) => {
    const family = (row.family_code || '').trim()
    const fiscal = (row.fiscal_code || '').trim()
    const haystack = `${family} ${row.product_name || ''} ${row.product_name_pl || ''} ${row.brand || ''} ${row.type_code || ''}`
    const isSales = Boolean(row.s_u) || Boolean(fiscal) || SALES_PATTERN.test(haystack)
    const isService = !isSales && (Boolean(family) || SERVICE_PATTERN.test(haystack))
    if (isSales) return 'sales' as const
    if (isService) return 'service' as const
    return 'other' as const
  }

  const categoryCounts = useMemo(() => {
    const counts = { service: 0, sales: 0, other: 0 }
    rows.forEach((row) => {
      const category = classifyRow(row)
      counts[category] += 1
    })
    return counts
  }, [rows])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return rows.filter((row) => {
      const category = classifyRow(row)
      if (!showArchived && !row.is_active) return false
      if (category === 'service' && !showServiceProducts) return false
      if (category === 'sales' && !showSalesProducts) return false
      if (category === 'other' && !showOtherProducts) return false
      if (!q) return true
      const family = ((row.family_code || '').trim() || 'Bez rodziny').toLowerCase()
      const name = (row.product_name || '').toLowerCase()
      const namePl = (row.product_name_pl || '').toLowerCase()
      return family.includes(q) || name.includes(q) || namePl.includes(q)
    })
  }, [rows, query, showArchived, showServiceProducts, showSalesProducts, showOtherProducts])

  const groupedRows = useMemo(() => {
    const mixedServiceSales = showServiceProducts && showSalesProducts
    const groups = new Map<string, { type: string; family: string; category: 'service' | 'sales' | 'other'; items: ProductRow[] }>()
    filtered.forEach((row) => {
      const type = (row.type_code || '').trim() || 'Bez typu'
      const family = (row.family_code || '').trim() || 'Bez rodziny'
      const category = classifyRow(row)
      const key = mixedServiceSales ? `${type}::${family}` : family
      const existing = groups.get(key)
      if (existing) {
        existing.items.push(row)
      } else {
        groups.set(key, { type, family, category, items: [row] })
      }
    })
    return Array.from(groups.values())
      .sort((a, b) => {
        if (mixedServiceSales) {
          const byType = a.type.localeCompare(b.type)
          if (byType !== 0) return byType
        }
        return a.family.localeCompare(b.family)
      })
      .map((group) => ({
        family: mixedServiceSales
          ? `${group.type} • ${group.family}`
          : group.family,
        items: group.items.sort((a, b) => a.product_name.localeCompare(b.product_name)),
      }))
  }, [filtered, showServiceProducts, showSalesProducts])

  const openEditDialog = (row: ProductRow) => {
    setEditDialogRow(row)
    setEditDialogDraft({
      product_code: row.product_code,
      product_name: row.product_name,
      product_name_pl: row.product_name_pl || '',
      brand: row.brand || '',
      fiscal_code: row.fiscal_code || '',
      family_code: row.family_code || '',
      package_size_g: row.package_size_g ?? null,
      unit_count: row.unit_count ?? null,
      weight: row.weight ?? null,
      package_weight: row.package_weight ?? null,
      min_unit: row.min_unit ?? null,
      catalog_net_price: row.catalog_net_price ?? null,
      sale_price_gross: row.sale_price_gross ?? null,
      salon_sale_price: row.salon_sale_price ?? null,
      purchase_price: row.purchase_price ?? null,
      stock_100: row.stock_100 ?? null,
      type_code: row.type_code || '',
      note: row.note || '',
      s_u: row.s_u,
      is_active: row.is_active,
    })
  }

  const openCreateDialog = (kind: CreateProductKind) => {
    setCreateKind(kind)
    setEditDialogRow(null)
    setEditDialogDraft({
      product_code: '',
      product_name: '',
      product_name_pl: '',
      brand: '',
      fiscal_code: '',
      family_code: '',
      package_size_g: null,
      unit_count: null,
      weight: null,
      package_weight: null,
      min_unit: null,
      catalog_net_price: null,
      sale_price_gross: null,
      salon_sale_price: null,
      purchase_price: null,
      stock_100: null,
      type_code: '',
      note: '',
      s_u: kind === 'sales',
      is_active: true,
    })
  }

  const closeEditDialog = () => {
    setEditDialogRow(null)
    setEditDialogDraft({})
    setSavingDialog(false)
  }

  const saveEditDialog = async () => {
    setSavingDialog(true)
    setError('')
    try {
      const payload = {
        product_code: (editDialogDraft.product_code ?? '').toString().trim(),
        product_name: (editDialogDraft.product_name ?? '').toString().trim() || null,
        product_name_pl: (editDialogDraft.product_name_pl ?? '').toString().trim() || null,
        brand: (editDialogDraft.brand ?? '').toString().trim() || null,
        fiscal_code: (editDialogDraft.fiscal_code ?? '').toString().trim() || null,
        family_code: (editDialogDraft.family_code ?? '').toString().trim() || null,
        salon_id: selectedSalonId === '' ? null : Number(selectedSalonId),
        package_size_g:
          editDialogDraft.package_size_g == null
            ? null
            : Number(editDialogDraft.package_size_g),
        unit_count:
          editDialogDraft.unit_count == null
            ? null
            : Number(editDialogDraft.unit_count),
        catalog_net_price:
          editDialogDraft.catalog_net_price == null
            ? null
            : Number(editDialogDraft.catalog_net_price),
        sale_price_gross:
          editDialogDraft.sale_price_gross == null
            ? null
            : Number(editDialogDraft.sale_price_gross),
        salon_sale_price:
          editDialogDraft.salon_sale_price == null
            ? null
            : Number(editDialogDraft.salon_sale_price),
        purchase_price:
          editDialogDraft.purchase_price == null
            ? null
            : Number(editDialogDraft.purchase_price),
        stock_100:
          editDialogDraft.stock_100 == null
            ? null
            : Number(editDialogDraft.stock_100),
        weight:
          editDialogDraft.weight == null
            ? null
            : Number(editDialogDraft.weight),
        package_weight:
          editDialogDraft.package_weight == null
            ? null
            : Number(editDialogDraft.package_weight),
        min_unit:
          editDialogDraft.min_unit == null
            ? null
            : Number(editDialogDraft.min_unit),
        type_code: (editDialogDraft.type_code ?? '').toString().trim() || null,
        note: (editDialogDraft.note ?? '').toString().trim() || null,
        s_u: editDialogRow ? Boolean(editDialogDraft.s_u) : createKind === 'sales',
        is_active: Boolean(editDialogDraft.is_active),
      }
      if (!payload.product_name) {
        setError('Nazwa produktu jest wymagana.')
        setSavingDialog(false)
        return
      }
      if (!editDialogRow && payload.product_code && existingProductCodes.has(payload.product_code.toUpperCase())) {
        setError('Kod produktu juz istnieje. Wpisz inny lub zostaw puste.')
        setSavingDialog(false)
        return
      }
      if (editDialogRow) {
        await api.patch(`/resources/products/${editDialogRow.product_id}`, payload)
        setRows((prev) =>
          prev.map((item) => (item.product_id === editDialogRow.product_id ? { ...item, ...payload } as ProductRow : item)),
        )
        setInfo('Zapisano zmiany produktu.')
      } else {
        if (createKind === 'sales' && !payload.fiscal_code) {
          setError('Dla produktu sprzedazowego wymagany jest kod FISK.')
          setSavingDialog(false)
          return
        }
        const res = await api.post<ProductRow>('/resources/products', payload)
        setRows((prev) => [...prev, res.data].sort((a, b) => a.product_code.localeCompare(b.product_code)))
        setInfo('Dodano nowy produkt.')
      }
      closeEditDialog()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac produktu.')
    } finally {
      setSavingDialog(false)
    }
  }

  const isSalesForm = Boolean(
    editDialogRow ? (editDialogDraft.s_u ?? editDialogRow.s_u) : createKind === 'sales',
  )
  const isServiceForm = !isSalesForm

  const netFromWeights = useMemo(() => {
    const full = Number(editDialogDraft.weight ?? 0)
    const empty = Number(editDialogDraft.package_weight ?? 0)
    if (full > 0 && empty >= 0 && full >= empty) return Number((full - empty).toFixed(4))
    return null
  }, [editDialogDraft.weight, editDialogDraft.package_weight])

  const doseWeight = useMemo(() => {
    const doses = Number(editDialogDraft.unit_count ?? 0)
    if (!netFromWeights || doses <= 0) return null
    return Number((netFromWeights / doses).toFixed(4))
  }, [netFromWeights, editDialogDraft.unit_count])

  return (
    <Box>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent='space-between' sx={{ mb: 2 }} spacing={1.5}>
        <Typography variant='h4'>Farby i kolory</Typography>
        <Stack direction='row' spacing={1}>
          <Button variant='contained' onClick={() => openCreateDialog('service')}>
            Nowy produkt - usluga
          </Button>
          <Button variant='outlined' onClick={() => openCreateDialog('sales')}>
            Nowy produkt - sprzedaz
          </Button>
          <Button
            variant='outlined'
            startIcon={<Refresh />}
            onClick={() => selectedSalonId !== '' && loadProducts(selectedSalonId)}
          >
            Odswiez
          </Button>
        </Stack>
      </Stack>

      <Paper variant='outlined' sx={{ p: 1.5, mb: 2 }}>
        <Stack direction={{ xs: 'column', lg: 'row' }} spacing={1.5} sx={{ mb: 1 }}>
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
            label='Szukaj rodziny lub produktu'
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            sx={{ minWidth: 280, flex: 1 }}
          />
          <FormControlLabel
            sx={{ ml: { xs: 0, lg: 1 } }}
            control={<Switch checked={showArchived} onChange={(_, checked) => setShowArchived(checked)} />}
            label='Pokaz archiwalne'
          />
        </Stack>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} sx={{ alignItems: { xs: 'flex-start', md: 'center' } }}>
          <FormControlLabel
            control={<Checkbox checked={showServiceProducts} onChange={(_, checked) => setShowServiceProducts(checked)} size='small' />}
            label={`Produkty do uslug (${categoryCounts.service})`}
          />
          <FormControlLabel
            control={<Checkbox checked={showSalesProducts} onChange={(_, checked) => setShowSalesProducts(checked)} size='small' />}
            label={`Produkty sprzedaz (${categoryCounts.sales})`}
          />
          <FormControlLabel
            control={<Checkbox checked={showOtherProducts} onChange={(_, checked) => setShowOtherProducts(checked)} size='small' />}
            label={`Pozostale (${categoryCounts.other})`}
          />
          <Button
            size='small'
            variant='text'
            onClick={() => {
              const next: Record<string, boolean> = {}
              groupedRows.forEach((group) => {
                next[group.family] = true
              })
              setCollapsedFamilies(next)
            }}
          >
            Zwin wszystkie
          </Button>
          <Button
            size='small'
            variant='text'
            onClick={() => {
              const next: Record<string, boolean> = {}
              groupedRows.forEach((group) => {
                next[group.family] = false
              })
              setCollapsedFamilies(next)
            }}
          >
            Rozwin wszystkie
          </Button>
        </Stack>
      </Paper>

      {error && <Alert severity='error' sx={{ mb: 2 }}>{error}</Alert>}
      {info && <Alert severity='success' sx={{ mb: 2 }}>{info}</Alert>}

      <Typography variant='body2' color='text.secondary' sx={{ mb: 1 }}>
        Domyslnie widok jest pogrupowany po rodzinach. Pole wyszukiwania filtruje rodziny. Kategorie produktow wlaczasz niezaleznymi checkboxami.
      </Typography>
      <Typography variant='caption' color='text.secondary' sx={{ display: 'block', mb: 1.5 }}>
        Rodziny sa pobierane bezposrednio z aktywnych produktow bez kodu fiskalnego. Pokaz archiwalne nadal filtruje rekordy, ale sama archiwizacja jest dostepna tylko w modalu edycji.
      </Typography>

      <Stack spacing={2}>
        {groupedRows.map((group) => (
          <Paper key={group.family} variant='outlined'>
            <Box sx={{ px: 2, py: 1.25, borderBottom: 1, borderColor: 'divider', backgroundColor: 'grey.50' }}>
              <Stack direction='row' justifyContent='space-between' alignItems='center' onClick={() => setCollapsedFamilies((prev) => ({ ...prev, [group.family]: !prev[group.family] }))} sx={{ cursor: 'pointer' }}>
                <Stack direction='row' spacing={1} alignItems='center'>
                  {collapsedFamilies[group.family] ? <ExpandMore fontSize='small' /> : <ExpandLess fontSize='small' />}
                  <Typography variant='subtitle1' sx={{ fontWeight: 700 }}>
                    {group.family}
                  </Typography>
                </Stack>
                <Typography variant='caption' color='text.secondary'>
                  {group.items.length} produktow
                </Typography>
              </Stack>
            </Box>
            {!collapsedFamilies[group.family] && (
              <TableContainer sx={{ maxHeight: '50vh' }}>
              <Table size='small' stickyHeader sx={{ tableLayout: 'auto', width: '100%' }}>
                <TableHead>
                  <TableRow>
                    {columns.map((col) => (
                      <TableCell key={String(col.key)} sx={columnCellSx(col)}>
                        {col.label}
                      </TableCell>
                    ))}
                    <TableCell sx={{ width: 110, minWidth: 110, maxWidth: 110, position: 'sticky', right: 0, zIndex: 3, backgroundColor: 'background.paper' }}>Edycja</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {group.items.map((row) => (
                    <TableRow
                      key={row.product_id}
                      hover
                      sx={{
                        opacity: row.is_active ? 1 : 0.55,
                        backgroundColor:
                          classifyRow(row) === 'sales'
                            ? 'rgba(255, 243, 224, 0.45)'
                            : classifyRow(row) === 'service'
                              ? 'rgba(232, 245, 233, 0.45)'
                              : 'rgba(227, 242, 253, 0.35)',
                      }}
                    >
                {columns.map((col) => (
                  <TableCell key={String(col.key)} sx={columnCellSx(col)}>
                    {renderCellValue(col, row, classifyRow)}
                  </TableCell>
                ))}
                <TableCell sx={{ position: 'sticky', right: 0, zIndex: 2, backgroundColor: 'background.paper' }}>
                  <Button size='small' variant='outlined' startIcon={<Edit fontSize='small' />} onClick={() => openEditDialog(row)}>
                    Edytuj
                  </Button>
                </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              </TableContainer>
            )}
          </Paper>
        ))}
        {!groupedRows.length && !loading && (
          <Paper variant='outlined' sx={{ p: 2 }}>
            <Typography>Brak produktow.</Typography>
          </Paper>
        )}
        {loading && (
          <Paper variant='outlined' sx={{ p: 2 }}>
            <Typography>Ladowanie...</Typography>
          </Paper>
        )}
      </Stack>

      <Dialog open={Boolean(editDialogRow) || Object.keys(editDialogDraft).length > 0} onClose={closeEditDialog} fullWidth maxWidth='md'>
        <DialogTitle>
          {editDialogRow
            ? `Edytuj produkt ${editDialogRow.product_code} - ${editDialogRow.product_name}`
            : createKind === 'sales'
              ? 'Nowy produkt - sprzedaz'
              : 'Nowy produkt - usluga'}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 0.5 }}>
            <TextField
              fullWidth
              size='small'
              label='Kod produktu'
              value={editDialogDraft.product_code ?? ''}
              onChange={(e) => setEditDialogDraft((prev) => ({ ...prev, product_code: e.target.value }))}
              disabled={Boolean(editDialogRow)}
              error={codeAlreadyExists}
              helperText={
                editDialogRow
                  ? 'Kod jest niezmienny dla istniejacego produktu.'
                  : codeAlreadyExists
                    ? 'Kod juz istnieje - wybierz inny albo zostaw puste.'
                    : 'Mozesz zostawic puste - system nada kolejny wolny kod.'
              }
            />
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
              <TextField
                fullWidth
                size='small'
                label='Nazwa'
                value={editDialogDraft.product_name ?? ''}
                onChange={(e) => setEditDialogDraft((prev) => ({ ...prev, product_name: e.target.value }))}
              />
              <TextField
                fullWidth
                size='small'
                label='Nazwa PL'
                value={editDialogDraft.product_name_pl ?? ''}
                onChange={(e) => setEditDialogDraft((prev) => ({ ...prev, product_name_pl: e.target.value }))}
              />
            </Stack>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
              <TextField
                fullWidth
                size='small'
                label='Marka'
                value={editDialogDraft.brand ?? ''}
                onChange={(e) => setEditDialogDraft((prev) => ({ ...prev, brand: e.target.value }))}
              />
              {isSalesForm && (
                <TextField
                  fullWidth
                  size='small'
                  label='FISK'
                  value={editDialogDraft.fiscal_code ?? ''}
                  onChange={(e) => setEditDialogDraft((prev) => ({ ...prev, fiscal_code: e.target.value }))}
                />
              )}
            </Stack>
            <Autocomplete
              fullWidth
              freeSolo
              options={familyOptions}
              value={familyOptions.find((option) => option.value === ((editDialogDraft.family_code as string) ?? '')) || ((editDialogDraft.family_code as string) ?? '')}
              inputValue={(editDialogDraft.family_code as string) ?? ''}
              onInputChange={(_, newInputValue) =>
                setEditDialogDraft((prev) => ({ ...prev, family_code: newInputValue || '' }))
              }
              onChange={(_, option) =>
                setEditDialogDraft((prev) => ({
                  ...prev,
                  family_code: typeof option === 'string' ? option : option?.value || '',
                }))
              }
              getOptionLabel={(option) => (typeof option === 'string' ? option : option.label)}
              isOptionEqualToValue={(option, value) =>
                option.value === (typeof value === 'string' ? value : value.value)
              }
              renderInput={(params) => (
                <TextField {...params} size='small' label='Rodzina' placeholder='Wyszukaj lub wybierz rodzine' />
              )}
            />
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
              <TextField
                size='small'
                type='number'
                label='Pojemnosc netto (ml/g)'
                value={editDialogDraft.package_size_g ?? ''}
                onChange={(e) => {
                  const nextQty = e.target.value === '' ? null : Number(e.target.value)
                  setEditDialogDraft((prev) => {
                    const next: Partial<ProductRow> = { ...prev, package_size_g: nextQty }
                    const doses = Number(prev.unit_count ?? 0)
                    const perDose = Number(prev.min_unit ?? 0)
                    if (isServiceForm && nextQty != null && nextQty > 0) {
                      if (doses > 0) next.min_unit = Number((nextQty / doses).toFixed(4))
                      else if (perDose > 0) next.unit_count = Number((nextQty / perDose).toFixed(4))
                    }
                    return next
                  })
                }}
                fullWidth
              />
              <TextField
                size='small'
                type='number'
                label={stockLabel}
                value={editDialogDraft.stock_100 ?? ''}
                onChange={(e) =>
                  setEditDialogDraft((prev) => ({
                    ...prev,
                    stock_100: e.target.value === '' ? null : Number(e.target.value),
                  }))
                }
                fullWidth
              />
            </Stack>
            {isServiceForm && (
              <>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
                  <TextField
                    size='small'
                    type='number'
                    label='Doz w opakowaniu'
                    value={editDialogDraft.unit_count ?? ''}
                    onChange={(e) => {
                      const nextDoses = e.target.value === '' ? null : Number(e.target.value)
                      setEditDialogDraft((prev) => {
                        const next: Partial<ProductRow> = { ...prev, unit_count: nextDoses }
                        const qty = Number(prev.package_size_g ?? 0)
                        if (nextDoses != null && nextDoses > 0 && qty > 0) {
                          next.min_unit = Number((qty / nextDoses).toFixed(4))
                        }
                        return next
                      })
                    }}
                    fullWidth
                  />
                  <TextField
                    size='small'
                    type='number'
                    label='Ml/g na doze'
                    value={editDialogDraft.min_unit ?? ''}
                    onChange={(e) => {
                      const nextPerDose = e.target.value === '' ? null : Number(e.target.value)
                      setEditDialogDraft((prev) => {
                        const next: Partial<ProductRow> = { ...prev, min_unit: nextPerDose }
                        const qty = Number(prev.package_size_g ?? 0)
                        if (nextPerDose != null && nextPerDose > 0 && qty > 0) {
                          next.unit_count = Number((qty / nextPerDose).toFixed(4))
                        }
                        return next
                      })
                    }}
                    fullWidth
                  />
                </Stack>
                <Stack direction='row' spacing={1.5} sx={{ alignItems: 'center' }}>
                  <Typography variant='caption' color='text.secondary'>
                    Netto z wag: {netFromWeights ?? '-'}
                  </Typography>
                  <Typography variant='caption' color='text.secondary'>
                    Waga 1 dozy: {doseWeight ?? '-'}
                  </Typography>
                </Stack>
              </>
            )}
            {isSalesForm ? (
              <>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
                  <TextField
                    size='small'
                    type='number'
                    label='Cena kat. net'
                    value={editDialogDraft.catalog_net_price ?? ''}
                    onChange={(e) => setEditDialogDraft((prev) => ({ ...prev, catalog_net_price: e.target.value === '' ? null : Number(e.target.value) }))}
                    fullWidth
                  />
                  <TextField
                    size='small'
                    type='number'
                    label='Cena sprz. brutto'
                    value={editDialogDraft.sale_price_gross ?? ''}
                    onChange={(e) => setEditDialogDraft((prev) => ({ ...prev, sale_price_gross: e.target.value === '' ? null : Number(e.target.value) }))}
                    fullWidth
                  />
                </Stack>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
                  <TextField
                    size='small'
                    type='number'
                    label='Cena zak.'
                    value={editDialogDraft.purchase_price ?? ''}
                    onChange={(e) => setEditDialogDraft((prev) => ({ ...prev, purchase_price: e.target.value === '' ? null : Number(e.target.value) }))}
                    fullWidth
                  />
                  <TextField
                    size='small'
                    type='number'
                    label='Cena salon'
                    value={editDialogDraft.salon_sale_price ?? ''}
                    onChange={(e) => setEditDialogDraft((prev) => ({ ...prev, salon_sale_price: e.target.value === '' ? null : Number(e.target.value) }))}
                    fullWidth
                  />
                </Stack>
              </>
            ) : (
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
                <TextField
                  size='small'
                  type='number'
                  label='Cena zak.'
                  value={editDialogDraft.purchase_price ?? ''}
                  onChange={(e) => setEditDialogDraft((prev) => ({ ...prev, purchase_price: e.target.value === '' ? null : Number(e.target.value) }))}
                  fullWidth
                />
              </Stack>
            )}
            {isServiceForm && (
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
                <TextField
                  size='small'
                  type='number'
                  label='Waga pelna (g)'
                  value={editDialogDraft.weight ?? ''}
                  onChange={(e) => setEditDialogDraft((prev) => ({ ...prev, weight: e.target.value === '' ? null : Number(e.target.value) }))}
                  fullWidth
                />
                <TextField
                  size='small'
                  type='number'
                  label='Waga pustej butelki/opak. (g)'
                  value={editDialogDraft.package_weight ?? ''}
                  onChange={(e) => setEditDialogDraft((prev) => ({ ...prev, package_weight: e.target.value === '' ? null : Number(e.target.value) }))}
                  fullWidth
                />
              </Stack>
            )}
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
              <Autocomplete
                fullWidth
                freeSolo
                options={typeOptions}
                value={typeOptions.find((o) => o.value === ((editDialogDraft.type_code as string) ?? '')) || ((editDialogDraft.type_code as string) ?? '')}
                inputValue={(editDialogDraft.type_code as string) ?? ''}
                onInputChange={(_, newInputValue) =>
                  setEditDialogDraft((prev) => ({ ...prev, type_code: newInputValue || '' }))
                }
                onChange={(_, option) =>
                  setEditDialogDraft((prev) => ({
                    ...prev,
                    type_code: typeof option === 'string' ? option : option?.value || '',
                  }))
                }
                getOptionLabel={(option) => (typeof option === 'string' ? option : option.label)}
                isOptionEqualToValue={(option, value) =>
                  option.value === (typeof value === 'string' ? value : value.value)
                }
                renderInput={(params) => (
                  <TextField {...params} size='small' label='Typ' placeholder='Wyszukaj lub wpisz typ' />
                )}
              />
            </Stack>
            <TextField
              size='small'
              label='Uwagi'
              value={editDialogDraft.note ?? ''}
              onChange={(e) => setEditDialogDraft((prev) => ({ ...prev, note: e.target.value }))}
              fullWidth
            />
            <FormControlLabel
              control={<Switch checked={Boolean(editDialogDraft.is_active)} onChange={(_, checked) => setEditDialogDraft((prev) => ({ ...prev, is_active: checked }))} />}
              label='Aktywny'
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeEditDialog}>Anuluj</Button>
          <Button variant='contained' onClick={saveEditDialog} disabled={savingDialog}>
            Zapisz
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default AlertsPage
