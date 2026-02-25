import { Card, CardContent, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material'
import { mockPriceListItems, mockSalons, mockServices } from '../mocks/bookingData'

const BellModelPage = () => {
  return (
    <Stack spacing={2}>
      <Typography variant="h4">Cennik uslug (per salon)</Typography>
      {mockSalons.map((salon) => (
        <Card key={salon.id}>
          <CardContent>
            <Typography variant="h6">{salon.name}</Typography>
            <Table size="small" sx={{ mt: 1 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Kod</TableCell>
                  <TableCell>Usluga</TableCell>
                  <TableCell align="right">Cena</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {mockPriceListItems.filter((item) => item.salon_id === salon.id).map((item) => {
                  const service = mockServices.find((service) => service.id === item.service_id)
                  return (
                    <TableRow key={item.id}>
                      <TableCell>{service?.code}</TableCell>
                      <TableCell>{service?.name}</TableCell>
                      <TableCell align="right">{item.price} PLN</TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ))}
    </Stack>
  )
}

export default BellModelPage
