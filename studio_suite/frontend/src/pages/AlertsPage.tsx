import { Card, CardContent, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material'
import { mockColorProducts } from '../mocks/bookingData'

const AlertsPage = () => {
  return (
    <Stack spacing={2}>
      <Typography variant="h4">Baza farb i kolorow</Typography>
      <Card>
        <CardContent>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Kod</TableCell>
                <TableCell>Nazwa</TableCell>
                <TableCell>Marka</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {mockColorProducts.map((product) => (
                <TableRow key={product.id}>
                  <TableCell>{product.code}</TableCell>
                  <TableCell>{product.name}</TableCell>
                  <TableCell>{product.brand}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </Stack>
  )
}

export default AlertsPage
