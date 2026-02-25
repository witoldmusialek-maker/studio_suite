import { Card, CardContent, Chip, Stack, Typography } from '@mui/material'
import { mockBundles, mockServices } from '../mocks/bookingData'

const SoundsPage = () => {
  return (
    <Stack spacing={2}>
      <Typography variant="h4">Pakiety (forfety)</Typography>
      {mockBundles.map((bundle) => (
        <Card key={bundle.id}>
          <CardContent>
            <Typography variant="h6">{bundle.code} - {bundle.name}</Typography>
            <Typography color="text.secondary">Cena pakietu: {bundle.price} PLN</Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ mt: 1 }}>
              {bundle.items.map((item, index) => {
                const service = mockServices.find((s) => s.id === item.service_id)
                const label = item.override_price
                  ? `${service?.name} (override: ${item.override_price} PLN)`
                  : `${service?.name} (cena standard)`
                return <Chip key={`${bundle.id}-${index}`} label={label} />
              })}
            </Stack>
          </CardContent>
        </Card>
      ))}
    </Stack>
  )
}

export default SoundsPage
