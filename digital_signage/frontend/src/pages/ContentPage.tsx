import { Card, CardContent, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material'
import { mockAppointments, mockClients, mockSalons, mockServices } from '../mocks/bookingData'

const ContentPage = () => {
  return (
    <Stack spacing={2}>
      <Typography variant="h4">Kartoteka klientow i historia</Typography>
      {mockClients.map((client) => {
        const history = mockAppointments.filter((appointment) => appointment.client_id === client.id)
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
                      <TableCell>{mockSalons.find((s) => s.id === visit.salon_id)?.name}</TableCell>
                      <TableCell>{visit.services.map((id) => mockServices.find((service) => service.id === id)?.name).filter(Boolean).join(', ')}</TableCell>
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
