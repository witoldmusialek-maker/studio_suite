import {
  Alert,
  Button,
  Card,
  CardContent,
  Grid,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
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

  const visibleAppointments = useMemo(
    () => appointments.filter((appointment) => user?.assigned_salon_ids?.includes(appointment.salon_id)),
    [appointments, user],
  )

  const onAddClient = () => {
    if (!fullName || !phone) {
      setFlash('Uzupelnij imie i nazwisko oraz telefon.')
      return
    }

    addClient({ full_name: fullName, phone, email })
    setFullName('')
    setPhone('')
    setEmail('')
    setFlash('Klient dodany (demo).')
  }

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

      {clients.map((client) => {
        const history = visibleAppointments.filter((appointment) => appointment.client_id === client.id)
        return (
          <Card key={client.id}>
            <CardContent>
              <Typography variant="h6">{client.full_name}</Typography>
              <Typography color="text.secondary">{client.phone} {client.email ? `| ${client.email}` : ''}</Typography>
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
                  {history.map((visit) => (
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
            </CardContent>
          </Card>
        )
      })}
    </Stack>
  )
}

export default ContentPage
