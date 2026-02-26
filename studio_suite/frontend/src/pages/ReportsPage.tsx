import {
  Alert,
  Card,
  CardContent,
  CircularProgress,
  Grid,
  MenuItem,
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
import { useEffect, useState } from 'react'

import { api } from '../services/api'

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
type LegacyServiceWorkerRow = {
  worker_code: string
  worker_name: string
  service_code: string
  service_name: string
  qty: number
  revenue: number
}
type LegacyServiceAggregateRow = { service_code: string; service_name: string; qty: number; revenue: number }
type LegacyMonthlyRow = { month: string; days_count: number; gross_total: number; net_total: number; vat_total: number; tickets_count: number }
type LegacyDailyRow = { date: string; day_name: string; gross_total: number; net_total: number; vat_total: number; tickets_count: number }
type LegacyCashflowRow = { date: string; payment_hint: string; count: number; revenue: number }
type LegacyStat7WorkerRow = { worker_code: string; worker_name: string; total: number; payment_a: string; payment_b: string; payment_c: string }

type ReportKey =
  | 'forfaits_analysis'
  | 'forfaits_list'
  | 'services_worker'
  | 'services_aggregate'
  | 'daily_ed1'
  | 'monthly_ed1'
  | 'cashflow'
  | 'stat7'

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

const ReportsPage = () => {
  const [preset, setPreset] = useState<'month_end' | 'custom'>('month_end')
  const [fromDate, setFromDate] = useState('2025-10-01T00:00')
  const [toDate, setToDate] = useState('2026-02-28T23:59')
  const [selectedReport, setSelectedReport] = useState<ReportKey>('forfaits_analysis')

  const [legacyLoading, setLegacyLoading] = useState(false)
  const [legacyError, setLegacyError] = useState('')

  const [summary, setSummary] = useState<LegacySummary | null>(null)
  const [forfaits, setForfaits] = useState<LegacyForfaitRow[]>([])
  const [forfaitTx, setForfaitTx] = useState<LegacyForfaitTxRow[]>([])
  const [servicesWorker, setServicesWorker] = useState<LegacyServiceWorkerRow[]>([])
  const [servicesAgg, setServicesAgg] = useState<LegacyServiceAggregateRow[]>([])
  const [monthly, setMonthly] = useState<LegacyMonthlyRow[]>([])
  const [daily, setDaily] = useState<LegacyDailyRow[]>([])
  const [cashflow, setCashflow] = useState<LegacyCashflowRow[]>([])
  const [stat7, setStat7] = useState<LegacyStat7WorkerRow[]>([])

  const fromDateIso = fromDate.slice(0, 10)
  const toDateIso = toDate.slice(0, 10)

  useEffect(() => {
    const fetchLegacyReports = async () => {
      setLegacyLoading(true)
      setLegacyError('')
      try {
        const [summaryRes, forfaitsRes, forfaitTxRes, servicesWorkerRes, servicesAggRes, monthlyRes, dailyRes, cashflowRes, stat7Res] =
          await Promise.all([
            api.get('/legacy/reports/summary'),
            api.get('/legacy/reports/forfaits', { params: { from_date: fromDateIso, to_date: toDateIso } }),
            api.get('/legacy/reports/forfait-transactions', { params: { from_date: fromDateIso, to_date: toDateIso } }),
            api.get('/legacy/reports/services-by-worker', { params: { from_date: fromDateIso, to_date: toDateIso } }),
            api.get('/legacy/reports/services-aggregate', { params: { from_date: fromDateIso, to_date: toDateIso } }),
            api.get('/legacy/reports/monthly-summary'),
            api.get('/legacy/reports/daily-summary', { params: { from_date: fromDateIso, to_date: toDateIso } }),
            api.get('/legacy/reports/cashflow', { params: { from_date: fromDateIso, to_date: toDateIso } }),
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
  }, [fromDateIso, toDateIso])

  const renderReport = () => {
    if (selectedReport === 'forfaits_analysis') {
      return (
        <TableContainer>
          <Table size="small" sx={TABLE_SX}>
            <TableHead>
              <TableRow>
                <TableCell>Kod forfaitu</TableCell>
                <TableCell>Nazwa</TableCell>
                <TableCell align="right">Ilosc</TableCell>
                <TableCell align="right">Suma PLN</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {forfaits.map((row, i) => (
                <TableRow key={`${row.bundle_code}-${i}`}>
                  <TableCell>{row.bundle_code}</TableCell>
                  <TableCell>{row.bundle_name}</TableCell>
                  <TableCell align="right">{row.count}</TableCell>
                  <TableCell align="right">{row.revenue.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )
    }
    if (selectedReport === 'forfaits_list') {
      return (
        <TableContainer>
          <Table size="small" sx={TABLE_SX}>
            <TableHead>
              <TableRow>
                <TableCell>Data</TableCell>
                <TableCell>Kod</TableCell>
                <TableCell>Nazwa forfaitu</TableCell>
                <TableCell align="right">Cena PLN</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {forfaitTx.map((row, i) => (
                <TableRow key={`${row.date_token}-${row.bundle_code}-${i}`}>
                  <TableCell>{row.date_token}</TableCell>
                  <TableCell>{row.bundle_code}</TableCell>
                  <TableCell>{row.bundle_name}</TableCell>
                  <TableCell align="right">{row.price.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )
    }
    if (selectedReport === 'services_worker') {
      return (
        <TableContainer>
          <Table size="small" sx={TABLE_SX}>
            <TableHead>
              <TableRow>
                <TableCell>Pracownik</TableCell>
                <TableCell>Kod uslugi</TableCell>
                <TableCell>Usluga</TableCell>
                <TableCell align="right">Ilosc</TableCell>
                <TableCell align="right">Suma PLN</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {servicesWorker.map((row, i) => (
                <TableRow key={`${row.worker_code}-${row.service_code}-${i}`}>
                  <TableCell>{row.worker_name || row.worker_code}</TableCell>
                  <TableCell>{row.service_code}</TableCell>
                  <TableCell>{row.service_name}</TableCell>
                  <TableCell align="right">{row.qty}</TableCell>
                  <TableCell align="right">{row.revenue.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )
    }
    if (selectedReport === 'services_aggregate') {
      return (
        <TableContainer>
          <Table size="small" sx={TABLE_SX}>
            <TableHead>
              <TableRow>
                <TableCell>Kod uslugi</TableCell>
                <TableCell>Usluga</TableCell>
                <TableCell align="right">Ilosc</TableCell>
                <TableCell align="right">Suma PLN</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {servicesAgg.map((row, i) => (
                <TableRow key={`${row.service_code}-${i}`}>
                  <TableCell>{row.service_code}</TableCell>
                  <TableCell>{row.service_name}</TableCell>
                  <TableCell align="right">{row.qty}</TableCell>
                  <TableCell align="right">{row.revenue.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )
    }
    if (selectedReport === 'daily_ed1') {
      return (
        <TableContainer>
          <Table size="small" sx={TABLE_SX}>
            <TableHead>
              <TableRow>
                <TableCell>Data</TableCell>
                <TableCell>Dzien</TableCell>
                <TableCell align="right">Brutto</TableCell>
                <TableCell align="right">Netto</TableCell>
                <TableCell align="right">VAT</TableCell>
                <TableCell align="right">Paragony</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {daily.map((row, i) => (
                <TableRow key={`${row.date}-${i}`}>
                  <TableCell>{row.date}</TableCell>
                  <TableCell>{row.day_name}</TableCell>
                  <TableCell align="right">{row.gross_total.toFixed(2)}</TableCell>
                  <TableCell align="right">{row.net_total.toFixed(2)}</TableCell>
                  <TableCell align="right">{row.vat_total.toFixed(2)}</TableCell>
                  <TableCell align="right">{row.tickets_count}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )
    }
    if (selectedReport === 'monthly_ed1') {
      return (
        <TableContainer>
          <Table size="small" sx={TABLE_SX}>
            <TableHead>
              <TableRow>
                <TableCell>Miesiac</TableCell>
                <TableCell align="right">Dni</TableCell>
                <TableCell align="right">Brutto</TableCell>
                <TableCell align="right">Netto</TableCell>
                <TableCell align="right">VAT</TableCell>
                <TableCell align="right">Paragony</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {monthly.map((row) => (
                <TableRow key={row.month}>
                  <TableCell>{row.month}</TableCell>
                  <TableCell align="right">{row.days_count}</TableCell>
                  <TableCell align="right">{row.gross_total.toFixed(2)}</TableCell>
                  <TableCell align="right">{row.net_total.toFixed(2)}</TableCell>
                  <TableCell align="right">{row.vat_total.toFixed(2)}</TableCell>
                  <TableCell align="right">{row.tickets_count}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )
    }
    if (selectedReport === 'cashflow') {
      return (
        <TableContainer>
          <Table size="small" sx={TABLE_SX}>
            <TableHead>
              <TableRow>
                <TableCell>Data</TableCell>
                <TableCell>Platnosc</TableCell>
                <TableCell align="right">Ilosc</TableCell>
                <TableCell align="right">Suma PLN</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {cashflow.map((row, i) => (
                <TableRow key={`${row.date}-${row.payment_hint}-${i}`}>
                  <TableCell>{row.date}</TableCell>
                  <TableCell>{row.payment_hint}</TableCell>
                  <TableCell align="right">{row.count}</TableCell>
                  <TableCell align="right">{row.revenue.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )
    }
    return (
      <TableContainer>
        <Table size="small" sx={TABLE_SX}>
          <TableHead>
            <TableRow>
              <TableCell>Pracownik</TableCell>
              <TableCell align="right">Suma PLN</TableCell>
              <TableCell>Forma A</TableCell>
              <TableCell>Forma B</TableCell>
              <TableCell>Forma C</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {stat7.map((row) => (
              <TableRow key={`${row.worker_code}-${row.worker_name}`}>
                <TableCell>{row.worker_name || row.worker_code}</TableCell>
                <TableCell align="right">{row.total.toFixed(2)}</TableCell>
                <TableCell>{row.payment_a}</TableCell>
                <TableCell>{row.payment_b}</TableCell>
                <TableCell>{row.payment_c}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    )
  }

  const selectedCount =
    selectedReport === 'forfaits_analysis'
      ? forfaits.length
      : selectedReport === 'forfaits_list'
        ? forfaitTx.length
        : selectedReport === 'services_worker'
          ? servicesWorker.length
          : selectedReport === 'services_aggregate'
            ? servicesAgg.length
            : selectedReport === 'daily_ed1'
              ? daily.length
              : selectedReport === 'monthly_ed1'
                ? monthly.length
                : selectedReport === 'cashflow'
                  ? cashflow.length
                  : stat7.length

  return (
    <Stack spacing={2}>
      <Typography variant="h4">Raporty legacy</Typography>

      <Card>
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={2}>
              <TextField
                select
                fullWidth
                label="Tryb dat"
                value={preset}
                onChange={(e) => {
                  const value = e.target.value as 'month_end' | 'custom'
                  setPreset(value)
                  if (value === 'month_end') {
                    setFromDate('2025-10-01T00:00')
                    setToDate('2026-02-28T23:59')
                  }
                }}
              >
                <MenuItem value="month_end">Koniec miesiaca</MenuItem>
                <MenuItem value="custom">Niestandardowy</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} md={2}>
              <TextField label="Od" type="datetime-local" fullWidth value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
            </Grid>
            <Grid item xs={12} md={2}>
              <TextField label="Do" type="datetime-local" fullWidth value={toDate} onChange={(e) => setToDate(e.target.value)} />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                select
                fullWidth
                label="Wybierz raport"
                value={selectedReport}
                onChange={(e) => setSelectedReport(e.target.value as ReportKey)}
              >
                <MenuItem value="daily_ed1">ED1: Raport dzienny</MenuItem>
                <MenuItem value="forfaits_analysis">ED4: Analiza forfaitow</MenuItem>
                <MenuItem value="forfaits_list">ED5: Lista forfaitow</MenuItem>
                <MenuItem value="services_aggregate">ED6: Uslugi agregat</MenuItem>
                <MenuItem value="stat7">ED7: STAT7 pracownicy</MenuItem>
                <MenuItem value="services_worker">ED8: Uslugi per pracownik</MenuItem>
                <MenuItem value="monthly_ed1">Compte rendu du mois</MenuItem>
                <MenuItem value="cashflow">Platnosci dzienne</MenuItem>
              </TextField>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {legacyError && <Alert severity="warning">{legacyError}</Alert>}
      {legacyLoading && <CircularProgress size={28} />}
      {!legacyLoading && !legacyError && selectedCount === 0 && (
        <Alert severity="info">Brak danych w wybranym zakresie dat. Zmien filtr dat i sprobuj ponownie.</Alert>
      )}

      {summary && (
        <Grid container spacing={2}>
          <Grid item xs={6} md={2}>
            <Card>
              <CardContent>
                <Typography variant="overline">Salony</Typography>
                <Typography variant="h6">{summary.salons}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} md={2}>
            <Card>
              <CardContent>
                <Typography variant="overline">Uslugi</Typography>
                <Typography variant="h6">{summary.services}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} md={2}>
            <Card>
              <CardContent>
                <Typography variant="overline">Forfety</Typography>
                <Typography variant="h6">{summary.bundles}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="overline">Transakcje forfaitow</Typography>
                <Typography variant="h6">{summary.forfait_transactions}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="overline">Wiersze FICHE</Typography>
                <Typography variant="h6">{summary.fiche_lines}</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <Card sx={{ border: '1px solid #9bb2cd', background: 'linear-gradient(180deg, #e7f0fa 0%, #d4e3f2 100%)' }}>
        <CardContent>
          {renderReport()}
        </CardContent>
      </Card>
    </Stack>
  )
}

export default ReportsPage
