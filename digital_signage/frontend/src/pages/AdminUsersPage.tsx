import { Card, CardContent, Chip, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material'
import { mockSalons, mockUsers } from '../mocks/bookingData'

const AdminUsersPage = () => {
  return (
    <Stack spacing={2}>
      <Typography variant="h4">Uzytkownicy i uprawnienia</Typography>
      <Card>
        <CardContent>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Login</TableCell>
                <TableCell>Imie i nazwisko</TableCell>
                <TableCell>Rola systemowa</TableCell>
                <TableCell>Zakres salonow</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {mockUsers.map((user) => (
                <TableRow key={user.id}>
                  <TableCell>{user.username}</TableCell>
                  <TableCell>{user.full_name}</TableCell>
                  <TableCell><Chip size="small" label={user.role} /></TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={1} flexWrap="wrap">
                      {(user.assigned_salon_ids ?? []).map((salonId) => (
                        <Chip
                          key={`${user.id}-${salonId}`}
                          size="small"
                          variant="outlined"
                          label={mockSalons.find((salon) => salon.id === salonId)?.name ?? salonId}
                        />
                      ))}
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </Stack>
  )
}

export default AdminUsersPage
