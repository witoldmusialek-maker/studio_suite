import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { Download, Refresh } from '@mui/icons-material'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { api } from '../services/api'
import { useBooking } from '../contexts/BookingContext'

type LegacySummary = {
  salons: number
  services: number
  bundles: number
  forfait_transactions: number
  fiche_lines: number
  edition1_days: number
}

type LegacyForfaitRow = { bundle_code: string; bundle_name: string; count: number; revenue: number }
type LegacyForfaitTxRow = { date_token: string; bundle_code: string; bundle_name: string; price: number }
type LegacyServiceWorkerRow = { worker_code: string; worker_name: string; service_code: string; service_name: string; qty: number; revenue: number }
type LegacyServiceAggregateRow = { service_code: string; service_name: string; qty: number; revenue: number }
type LegacyMonthlyRow = { month: string; days_count: number; gross_total: number; net_total: number; vat_total: number; tickets_count: number }
type LegacyDailyRow = { date: string; day_name: string; gross_total: number; net_total: number; vat_total: number; tickets_count: number }
type LegacyCashflowRow = { date: string; payment_hint: string; count: number; revenue: number }
type LegacyStat7WorkerRow = { worker_code: string; worker_name: string; total: number; payment_a: string; payment_b: string; payment_c: string }

type MaterialByStaffRow = { staff_id?: number | null; staff_name?: string | null; services_count: number; lines_count: number; total_quantity: number; total_cost: number }
type MaterialByServiceRow = { service_id?: number | null; service_name?: string | null; lines_count: number; total_quantity: number; total_cost: number }
type MaterialDeviationRow = { staff_id?: number | null; staff_name?: string | null; lines_count: number; total_planned: number; total_actual: number; deviation: number }
type SalesBySalonRow = { salon_id: number; salon_name?: string | null; sales_count: number; transactions_count: number; lines_count: number; total_gross: number }

type ReportKey = 'forfaits_analysis' | 'forfaits_list' | 'services_worker' | 'services_aggregate' | 'daily_ed1' | 'monthly_ed1' | 'cashflow' | 'stat7'
type MainTab = 'legacy' | 'materials' | 'sales'
type MaterialMode = 'by-staff' | 'by-service' | 'deviations'

const TABLE_SX = {
  '& .MuiTableHead-root .MuiTableCell-root': {
    backgroundColor: '#3a6ea5',
    color: '#fff',
    fontWeight: 700,
    borderBottom: '1px solid #98b3d1',
  },
  '& .MuiTableBody-root .MuiTableCell-root': {
    borderBottom: '1px solid #c5d5e6',
    fontSize: 13,
    paddingTop: '6px',
    paddingBottom: '6px',
  },
}

const downloadCsv = (filename: string, rows: Record<string, unknown>[]) => {
  if (!rows.length) return
  const headers = Object.keys(rows[0])
  const csv = [
    headers.join(','),
    ...rows.map((row) => headers.map((header) => JSON.stringify(row[header] ?? '')).join(',')),
  ].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

const ReportsPage = () => {
  const { salons } = useBooking()
  const [mainTab, setMainTab] = useState<MainTab>('legacy')
  const [preset, setPreset] = useState<'month_end' | 'custom'>('month_end')
  const [fromDate, setFromDate] = useState('2025-10-01')
  const [toDate, setToDate] = useState('2026-02-28')
  const [selectedReport, setSelectedReport] = useState<ReportKey>('forfaits_analysis')
  const [materialMode, setMaterialMode] = useState<MaterialMode>('by-staff')
  const [selectedSalonId, setSelectedSalonId] = useState<number | ''>('')

  const [legacyLoading, setLegacyLoading] = useState(false)
  const [legacyError, setLegacyError] = useState('')
  const [opsLoading, setOpsLoading] = useState(false)
  const [opsError, setOpsError] = useState('')

  const [summary, setSummary] = useState<LegacySummary | null>(null)
  const [forfaits, setForfaits] = useState<LegacyForfaitRow[]>([])
  const [forfaitTx, setForfaitTx] = useState<LegacyForfaitTxRow[]>([])
  const [servicesWorker, setServicesWorker] = useState<LegacyServiceWorkerRow[]>([])
  const [servicesAgg, setServicesAgg] = useState<LegacyServiceAggregateRow[]>([])
  const [monthly, setMonthly] = useState<LegacyMonthlyRow[]>([])
  const [daily, setDaily] = useState<LegacyDailyRow[]>([])
  const [cashflow, setCashflow] = useState<LegacyCashflowRow[]>([])
  const [stat7, setStat7] = useState<LegacyStat7WorkerRow[]>([])

  const [materialByStaff, setMaterialByStaff] = useState<MaterialByStaffRow[]>([])
  const [materialByService, setMaterialByService] = useState<MaterialByServiceRow[]>([])
  const [materialDeviation, setMaterialDeviation] = useState<MaterialDeviationRow[]>([])
  const [salesBySalon, setSalesBySalon] = useState<SalesBySalonRow[]>([])

  useEffect(() => {
    if (selectedSalonId === '' && salons.length) setSelectedSalonId(salons[0].id)
  }, [salons, selectedSalonId])

  useEffect(() => {
    const fetchLegacyReports = async () => {
      setLegacyLoading(true)
      setLegacyError('')
      try {
        const params = { from_date: fromDate, to_date: toDate }
        const [summaryRes, forfaitsRes, forfaitTxRes, servicesWorkerRes, servicesAggRes, monthlyRes, dailyRes, cashflowRes, stat7Res] = await Promise.all([
          api.get('/legacy/reports/summary'),
          api.get('/legacy/reports/forfaits', { params }),
          api.get('/legacy/reports/forfait-transactions', { params }),
          api.get('/legacy/reports/services-by-worker', { params }),
          api.get('/legacy/reports/services-aggregate', { params }),
          api.get('/legacy/reports/monthly-summary'),
          api.get('/legacy/reports/daily-summary', { params }),
          api.get('/legacy/reports/cashflow', { params }),
          api.get('/legacy/reports/stat7-worker'),
        ])
        setSummary(summaryRes.data)
        setForfaits(forfaitsRes.data.rows || [])
        setForfaitTx(forfaitTxRes.data.rows || [])
        setServicesWorker(servicesWorkerRes.data.rows || [])
        setServicesAgg(servicesAggRes.data.rows || [])
        setMonthly(monthlyRes.data.rows || [])
        setDaily(dailyRes.data.rows || [])
        setCashflow(cashflowRes.data.rows || [])
        setStat7(stat7Res.data.rows || [])
      } catch (error) {
        console.error(error)
        setLegacyError('Nie udalo sie pobrac raportow legacy.')
      } finally {
        setLegacyLoading(false)
      }
    }
    fetchLegacyReports()
  }, [fromDate, toDate])

  const fetchOperational = async () => {
    setOpsLoading(true)
    setOpsError('')
    try {
      const params = {
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
        salon_id: selectedSalonId === '' ? undefined : selectedSalonId,
      }
      const [staffRes, serviceRes, deviationRes, salesRes] = await Promise.all([
        api.get('/reports/material-usage/by-staff', { params }),
        api.get('/reports/material-cost/by-service', { params }),
        api.get('/reports/deviation/by-staff', { params }),
        api.get('/reports/sales/by-salon', { params }),
      ])
      setMaterialByStaff(staffRes.data.rows || [])
      setMaterialByService(serviceRes.data.rows || [])
      setMaterialDeviation(deviationRes.data.rows || [])
      setSalesBySalon(salesRes.data.rows || [])
    } catch (error: any) {
      console.error(error)
      setOpsError(error?.response?.data?.detail || 'Nie udalo sie pobrac raportow operacyjnych.')
    } finally {
      setOpsLoading(false)
    }
  }

  useEffect(() => {
    fetchOperational()
  }, [fromDate, toDate, selectedSalonId])

  const renderLegacyReport = () => {
    if (selectedReport === 'forfaits_analysis') {
      return forfaits.map((row) => ({ Kod: row.bundle_code, Nazwa: row.bundle_name, Ilosc: row.count, Suma: row.revenue.toFixed(2) }))
    }
    if (selectedReport === 'forfaits_list') {
      return forfaitTx.map((row) => ({ Data: row.date_token, Kod: row.bundle_code, Nazwa: row.bundle_name, Cena: row.price.toFixed(2) }))
    }
    if (selectedReport === 'services_worker') {
      return servicesWorker.map((row) => ({ Pracownik: row.worker_name || row.worker_code, Kod: row.service_code, Usluga: row.service_name, Ilosc: row.qty, Suma: row.revenue.toFixed(2) }))
    }
    if (selectedReport === 'services_aggregate') {
      return servicesAgg.map((row) => ({ Kod: row.service_code, Usluga: row.service_name, Ilosc: row.qty, Suma: row.revenue.toFixed(2) }))
    }
    if (selectedReport === 'daily_ed1') {
      return daily.map((row) => ({ Data: row.date, Dzien: row.day_name, Brutto: row.gross_total.toFixed(2), Netto: row.net_total.toFixed(2), VAT: row.vat_total.toFixed(2), Paragony: row.tickets_count }))
    }
    if (selectedReport === 'monthly_ed1') {
      return monthly.map((row) => ({ Miesiac: row.month, Dni: row.days_count, Brutto: row.gross_total.toFixed(2), Netto: row.net_total.toFixed(2), VAT: row.vat_total.toFixed(2), Paragony: row.tickets_count }))
    }
    if (selectedReport === 'cashflow') {
      return cashflow.map((row) => ({ Data: row.date, Platnosc: row.payment_hint, Ilosc: row.count, Suma: row.revenue.toFixed(2) }))
    }
    return stat7.map((row) => ({ Kod: row.worker_code, Pracownik: row.worker_name, Suma: row.total.toFixed(2), A: row.payment_a, B: row.payment_b, C: row.payment_c }))
  }

  const materialRows = useMemo(() => {
    if (materialMode === 'by-staff') return materialByStaff.map((row) => ({ Pracownik: row.staff_name || row.staff_id || '-', Uslugi: row.services_count, Linie: row.lines_count, Ilosc: row.total_quantity.toFixed(2), Koszt: row.total_cost.toFixed(2) }))
    if (materialMode === 'by-service') return materialByService.map((row) => ({ Usluga: row.service_name || row.service_id || '-', Linie: row.lines_count, Ilosc: row.total_quantity.toFixed(2), Koszt: row.total_cost.toFixed(2) }))
    return materialDeviation.map((row) => ({ Pracownik: row.staff_name || row.staff_id || '-', Linie: row.lines_count, Plan: row.total_planned.toFixed(2), Faktycznie: row.total_actual.toFixed(2), Odchylenie: row.deviation.toFixed(2) }))
  }, [materialByService, materialByStaff, materialDeviation, materialMode])

  const salesTotal = useMemo(() => salesBySalon.reduce((sum, row) => sum + row.total_gross, 0), [salesBySalon])

  const renderGenericTable = (rows: Record<string, unknown>[]) => {
    if (!rows.length) return <Typography color="text.secondary">Brak danych dla wybranego zakresu.</Typography>
    const headers = Object.keys(rows[0])
    return (
      <TableContainer>
        <Table size="small" sx={TABLE_SX}>
          <TableHead>
            <TableRow>
              {headers.map((header) => <TableCell key={header}>{header}</TableCell>)}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, index) => (
              <TableRow key={index}>
                {headers.map((header) => <TableCell key={header}>{String(row[header] ?? '')}</TableCell>)}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    )
  }

  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={1.5}>
        <Typography variant="h4">Raporty</Typography>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel>Preset</InputLabel>
            <Select label="Preset" value={preset} onChange={(e) => setPreset(e.target.value as 'month_end' | 'custom')}>
              <MenuItem value="month_end">Miesiac + koniec</MenuItem>
              <MenuItem value="custom">Zakres reczny</MenuItem>
            </Select>
          </FormControl>
          <TextField size="small" type="date" label="Od" InputLabelProps={{ shrink: true }} value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
          <TextField size="small" type="date" label="Do" InputLabelProps={{ shrink: true }} value={toDate} onChange={(e) => setToDate(e.target.value)} />
          <FormControl size="small" sx={{ minWidth: 220 }}>
            <InputLabel>Salon</InputLabel>
            <Select label="Salon" value={selectedSalonId} onChange={(e) => setSelectedSalonId(e.target.value === '' ? '' : Number(e.target.value))}>
              <MenuItem value="">Wszystkie</MenuItem>
              {salons.map((salon) => <MenuItem key={salon.id} value={salon.id}>{salon.name}</MenuItem>)}
            </Select>
          </FormControl>
          <Button startIcon={<Refresh />} onClick={fetchOperational}>Odswiez</Button>
        </Stack>
      </Stack>

      <Tabs value={mainTab} onChange={(_, value) => setMainTab(value)}>
        <Tab value="legacy" label="Legacy" />
        <Tab value="materials" label="Materialy" />
        <Tab value="sales" label="Sprzedaz" />
      </Tabs>

      {legacyError && mainTab === 'legacy' && <Alert severity="error">{legacyError}</Alert>}
      {opsError && mainTab !== 'legacy' && <Alert severity="error">{opsError}</Alert>}
      {legacyLoading && mainTab === 'legacy' && <Alert severity="info">Ladowanie raportow legacy...</Alert>}
      {opsLoading && mainTab !== 'legacy' && <Alert severity="info">Ladowanie raportow operacyjnych...</Alert>}

      {mainTab === 'legacy' && (
        <Stack spacing={2}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={2}><Card><CardContent><Typography variant="overline">Salony</Typography><Typography variant="h4">{summary?.salons ?? 0}</Typography></CardContent></Card></Grid>
            <Grid item xs={12} md={2}><Card><CardContent><Typography variant="overline">Uslugi</Typography><Typography variant="h4">{summary?.services ?? 0}</Typography></CardContent></Card></Grid>
            <Grid item xs={12} md={2}><Card><CardContent><Typography variant="overline">Pakiety</Typography><Typography variant="h4">{summary?.bundles ?? 0}</Typography></CardContent></Card></Grid>
            <Grid item xs={12} md={3}><Card><CardContent><Typography variant="overline">Transakcje forfait</Typography><Typography variant="h4">{summary?.forfait_transactions ?? 0}</Typography></CardContent></Card></Grid>
            <Grid item xs={12} md={3}><Card><CardContent><Typography variant="overline">Fiche lines</Typography><Typography variant="h4">{summary?.fiche_lines ?? 0}</Typography></CardContent></Card></Grid>
          </Grid>

          <Card>
            <CardContent>
              <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" sx={{ mb: 2 }} spacing={1}>
                <FormControl size="small" sx={{ minWidth: 260 }}>
                  <InputLabel>Raport</InputLabel>
                  <Select label="Raport" value={selectedReport} onChange={(e) => setSelectedReport(e.target.value as ReportKey)}>
                    <MenuItem value="forfaits_analysis">Forfety - analiza</MenuItem>
                    <MenuItem value="forfaits_list">Forfety - lista</MenuItem>
                    <MenuItem value="services_worker">Uslugi wg pracownika</MenuItem>
                    <MenuItem value="services_aggregate">Uslugi - agregat</MenuItem>
                    <MenuItem value="daily_ed1">Dzienny</MenuItem>
                    <MenuItem value="monthly_ed1">Miesieczny</MenuItem>
                    <MenuItem value="cashflow">Cashflow</MenuItem>
                    <MenuItem value="stat7">Stat7</MenuItem>
                  </Select>
                </FormControl>
                <Button startIcon={<Download />} onClick={() => downloadCsv(`legacy-${selectedReport}.csv`, renderLegacyReport())}>Eksport CSV</Button>
              </Stack>
              {renderGenericTable(renderLegacyReport())}
            </CardContent>
          </Card>
        </Stack>
      )}

      {mainTab === 'materials' && (
        <Card>
          <CardContent>
            <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" sx={{ mb: 2 }} spacing={1}>
              <FormControl size="small" sx={{ minWidth: 240 }}>
                <InputLabel>Grupowanie</InputLabel>
                <Select label="Grupowanie" value={materialMode} onChange={(e) => setMaterialMode(e.target.value as MaterialMode)}>
                  <MenuItem value="by-staff">by-staff</MenuItem>
                  <MenuItem value="by-service">by-service</MenuItem>
                  <MenuItem value="deviations">deviations</MenuItem>
                </Select>
              </FormControl>
              <Button startIcon={<Download />} onClick={() => downloadCsv(`materials-${materialMode}.csv`, materialRows)}>Eksport CSV</Button>
            </Stack>
            {renderGenericTable(materialRows)}
          </CardContent>
        </Card>
      )}

      {mainTab === 'sales' && (
        <Stack spacing={2}>
          <Grid container spacing={2}>
            {salesBySalon.map((row) => (
              <Grid item xs={12} md={4} key={row.salon_id}>
                <Card>
                  <CardContent>
                    <Typography variant="overline">{row.salon_name || `Salon ${row.salon_id}`}</Typography>
                    <Typography variant="h5">{row.total_gross.toFixed(2)} PLN</Typography>
                    <Typography color="text.secondary">Transakcje: {row.transactions_count}</Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
            {!salesBySalon.length && (
              <Grid item xs={12}><Alert severity="info">Brak danych sprzedazowych dla wybranego zakresu.</Alert></Grid>
            )}
          </Grid>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Sprzedaz detaliczna wg salonu</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>Laczna sprzedaz: {salesTotal.toFixed(2)} PLN</Typography>
              <Box sx={{ width: '100%', height: 320 }}>
                <ResponsiveContainer>
                  <BarChart data={salesBySalon}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="salon_name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="total_gross" name="Total gross" fill="#3a6ea5" radius={[6, 6, 0, 0]} />
                    <Bar dataKey="transactions_count" name="Transactions" fill="#57a773" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
              <Stack direction="row" justifyContent="flex-end" sx={{ mt: 2 }}>
                <Button startIcon={<Download />} onClick={() => downloadCsv('sales-by-salon.csv', salesBySalon.map((row) => ({ Salon: row.salon_name || row.salon_id, Transactions: row.transactions_count, Linie: row.lines_count, TotalGross: row.total_gross.toFixed(2) })))}>Eksport CSV</Button>
              </Stack>
            </CardContent>
          </Card>
        </Stack>
      )}
    </Stack>
  )
}

export default ReportsPage
