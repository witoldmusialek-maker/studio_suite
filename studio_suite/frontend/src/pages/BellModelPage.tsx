import { useEffect, useMemo, useState } from 'react'
import {
  Alert,
  Card,
  CardContent,
  CircularProgress,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'

import { api } from '../services/api'

type ServicePriceRow = {
  service_id: number
  service_code: string
  service_name: string
  salon_id: number
  price: number
}

const BellModelPage = () => {
  const [query, setQuery] = useState('')
  const [rows, setRows] = useState<ServicePriceRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await api.get('/legacy/catalog')
      setRows(response.data.service_prices || [])
    } catch (err) {
      console.error(err)
      setError('Nie udalo sie pobrac cennika z bazy.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return rows
    return rows.filter((row) => `${row.service_code} ${row.service_name}`.toLowerCase().includes(q))
  }, [rows, query])

  const updatePrice = async (row: ServicePriceRow, nextPrice: number) => {
    const normalized = Math.round((Number(nextPrice) || 0) * 100) / 100
    try {
      await api.patch(`/legacy/catalog/services/${row.service_id}/price`, { price: normalized })
      setRows((prev) => prev.map((item) => (item.service_id === row.service_id ? { ...item, price: normalized } : item)))
    } catch (err) {
      console.error(err)
      setError('Nie udalo sie zapisac ceny uslugi.')
    }
  }

  return (
    <Stack spacing={2}>
      <Typography variant="h4">Cennik uslug (na bazie)</Typography>
      <TextField
        label="Szukaj uslugi (kod / nazwa)"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        size="small"
        sx={{ maxWidth: 420 }}
      />
      {error && <Alert severity="warning">{error}</Alert>}
      {loading && <CircularProgress size={28} />}
      {!loading && (
        <Card>
          <CardContent>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Kod</TableCell>
                  <TableCell>Usluga</TableCell>
                  <TableCell align="right">Cena PLN</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filtered.map((row) => (
                  <TableRow key={`${row.salon_id}-${row.service_id}`}>
                    <TableCell>{row.service_code}</TableCell>
                    <TableCell>{row.service_name}</TableCell>
                    <TableCell align="right" sx={{ minWidth: 150 }}>
                      <TextField
                        size="small"
                        type="number"
                        inputProps={{ step: 1, min: 0 }}
                        defaultValue={row.price.toFixed(2)}
                        onFocus={(event) => event.target.select()}
                        onBlur={(event) => updatePrice(row, Number(event.target.value))}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </Stack>
  )
}

export default BellModelPage
