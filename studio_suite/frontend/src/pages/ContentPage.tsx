import {
  Alert,
  Button,
  Card,
  CardContent,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useMemo, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useBooking } from '../contexts/BookingContext'

const ContentPage = () => {
  const { user } = useAuth()
  const { clients, appointments, salons, services, addClient } = useBooking()

  const [fullName, setFullName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [flash, setFlash] = useState('')
  const [selectedClientId, setSelectedClientId] = useState<number | null>(null)

  const visibleAppointments = useMemo(
    () => appointments.filter((appointment) => user?.assigned_salon_ids?.includes(appointment.salon_id)),
    [appointments, user],
  )

  const onAddClient = async () => {
    if (!fullName || !phone) {
      setFlash('Uzupelnij imie i nazwisko oraz telefon.')
      return
    }
    try {
      const created = await addClient({ full_name: fullName, phone, email })
      setFullName('')
      setPhone('')
      setEmail('')
      setSelectedClientId(created.id)
      setFlash('Klient dodany.')
    } catch {
      setFlash('Nie udalo sie dodac klienta.')
    }
  }

  const selectedClient = useMemo(
    () => clients.find((client) => client.id === selectedClientId) ?? null,
    [clients, selectedClientId],
  )

  const selectedClientHistory = useMemo(
    () => visibleAppointments
      .filter((appointment) => appointment.client_id === selectedClientId)
      .sort((a, b) => b.start_at.localeCompare(a.start_at)),
    [selectedClientId, visibleAppointments],
  )

  return (
    <Stack spacing={2}>
      <Typography variant="h4">Kartoteka klientow i historia</Typography>

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>Nowy klient</Typography>
          {flash && <Alert severity="info" sx={{ mb: 2 }}>{flash}</Alert>}
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <TextField label="Imie i nazwisko" fullWidth value={fullName} onChange={(e) => setFullName(e.target.value)} />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField label="Telefon" fullWidth value={phone} onChange={(e) => setPhone(e.target.value)} />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField label="Email" fullWidth value={email} onChange={(e) => setEmail(e.target.value)} />
            </Grid>
            <Grid item xs={12} md={2}>
              <Button variant="contained" fullWidth onClick={onAddClient}>Dodaj</Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {selectedClient ? (
        <Card>
          <CardContent>
            <Typography variant="h6">{selectedClient.full_name}</Typography>
            <Typography color="text.secondary">
              {selectedClient.phone} {selectedClient.email ? `| ${selectedClient.email}` : ''}
            </Typography>
            <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
              Historia wizyt
            </Typography>
            {selectedClientHistory.length === 0 ? (
              <Alert severity="info">Brak wizyt dla wybranego klienta.</Alert>
            ) : (
              <Table size="small" sx={{ mt: 1 }}>
                <TableHead>
                  <TableRow>
                    <TableCell>Data</TableCell>
                    <TableCell>Salon</TableCell>
                    <TableCell>Zabiegi</TableCell>
                    <TableCell align="right">Cena (snapshot)</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {selectedClientHistory.map((visit) => (
                    <TableRow key={visit.id}>
                      <TableCell>{visit.start_at.replace('T', ' ')}</TableCell>
                      <TableCell>{salons.find((s) => s.id === visit.salon_id)?.name}</TableCell>
                      <TableCell>
                        {visit.services
                          .map((id) => services.find((service) => service.id === id)?.name)
                          .filter(Boolean)
                          .join(', ')}
                      </TableCell>
                      <TableCell align="right">{visit.total_price_snapshot} PLN</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>Kartoteka klientow</Typography>
          {!clients.length ? (
            <Alert severity="info" sx={{ mb: 2 }}>
              Lista klientow jest pusta, bo w bazie nie ma jeszcze rekordow w tabeli `customers`.
            </Alert>
          ) : null}
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Klient</TableCell>
                <TableCell>Kontakt</TableCell>
                <TableCell align="right">Liczba wizyt</TableCell>
                <TableCell>Akcja</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {clients.map((client) => {
                const visitsCount = visibleAppointments.filter((appointment) => appointment.client_id === client.id).length
                return (
                  <TableRow
                    key={client.id}
                    hover
                    selected={selectedClientId === client.id}
                    onClick={() => setSelectedClientId(client.id)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <TableCell>{client.full_name}</TableCell>
                    <TableCell>{client.phone} {client.email ? `| ${client.email}` : ''}</TableCell>
                    <TableCell align="right">{visitsCount}</TableCell>
                    <TableCell>
                      <Button size="small" variant="outlined" onClick={() => setSelectedClientId(client.id)}>
                        Historia wizyt
                      </Button>
                    </TableCell>
                  </TableRow>
                )
              })}
              {!clients.length && (
                <TableRow>
                  <TableCell colSpan={4}>Brak klientow.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </Stack>
  )
}

export default ContentPage
