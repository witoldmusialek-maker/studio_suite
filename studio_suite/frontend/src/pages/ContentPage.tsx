import {
  Alert,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TableContainer,
  TextField,
  Typography,
} from '@mui/material'
import { useMemo, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useBooking } from '../contexts/BookingContext'

const ContentPage = () => {
  const { user } = useAuth()
  const { clients, appointments, salons, services, addClient, updateClient, deleteClient } = useBooking()

  const [fullName, setFullName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [flash, setFlash] = useState('')
  const [search, setSearch] = useState('')
  const [selectedClientId, setSelectedClientId] = useState<number | null>(null)
  const [editOpen, setEditOpen] = useState(false)
  const [editingClientId, setEditingClientId] = useState<number | null>(null)
  const [editFullName, setEditFullName] = useState('')
  const [editPhone, setEditPhone] = useState('')
  const [editEmail, setEditEmail] = useState('')

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

  const openEditClient = (clientId: number) => {
    const row = clients.find((client) => client.id === clientId)
    if (!row) return
    setEditingClientId(row.id)
    setEditFullName(row.full_name || '')
    setEditPhone(row.phone || '')
    setEditEmail(row.email || '')
    setEditOpen(true)
  }

  const saveClientEdit = async () => {
    if (!editingClientId) return
    if (!editFullName.trim() || !editPhone.trim()) {
      setFlash('Imie i nazwisko oraz telefon sa wymagane.')
      return
    }
    try {
      const updated = await updateClient({
        client_id: editingClientId,
        full_name: editFullName.trim(),
        phone: editPhone.trim(),
        email: editEmail.trim() || '',
      })
      setSelectedClientId(updated.id)
      setEditOpen(false)
      setFlash('Dane klienta zaktualizowane.')
    } catch {
      setFlash('Nie udalo sie zaktualizowac klienta.')
    }
  }

  const removeClient = async (clientId: number) => {
    const row = clients.find((client) => client.id === clientId)
    if (!row) return
    if (!window.confirm(`Usunac klienta ${row.full_name}?`)) return
    try {
      await deleteClient(clientId)
      if (selectedClientId === clientId) {
        setSelectedClientId(null)
      }
      setFlash('Klient usuniety.')
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setFlash(detail || 'Nie udalo sie usunac klienta.')
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

  const filteredClients = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return clients
    return clients.filter((client) => {
      const haystack = `${client.full_name || ''} ${client.phone || ''} ${client.email || ''}`.toLowerCase()
      return haystack.includes(q)
    })
  }, [clients, search])

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
            <Stack direction={{ xs: 'column', md: 'row' }} justifyContent='space-between' spacing={1}>
              <Stack spacing={0.25}>
                <Typography variant="h6">{selectedClient.full_name}</Typography>
                <Typography color="text.secondary">
                  {selectedClient.phone} {selectedClient.email ? `| ${selectedClient.email}` : ''}
                </Typography>
              </Stack>
              <Stack direction='row' spacing={1}>
                <Button
                  size='small'
                  variant='outlined'
                  onClick={() => openEditClient(selectedClient.id)}
                >
                  Edytuj klienta
                </Button>
                <Button
                  size='small'
                  variant='outlined'
                  color='error'
                  onClick={() => removeClient(selectedClient.id)}
                >
                  Usun
                </Button>
              </Stack>
            </Stack>
            <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
              Historia wizyt
            </Typography>
            {selectedClientHistory.length === 0 ? (
              <Alert severity="info">Brak wizyt dla wybranego klienta.</Alert>
            ) : (
              <TableContainer sx={{ mt: 1 }}>
              <Table size="small">
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
              </TableContainer>
            )}
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardContent>
          <Stack direction={{ xs: 'column', md: 'row' }} justifyContent='space-between' spacing={1} sx={{ mb: 1 }}>
            <Typography variant="h6">Kartoteka klientow</Typography>
            <TextField
              size='small'
              label='Szukaj klienta'
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              sx={{ minWidth: 280 }}
            />
          </Stack>
          {!clients.length ? (
            <Alert severity="info" sx={{ mb: 2 }}>
              Lista klientow jest pusta, bo w bazie nie ma jeszcze rekordow w tabeli `customers`.
            </Alert>
          ) : null}
          <TableContainer>
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
              {filteredClients.map((client) => {
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
                      <Stack direction='row' spacing={1}>
                        <Button size="small" variant="outlined" onClick={() => setSelectedClientId(client.id)}>
                          Historia
                        </Button>
                        <Button size="small" variant="outlined" onClick={() => openEditClient(client.id)}>
                          Edytuj
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          color='error'
                          onClick={(e) => {
                            e.stopPropagation()
                            void removeClient(client.id)
                          }}
                        >
                          Usun
                        </Button>
                      </Stack>
                    </TableCell>
                  </TableRow>
                )
              })}
              {!filteredClients.length && (
                <TableRow>
                  <TableCell colSpan={4}>Brak klientow dla podanego filtra.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
          </TableContainer>
        </CardContent>
      </Card>

      <Dialog open={editOpen} onClose={() => setEditOpen(false)} fullWidth maxWidth='sm'>
        <DialogTitle>Edytuj klienta</DialogTitle>
        <DialogContent>
          <Stack spacing={1.5} sx={{ mt: 1 }}>
            <TextField
              label='Imie i nazwisko'
              size='small'
              value={editFullName}
              onChange={(e) => setEditFullName(e.target.value)}
            />
            <TextField
              label='Telefon'
              size='small'
              value={editPhone}
              onChange={(e) => setEditPhone(e.target.value)}
            />
            <TextField
              label='Email'
              size='small'
              value={editEmail}
              onChange={(e) => setEditEmail(e.target.value)}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditOpen(false)}>Anuluj</Button>
          <Button
            variant='contained'
            onClick={saveClientEdit}
            disabled={!editFullName.trim() || !editPhone.trim()}
          >
            Zapisz
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}

export default ContentPage
