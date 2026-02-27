import { Fragment, useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Autocomplete,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { Add, CheckCircle, Refresh } from '@mui/icons-material'
import { useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext'
import { useBooking } from '../contexts/BookingContext'
import { api } from '../services/api'

type SalonRow = { id: number; code?: string; name: string }
type StockLocationRow = { id: number; salon_id: number; code: string; name: string; location_type: string; is_active: boolean }
type StockLevelRow = {
  id: number
  stock_location_id: number
  stock_location_name?: string | null
  salon_id?: number | null
  product_id: number
  product_name?: string | null
  quantity: number
  unit: string
}
type StaffRow = { id: number; display_name: string; role_code?: string | null; can_be_booked: boolean }
type IssueLineRow = {
  id: number
  recipe_item_id?: number | null
  recipe_product_family?: string | null
  recipe_note?: string | null
  product_id?: number | null
  product_name?: string | null
  quantity_actual?: number | null
  quantity_planned?: number | null
  unit: string
  unit_cost: number
  total_cost: number
}
type InventoryIssueRow = {
  id: number
  salon_id: number
  stock_location_id: number
  appointment_id?: number | null
  service_id?: number | null
  performed_line_id?: number | null
  staff_id?: number | null
  issue_time: string
  status: string
  remarks?: string | null
  lines: IssueLineRow[]
}
type SaleLineRow = {
  id: number
  product_id: number
  quantity: number
  unit: string
  unit_price_gross: number
  total_price_gross: number
  fiscal_code?: string | null
}
type SaleRow = {
  id: number
  salon_id: number
  customer_id?: number | null
  appointment_id?: number | null
  cashier_user_id: number
  sale_time: string
  total_gross: number
  status: string
  lines: SaleLineRow[]
}
type ProductOption = { product_id: number; product_name: string; fiscal_code?: string | null; sale_price_gross?: number | null; family_code?: string | null }

type IssueDraftLine = { product: ProductOption | null; quantityActual: string; unit: string }
type SaleDraftLine = { product: ProductOption | null; quantity: string; unit: string; unitPriceGross: string }
type IssueEditDraft = { id: number; remarks: string; lines: Array<{ id: number; product: ProductOption | null; quantityActual: string; unit: string; recipeProductFamily?: string | null }> }

const INVENTORY_TABS = [
  { label: 'Lokalizacje', path: '/inventory/stock-locations' },
  { label: 'Stany', path: '/inventory/stock-levels' },
  { label: 'Rozchody', path: '/inventory/issues' },
  { label: 'Sprzedaz', path: '/inventory/sales' },
] as const

const InventoryPage = () => {
  const { user } = useAuth()
  const { salons: bookingSalons, appointments, colorProducts } = useBooking()
  const navigate = useNavigate()
  const location = useLocation()

  const salons = useMemo<SalonRow[]>(() => bookingSalons.map((s) => ({ id: s.id, code: s.code, name: s.name })), [bookingSalons])
  const currentTab = INVENTORY_TABS.find((item) => location.pathname.startsWith(item.path))?.path ?? INVENTORY_TABS[1].path
  const appointmentFilterId = useMemo(() => {
    const raw = new URLSearchParams(location.search).get('appointment_id')
    if (!raw) return null
    const parsed = Number(raw)
    return Number.isFinite(parsed) ? parsed : null
  }, [location.search])

  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [loading, setLoading] = useState(false)

  const [stockLocations, setStockLocations] = useState<StockLocationRow[]>([])
  const [stockLevels, setStockLevels] = useState<StockLevelRow[]>([])
  const [issues, setIssues] = useState<InventoryIssueRow[]>([])
  const [sales, setSales] = useState<SaleRow[]>([])
  const [salonStaff, setSalonStaff] = useState<StaffRow[]>([])
  const [productOptions, setProductOptions] = useState<ProductOption[]>([])

  const [selectedSalonId, setSelectedSalonId] = useState<number | ''>('')
  const [selectedLocationId, setSelectedLocationId] = useState<number | ''>('')
  const [productQuery, setProductQuery] = useState('')
  const [issueStatusFilter, setIssueStatusFilter] = useState<'ALL' | 'PLANNED' | 'POSTED'>('ALL')
  const [salesFromDate, setSalesFromDate] = useState('')
  const [salesToDate, setSalesToDate] = useState('')

  const [locationDialogOpen, setLocationDialogOpen] = useState(false)
  const [newLocationName, setNewLocationName] = useState('')
  const [newLocationCode, setNewLocationCode] = useState('')
  const [newLocationType, setNewLocationType] = useState('MIXED')

  const [issueDialogOpen, setIssueDialogOpen] = useState(false)
  const [draftIssueLocationId, setDraftIssueLocationId] = useState<number | ''>('')
  const [draftIssueAppointmentId, setDraftIssueAppointmentId] = useState<number | ''>('')
  const [draftIssueStaffId, setDraftIssueStaffId] = useState<number | ''>('')
  const [draftIssueRemarks, setDraftIssueRemarks] = useState('')
  const [draftIssueLines, setDraftIssueLines] = useState<IssueDraftLine[]>([{ product: null, quantityActual: '', unit: 'PCS' }])
  const [expandedIssueId, setExpandedIssueId] = useState<number | null>(null)
  const [issueEditDraft, setIssueEditDraft] = useState<IssueEditDraft | null>(null)

  const [saleDialogOpen, setSaleDialogOpen] = useState(false)
  const [draftSaleCustomerId, setDraftSaleCustomerId] = useState<number | ''>('')
  const [draftSaleAppointmentId, setDraftSaleAppointmentId] = useState<number | ''>('')
  const [draftSaleLines, setDraftSaleLines] = useState<SaleDraftLine[]>([{ product: null, quantity: '1', unit: 'PCS', unitPriceGross: '' }])

  const canManageLocations = user?.role === 'admin' || user?.role === 'manager'
  const canWriteInventory = ['admin', 'manager', 'receptionist', 'employee'].includes(user?.role || '')
  const canWriteSales = ['admin', 'manager', 'receptionist'].includes(user?.role || '')

  const locationOptions = useMemo(
    () => stockLocations.filter((item) => (selectedSalonId === '' ? true : item.salon_id === selectedSalonId)),
    [selectedSalonId, stockLocations],
  )

  const visibleStockLevels = useMemo(() => {
    const q = productQuery.trim().toLowerCase()
    return stockLevels.filter((row) => (q ? `${row.product_name || ''}`.toLowerCase().includes(q) : true))
  }, [productQuery, stockLevels])

  const visibleAppointments = useMemo(
    () => appointments.filter((item) => (selectedSalonId === '' ? true : item.salon_id === selectedSalonId)),
    [appointments, selectedSalonId],
  )

  const retailProductOptions = useMemo(
    () => productOptions.filter((item) => item.fiscal_code || (item.sale_price_gross || 0) > 0),
    [productOptions],
  )

  const loadStockLocations = async () => {
    const res = await api.get<StockLocationRow[]>('/inventory/stock-locations', {
      params: selectedSalonId === '' ? undefined : { salon_id: selectedSalonId },
    })
    setStockLocations(res.data || [])
  }

  const loadStockLevels = async () => {
    const params: Record<string, number> = {}
    if (selectedSalonId !== '') params.salon_id = selectedSalonId
    if (selectedLocationId !== '') params.location_id = selectedLocationId
    const res = await api.get<StockLevelRow[]>('/inventory/stock-levels', { params })
    setStockLevels(res.data || [])
  }

  const loadIssues = async () => {
    const params: Record<string, string | number> = {}
    if (selectedSalonId !== '' && appointmentFilterId === null) params.salon_id = selectedSalonId
    if (appointmentFilterId !== null) params.appointment_id = appointmentFilterId
    if (issueStatusFilter !== 'ALL') params.status_filter = issueStatusFilter
    const res = await api.get<InventoryIssueRow[]>('/inventory/issues', { params })
    setIssues(res.data || [])
    if (expandedIssueId !== null) {
      const refreshed = (res.data || []).find((item) => item.id === expandedIssueId)
      if (refreshed) {
        setIssueEditDraft({
          id: refreshed.id,
          remarks: refreshed.remarks || '',
          lines: refreshed.lines.map((line) => ({
            id: line.id,
            product: line.product_id ? productOptions.find((item) => item.product_id === line.product_id) || null : null,
            quantityActual: line.quantity_actual == null ? '' : String(line.quantity_actual),
            unit: line.unit,
            recipeProductFamily: line.recipe_product_family || null,
          })),
        })
      }
    }
  }

  const loadSales = async () => {
    const params: Record<string, string | number> = {}
    if (selectedSalonId !== '') params.salon_id = selectedSalonId
    if (salesFromDate) params.date_from = salesFromDate
    if (salesToDate) params.date_to = salesToDate
    const res = await api.get<SaleRow[]>('/sales', { params })
    setSales(res.data || [])
  }

  const loadSalonStaff = async (salonId: number) => {
    const res = await api.get<StaffRow[]>(`/booking/salons/${salonId}/staff`)
    setSalonStaff(res.data || [])
  }

  const loadProductsForSalon = async (salonId: number) => {
    const res = await api.get<ProductOption[]>('/resources/products', { params: { salon_id: salonId } })
    setProductOptions(res.data || [])
  }

  const safeLoad = async (fn: () => Promise<void>) => {
    setLoading(true)
    setError('')
    try {
      await fn()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie pobrac danych.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (selectedSalonId === '' && salons.length) {
      const allowed = user?.assigned_salon_ids?.length ? user.assigned_salon_ids[0] : salons[0].id
      setSelectedSalonId(allowed)
    }
  }, [salons, selectedSalonId, user?.assigned_salon_ids])

  useEffect(() => {
    safeLoad(async () => {
      await loadStockLocations()
    })
  }, [selectedSalonId])

  useEffect(() => {
    if (currentTab === '/inventory/stock-levels') {
      safeLoad(loadStockLevels)
      const timer = window.setInterval(() => {
        loadStockLevels().catch(() => undefined)
      }, 60000)
      return () => window.clearInterval(timer)
    }
    if (currentTab === '/inventory/issues') {
      safeLoad(loadIssues)
    }
    if (currentTab === '/inventory/sales') {
      safeLoad(loadSales)
    }
    return undefined
  }, [currentTab, selectedSalonId, selectedLocationId, issueStatusFilter, salesFromDate, salesToDate, appointmentFilterId])

  useEffect(() => {
    if (selectedSalonId === '') return
    loadSalonStaff(selectedSalonId).catch(() => undefined)
    loadProductsForSalon(selectedSalonId).catch(() => undefined)
  }, [selectedSalonId])

  const resetIssueDraft = () => {
    setDraftIssueLocationId('')
    setDraftIssueAppointmentId('')
    setDraftIssueStaffId(user?.role === 'employee' && salonStaff.length ? salonStaff[0].id : '')
    setDraftIssueRemarks('')
    setDraftIssueLines([{ product: null, quantityActual: '', unit: 'PCS' }])
  }

  const resetSaleDraft = () => {
    setDraftSaleCustomerId('')
    setDraftSaleAppointmentId('')
    setDraftSaleLines([{ product: null, quantity: '1', unit: 'PCS', unitPriceGross: '' }])
  }

  const handleCreateLocation = async () => {
    if (selectedSalonId === '' || !newLocationName.trim() || !newLocationCode.trim()) return
    setError('')
    try {
      await api.post('/inventory/stock-locations', {
        salon_id: selectedSalonId,
        code: newLocationCode.trim().toUpperCase(),
        name: newLocationName.trim(),
        location_type: newLocationType,
      })
      setInfo('Dodano lokalizacje magazynowa.')
      setLocationDialogOpen(false)
      setNewLocationName('')
      setNewLocationCode('')
      setNewLocationType('MIXED')
      await loadStockLocations()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie dodac lokalizacji.')
    }
  }

  const handleCreateIssue = async () => {
    if (selectedSalonId === '' || draftIssueLocationId === '') return
    const lines = draftIssueLines
      .filter((line) => line.product && Number(line.quantityActual) > 0)
      .map((line) => ({
        product_id: line.product!.product_id,
        quantity_actual: Number(line.quantityActual),
        unit: line.unit,
      }))
    if (!lines.length) {
      setError('Dodaj co najmniej jedna linie rozchodu.')
      return
    }
    try {
      await api.post('/inventory/issues', {
        salon_id: selectedSalonId,
        stock_location_id: draftIssueLocationId,
        appointment_id: draftIssueAppointmentId === '' ? null : draftIssueAppointmentId,
        staff_id: draftIssueStaffId === '' ? null : draftIssueStaffId,
        issue_time: new Date().toISOString(),
        remarks: draftIssueRemarks,
        lines,
      })
      setInfo('Utworzono dokument rozchodu.')
      setIssueDialogOpen(false)
      resetIssueDraft()
      await loadIssues()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie utworzyc rozchodu.')
    }
  }

  const handlePostIssue = async (issueId: number) => {
    try {
      await api.post(`/inventory/issues/${issueId}/post`)
      setInfo('Rozchod zatwierdzony.')
      await loadIssues()
      if (currentTab === '/inventory/stock-levels') await loadStockLevels()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zatwierdzic rozchodu.')
    }
  }

  const openIssueEditor = (row: InventoryIssueRow) => {
    if (expandedIssueId === row.id) {
      setExpandedIssueId(null)
      setIssueEditDraft(null)
      return
    }
    setExpandedIssueId(row.id)
    setIssueEditDraft({
      id: row.id,
      remarks: row.remarks || '',
      lines: row.lines.map((line) => ({
        id: line.id,
        product: line.product_id ? productOptions.find((item) => item.product_id === line.product_id) || null : null,
        quantityActual: line.quantity_actual == null ? '' : String(line.quantity_actual),
        unit: line.unit,
        recipeProductFamily: line.recipe_product_family || null,
      })),
    })
  }

  const handleSaveIssue = async () => {
    if (!issueEditDraft) return
    try {
      await api.patch(`/inventory/issues/${issueEditDraft.id}`, {
        remarks: issueEditDraft.remarks,
        lines: issueEditDraft.lines.map((line) => ({
          id: line.id,
          product_id: line.product?.product_id ?? null,
          quantity_actual: line.quantityActual === '' ? null : Number(line.quantityActual),
          unit: line.unit,
        })),
      })
      setInfo('Dokument rozchodu zaktualizowany.')
      await loadIssues()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zapisac rozchodu.')
    }
  }

  const handleCreateSale = async () => {
    if (selectedSalonId === '') return
    const lines = draftSaleLines
      .filter((line) => line.product && Number(line.quantity) > 0)
      .map((line) => ({
        product_id: line.product!.product_id,
        quantity: Number(line.quantity),
        unit: line.unit,
        unit_price_gross: Number(line.unitPriceGross || line.product?.sale_price_gross || 0),
      }))
    if (!lines.length) {
      setError('Dodaj co najmniej jedna linie sprzedazy.')
      return
    }
    try {
      await api.post('/sales', {
        salon_id: selectedSalonId,
        customer_id: draftSaleCustomerId === '' ? null : draftSaleCustomerId,
        appointment_id: draftSaleAppointmentId === '' ? null : draftSaleAppointmentId,
        sale_time: new Date().toISOString(),
        lines,
      })
      setInfo('Utworzono sprzedaz.')
      setSaleDialogOpen(false)
      resetSaleDraft()
      await loadSales()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie utworzyc sprzedazy.')
    }
  }

  const handleCompleteSale = async (saleId: number) => {
    try {
      await api.post(`/sales/${saleId}/complete`)
      setInfo('Sprzedaz zakonczona.')
      await loadSales()
      if (currentTab === '/inventory/stock-levels') await loadStockLevels()
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Nie udalo sie zakonczyc sprzedazy.')
    }
  }

  const renderStockLocations = () => (
    <Card>
      <CardContent>
        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" sx={{ mb: 2 }} spacing={1}>
          <Typography variant="h6">Lokalizacje magazynowe</Typography>
          <Stack direction="row" spacing={1}>
            <Button startIcon={<Refresh />} onClick={() => safeLoad(loadStockLocations)}>Odswiez</Button>
            {canManageLocations && (
              <Button variant="contained" startIcon={<Add />} onClick={() => setLocationDialogOpen(true)}>Dodaj</Button>
            )}
          </Stack>
        </Stack>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Nazwa</TableCell>
              <TableCell>Typ</TableCell>
              <TableCell>Salon</TableCell>
              <TableCell>Kod</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {stockLocations.map((row) => (
              <TableRow key={row.id}>
                <TableCell>{row.name}</TableCell>
                <TableCell><Chip size="small" label={row.location_type} /></TableCell>
                <TableCell>{salons.find((s) => s.id === row.salon_id)?.name || row.salon_id}</TableCell>
                <TableCell>{row.code}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )

  const renderStockLevels = () => (
    <Card>
      <CardContent>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} sx={{ mb: 2 }}>
          <FormControl size="small" sx={{ minWidth: 220 }}>
            <InputLabel>Lokalizacja</InputLabel>
            <Select
              label="Lokalizacja"
              value={selectedLocationId}
              onChange={(e) => setSelectedLocationId(e.target.value === '' ? '' : Number(e.target.value))}
            >
              <MenuItem value="">Wszystkie</MenuItem>
              {locationOptions.map((row) => <MenuItem key={row.id} value={row.id}>{row.name}</MenuItem>)}
            </Select>
          </FormControl>
          <TextField size="small" label="Szukaj produktu" value={productQuery} onChange={(e) => setProductQuery(e.target.value)} sx={{ minWidth: 280 }} />
          <Button startIcon={<Refresh />} onClick={() => safeLoad(loadStockLevels)}>Odswiez</Button>
        </Stack>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Produkt</TableCell>
              <TableCell>Lokalizacja</TableCell>
              <TableCell align="right">Stan</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {visibleStockLevels.map((row) => (
              <TableRow key={row.id}>
                <TableCell>{row.product_name || row.product_id}</TableCell>
                <TableCell>{row.stock_location_name || row.stock_location_id}</TableCell>
                <TableCell align="right">{row.quantity.toFixed(2)} {row.unit}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )

  const renderIssues = () => (
    <Card>
      <CardContent>
        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" sx={{ mb: 2 }} spacing={1}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel>Status</InputLabel>
              <Select label="Status" value={issueStatusFilter} onChange={(e) => setIssueStatusFilter(e.target.value as 'ALL' | 'PLANNED' | 'POSTED')}>
                <MenuItem value="ALL">Wszystkie</MenuItem>
                <MenuItem value="PLANNED">PLANNED</MenuItem>
                <MenuItem value="POSTED">POSTED</MenuItem>
              </Select>
            </FormControl>
            <Button startIcon={<Refresh />} onClick={() => safeLoad(loadIssues)}>Odswiez</Button>
            {appointmentFilterId !== null && <Chip size="small" color="info" label={`Wizyta #${appointmentFilterId}`} />}
          </Stack>
          {canWriteInventory && <Button variant="contained" startIcon={<Add />} onClick={() => { resetIssueDraft(); setIssueDialogOpen(true) }}>Nowy rozchod</Button>}
        </Stack>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Data</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Lokalizacja</TableCell>
              <TableCell>Pracownik</TableCell>
              <TableCell align="right">Koszt</TableCell>
              <TableCell>Akcje</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {issues.map((row) => {
              const canPost = row.status === 'PLANNED' && row.lines.every((line) => !!line.product_id && (line.quantity_actual ?? 0) > 0)
              const draft = expandedIssueId === row.id ? issueEditDraft : null
              return (
                <Fragment key={row.id}>
                  <TableRow>
                    <TableCell>{row.id}</TableCell>
                    <TableCell>{new Date(row.issue_time).toLocaleString()}</TableCell>
                    <TableCell><Chip size="small" label={row.status} color={row.status === 'POSTED' ? 'success' : 'default'} /></TableCell>
                    <TableCell>{stockLocations.find((item) => item.id === row.stock_location_id)?.name || row.stock_location_id}</TableCell>
                    <TableCell>{salonStaff.find((item) => item.id === row.staff_id)?.display_name || row.staff_id || '-'}</TableCell>
                    <TableCell align="right">{row.lines.reduce((sum, line) => sum + line.total_cost, 0).toFixed(2)}</TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={1}>
                        {row.status === 'PLANNED' && (
                          <Button size="small" variant="outlined" onClick={() => openIssueEditor(row)}>Szczegoly</Button>
                        )}
                        {row.status === 'PLANNED' && canWriteInventory && (
                          <Button size="small" startIcon={<CheckCircle />} onClick={() => handlePostIssue(row.id)} disabled={!canPost}>Zatwierdz</Button>
                        )}
                      </Stack>
                    </TableCell>
                  </TableRow>
                  {draft && (
                    <TableRow>
                      <TableCell colSpan={7}>
                        <Stack spacing={1.5} sx={{ py: 1 }}>
                          <TextField
                            size="small"
                            label="Uwagi"
                            value={draft.remarks}
                            onChange={(e) => setIssueEditDraft((prev) => (prev ? { ...prev, remarks: e.target.value } : prev))}
                          />
                          {draft.lines.map((line, index) => {
                            const filteredOptions = (line.recipeProductFamily
                              ? productOptions.filter((item) => (item.family_code || '').toUpperCase() === line.recipeProductFamily?.toUpperCase())
                              : productOptions)
                            return (
                              <Stack key={line.id} direction={{ xs: 'column', md: 'row' }} spacing={1.5} alignItems="center">
                                <Autocomplete
                                  options={filteredOptions}
                                  getOptionLabel={(option) => option.product_name}
                                  value={line.product}
                                  onChange={(_, value) =>
                                    setIssueEditDraft((prev) =>
                                      prev
                                        ? {
                                            ...prev,
                                            lines: prev.lines.map((item, idx) => (idx === index ? { ...item, product: value } : item)),
                                          }
                                        : prev
                                    )
                                  }
                                  renderInput={(params) => (
                                    <TextField
                                      {...params}
                                      label={line.recipeProductFamily ? `Produkt (${line.recipeProductFamily})` : 'Produkt'}
                                    />
                                  )}
                                  sx={{ flex: 1 }}
                                />
                                <TextField
                                  size="small"
                                  label="Plan"
                                  value={row.lines[index]?.quantity_planned ?? ''}
                                  InputProps={{ readOnly: true }}
                                  sx={{ width: 120 }}
                                />
                                <TextField
                                  size="small"
                                  label="Actual"
                                  value={line.quantityActual}
                                  onChange={(e) =>
                                    setIssueEditDraft((prev) =>
                                      prev
                                        ? {
                                            ...prev,
                                            lines: prev.lines.map((item, idx) => (idx === index ? { ...item, quantityActual: e.target.value } : item)),
                                          }
                                        : prev
                                    )
                                  }
                                  sx={{ width: 120 }}
                                />
                                <FormControl size="small" sx={{ width: 120 }}>
                                  <InputLabel>Jedn.</InputLabel>
                                  <Select
                                    label="Jedn."
                                    value={line.unit}
                                    onChange={(e) =>
                                      setIssueEditDraft((prev) =>
                                        prev
                                          ? {
                                              ...prev,
                                              lines: prev.lines.map((item, idx) => (idx === index ? { ...item, unit: String(e.target.value) } : item)),
                                            }
                                          : prev
                                      )
                                    }
                                  >
                                    <MenuItem value="PCS">PCS</MenuItem>
                                    <MenuItem value="G">G</MenuItem>
                                    <MenuItem value="ML">ML</MenuItem>
                                  </Select>
                                </FormControl>
                              </Stack>
                            )
                          })}
                          <Stack direction="row" spacing={1}>
                            <Button variant="contained" onClick={handleSaveIssue}>Zapisz linie</Button>
                            <Button onClick={() => { setExpandedIssueId(null); setIssueEditDraft(null) }}>Zamknij</Button>
                          </Stack>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  )}
                </Fragment>
              )
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )

  const renderSales = () => (
    <Card>
      <CardContent>
        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" sx={{ mb: 2 }} spacing={1}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
            <TextField size="small" type="date" label="Od" InputLabelProps={{ shrink: true }} value={salesFromDate} onChange={(e) => setSalesFromDate(e.target.value)} />
            <TextField size="small" type="date" label="Do" InputLabelProps={{ shrink: true }} value={salesToDate} onChange={(e) => setSalesToDate(e.target.value)} />
            <Button startIcon={<Refresh />} onClick={() => safeLoad(loadSales)}>Odswiez</Button>
          </Stack>
          {canWriteSales && <Button variant="contained" startIcon={<Add />} onClick={() => { resetSaleDraft(); setSaleDialogOpen(true) }}>Nowa sprzedaz</Button>}
        </Stack>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Data</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Kwota</TableCell>
              <TableCell>Akcje</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sales.map((row) => (
              <TableRow key={row.id}>
                <TableCell>{row.id}</TableCell>
                <TableCell>{new Date(row.sale_time).toLocaleString()}</TableCell>
                <TableCell><Chip size="small" label={row.status} color={row.status === 'COMPLETED' ? 'success' : 'default'} /></TableCell>
                <TableCell align="right">{row.total_gross.toFixed(2)}</TableCell>
                <TableCell>
                  {row.status === 'OPEN' && canWriteSales && (
                    <Button size="small" startIcon={<CheckCircle />} onClick={() => handleCompleteSale(row.id)}>Zakoncz</Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )

  const content =
    currentTab === '/inventory/stock-locations'
      ? renderStockLocations()
      : currentTab === '/inventory/stock-levels'
        ? renderStockLevels()
        : currentTab === '/inventory/issues'
          ? renderIssues()
          : renderSales()

  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1.5}>
        <Typography variant="h4">Magazyn</Typography>
        <FormControl size="small" sx={{ minWidth: 260 }}>
          <InputLabel>Salon</InputLabel>
          <Select
            label="Salon"
            value={selectedSalonId}
            onChange={(e) => {
              setSelectedSalonId(e.target.value === '' ? '' : Number(e.target.value))
              setSelectedLocationId('')
            }}
          >
            {salons.map((row) => <MenuItem key={row.id} value={row.id}>{row.code ? `${row.code} - ` : ''}{row.name}</MenuItem>)}
          </Select>
        </FormControl>
      </Stack>

      <Tabs value={currentTab} onChange={(_, value) => navigate(value)} variant="scrollable" scrollButtons="auto">
        {INVENTORY_TABS.map((item) => <Tab key={item.path} value={item.path} label={item.label} />)}
      </Tabs>

      {error && <Alert severity="error">{error}</Alert>}
      {info && <Alert severity="success">{info}</Alert>}
      {loading && <Alert severity="info">Ladowanie danych...</Alert>}

      {content}

      <Dialog open={locationDialogOpen} onClose={() => setLocationDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Dodaj lokalizacje magazynowa</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField label="Nazwa" value={newLocationName} onChange={(e) => setNewLocationName(e.target.value)} fullWidth />
            <TextField label="Kod" value={newLocationCode} onChange={(e) => setNewLocationCode(e.target.value)} fullWidth />
            <FormControl fullWidth>
              <InputLabel>Typ</InputLabel>
              <Select label="Typ" value={newLocationType} onChange={(e) => setNewLocationType(e.target.value)}>
                <MenuItem value="RETAIL">RETAIL</MenuItem>
                <MenuItem value="BACKBAR">BACKBAR</MenuItem>
                <MenuItem value="MIXED">MIXED</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLocationDialogOpen(false)}>Anuluj</Button>
          <Button variant="contained" onClick={handleCreateLocation}>Zapisz</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={issueDialogOpen} onClose={() => setIssueDialogOpen(false)} fullWidth maxWidth="md">
        <DialogTitle>Nowy rozchod</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <FormControl fullWidth>
                <InputLabel>Lokalizacja</InputLabel>
                <Select label="Lokalizacja" value={draftIssueLocationId} onChange={(e) => setDraftIssueLocationId(e.target.value === '' ? '' : Number(e.target.value))}>
                  {locationOptions.map((row) => <MenuItem key={row.id} value={row.id}>{row.name}</MenuItem>)}
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>Wizyta</InputLabel>
                <Select label="Wizyta" value={draftIssueAppointmentId} onChange={(e) => setDraftIssueAppointmentId(e.target.value === '' ? '' : Number(e.target.value))}>
                  <MenuItem value="">Brak</MenuItem>
                  {visibleAppointments.slice(0, 100).map((row) => <MenuItem key={row.id} value={row.id}>#{row.id} {new Date(row.start_at).toLocaleString()}</MenuItem>)}
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>Pracownik</InputLabel>
                <Select label="Pracownik" value={draftIssueStaffId} onChange={(e) => setDraftIssueStaffId(e.target.value === '' ? '' : Number(e.target.value))}>
                  <MenuItem value="">Brak</MenuItem>
                  {salonStaff.map((row) => <MenuItem key={row.id} value={row.id}>{row.display_name}</MenuItem>)}
                </Select>
              </FormControl>
            </Stack>
            <TextField label="Uwagi" value={draftIssueRemarks} onChange={(e) => setDraftIssueRemarks(e.target.value)} fullWidth />
            {draftIssueLines.map((line, index) => (
              <Stack key={index} direction={{ xs: 'column', md: 'row' }} spacing={1.5} alignItems="center">
                <Autocomplete
                  options={productOptions.length ? productOptions : colorProducts.map((item) => ({ product_id: item.id, product_name: item.name }))}
                  getOptionLabel={(option) => option.product_name}
                  value={line.product}
                  onChange={(_, value) => setDraftIssueLines((prev) => prev.map((item, idx) => idx === index ? { ...item, product: value } : item))}
                  renderInput={(params) => <TextField {...params} label="Produkt" />}
                  sx={{ flex: 1 }}
                />
                <TextField label="Ilosc" value={line.quantityActual} onChange={(e) => setDraftIssueLines((prev) => prev.map((item, idx) => idx === index ? { ...item, quantityActual: e.target.value } : item))} sx={{ width: 120 }} />
                <FormControl sx={{ width: 120 }}>
                  <InputLabel>Jedn.</InputLabel>
                  <Select label="Jedn." value={line.unit} onChange={(e) => setDraftIssueLines((prev) => prev.map((item, idx) => idx === index ? { ...item, unit: e.target.value } : item))}>
                    <MenuItem value="PCS">PCS</MenuItem>
                    <MenuItem value="G">G</MenuItem>
                    <MenuItem value="ML">ML</MenuItem>
                  </Select>
                </FormControl>
              </Stack>
            ))}
            <Button onClick={() => setDraftIssueLines((prev) => [...prev, { product: null, quantityActual: '', unit: 'PCS' }])}>Dodaj linie</Button>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIssueDialogOpen(false)}>Anuluj</Button>
          <Button variant="contained" onClick={handleCreateIssue}>Zapisz</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={saleDialogOpen} onClose={() => setSaleDialogOpen(false)} fullWidth maxWidth="md">
        <DialogTitle>Nowa sprzedaz</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <FormControl fullWidth>
                <InputLabel>Wizyta</InputLabel>
                <Select label="Wizyta" value={draftSaleAppointmentId} onChange={(e) => setDraftSaleAppointmentId(e.target.value === '' ? '' : Number(e.target.value))}>
                  <MenuItem value="">Brak</MenuItem>
                  {visibleAppointments.slice(0, 100).map((row) => <MenuItem key={row.id} value={row.id}>#{row.id} {new Date(row.start_at).toLocaleString()}</MenuItem>)}
                </Select>
              </FormControl>
              <TextField label="ID klienta (opcjonalnie)" value={draftSaleCustomerId} onChange={(e) => setDraftSaleCustomerId(e.target.value === '' ? '' : Number(e.target.value))} fullWidth />
            </Stack>
            {draftSaleLines.map((line, index) => (
              <Stack key={index} direction={{ xs: 'column', md: 'row' }} spacing={1.5} alignItems="center">
                <Autocomplete
                  options={retailProductOptions}
                  getOptionLabel={(option) => option.product_name}
                  value={line.product}
                  onChange={(_, value) => setDraftSaleLines((prev) => prev.map((item, idx) => idx === index ? { ...item, product: value, unitPriceGross: value?.sale_price_gross ? String(value.sale_price_gross) : item.unitPriceGross } : item))}
                  renderInput={(params) => <TextField {...params} label="Produkt retail" />}
                  sx={{ flex: 1 }}
                />
                <TextField label="Ilosc" value={line.quantity} onChange={(e) => setDraftSaleLines((prev) => prev.map((item, idx) => idx === index ? { ...item, quantity: e.target.value } : item))} sx={{ width: 100 }} />
                <TextField label="Cena brutto" value={line.unitPriceGross} onChange={(e) => setDraftSaleLines((prev) => prev.map((item, idx) => idx === index ? { ...item, unitPriceGross: e.target.value } : item))} sx={{ width: 140 }} />
              </Stack>
            ))}
            <Button onClick={() => setDraftSaleLines((prev) => [...prev, { product: null, quantity: '1', unit: 'PCS', unitPriceGross: '' }])}>Dodaj linie</Button>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaleDialogOpen(false)}>Anuluj</Button>
          <Button variant="contained" onClick={handleCreateSale}>Zapisz</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}

export default InventoryPage
