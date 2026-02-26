import { Card, CardContent, Chip, Grid, Stack, Typography } from '@mui/material'
import { mockResources, mockSalons, mockStaffRoles } from '../mocks/bookingData'

const GroupsPage = () => {
  return (
    <Stack spacing={2}>
      <Typography variant="h4">Salony i zasoby</Typography>
      <Grid container spacing={2}>
        {mockSalons.map((salon) => (
          <Grid item xs={12} md={6} key={salon.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">{salon.name}</Typography>
                <Typography color="text.secondary" sx={{ mb: 1 }}>{salon.city}</Typography>
                <Stack spacing={1}>
                  {mockResources.filter((resource) => resource.salon_id === salon.id).map((resource) => (
                    <Card key={resource.id} variant="outlined" sx={{ p: 1 }}>
                      <Typography sx={{ fontWeight: 700 }}>{resource.name}</Typography>
                      <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                        {resource.role_ids.map((roleId) => (
                          <Chip
                            key={roleId}
                            size="small"
                            label={mockStaffRoles.find((role) => role.id === roleId)?.name ?? roleId}
                          />
                        ))}
                      </Stack>
                    </Card>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Stack>
  )
}

export default GroupsPage
