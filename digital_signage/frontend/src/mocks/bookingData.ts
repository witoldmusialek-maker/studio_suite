import {
  Appointment,
  BundleCatalog,
  ClientCard,
  ColorProduct,
  PriceListItem,
  Salon,
  ServiceCatalogItem,
  StaffResource,
  StaffRole,
  User,
} from '../types'

export const mockUsers: User[] = [
  { id: 1, username: 'admin', full_name: 'Anna Admin', role: 'admin', assigned_salon_ids: [1, 2] },
  { id: 2, username: 'manager', full_name: 'Marek Manager', role: 'manager', assigned_salon_ids: [1, 2] },
  { id: 3, username: 'recepcja', full_name: 'Roksana Recepcja', role: 'receptionist', assigned_salon_ids: [1] },
]

export const mockSalons: Salon[] = [
  { id: 1, name: 'Studio Glow - Centrum', city: 'Warszawa' },
  { id: 2, name: 'Studio Glow - Mokotow', city: 'Warszawa' },
]

export const mockStaffRoles: StaffRole[] = [
  { id: 1, code: 'FRYZJER', name: 'Fryzjer' },
  { id: 2, code: 'POMOCNIK', name: 'Pomocnik' },
  { id: 3, code: 'MANICURZYSTKA', name: 'Manicurzystka' },
]

export const mockResources: StaffResource[] = [
  { id: 1, salon_id: 1, name: 'Karolina', role_ids: [1] },
  { id: 2, salon_id: 1, name: 'Natalia', role_ids: [2] },
  { id: 3, salon_id: 2, name: 'Wiktoria', role_ids: [1, 3] },
]

export const mockClients: ClientCard[] = [
  { id: 1, full_name: 'Ewa Mazur', phone: '+48 500 111 222', email: 'ewa@example.com' },
  { id: 2, full_name: 'Monika Bialek', phone: '+48 500 222 333' },
  { id: 3, full_name: 'Alicja Wrona', phone: '+48 500 333 444' },
]

export const mockServices: ServiceCatalogItem[] = [
  { id: 1, code: '01', name: 'Strzyzenie', duration_minutes: 45 },
  { id: 2, code: '02', name: 'Mycie', duration_minutes: 15 },
  { id: 3, code: '03', name: 'Koloryzacja', duration_minutes: 90 },
  { id: 4, code: '04', name: 'Manicure hybrydowy', duration_minutes: 60 },
]

export const mockPriceListItems: PriceListItem[] = [
  { id: 1, salon_id: 1, service_id: 1, price: 150 },
  { id: 2, salon_id: 1, service_id: 2, price: 35 },
  { id: 3, salon_id: 1, service_id: 3, price: 260 },
  { id: 4, salon_id: 2, service_id: 1, price: 170 },
  { id: 5, salon_id: 2, service_id: 2, price: 40 },
  { id: 6, salon_id: 2, service_id: 4, price: 140 },
]

export const mockBundles: BundleCatalog[] = [
  {
    id: 1,
    salon_id: 1,
    code: 'P01',
    name: 'Pakiet metamorfoza',
    price: 360,
    items: [
      { service_id: 2, override_price: 20 },
      { service_id: 1 },
      { service_id: 3, override_price: 190 },
    ],
  },
]

export const mockColorProducts: ColorProduct[] = [
  { id: 1, code: 'C-7.1', name: 'Popielaty blond 7.1', brand: 'Luma Color' },
  { id: 2, code: 'C-6.3', name: 'Ciemny blond zloto 6.3', brand: 'Luma Color' },
]

export const mockAppointments: Appointment[] = [
  {
    id: 1,
    salon_id: 1,
    client_id: 1,
    start_at: '2026-02-26T09:00:00',
    end_at: '2026-02-26T10:30:00',
    status: 'confirmed',
    resources: [1, 2],
    services: [2, 1],
    total_price_snapshot: 185,
  },
  {
    id: 2,
    salon_id: 1,
    client_id: 2,
    start_at: '2026-02-26T11:00:00',
    end_at: '2026-02-26T12:30:00',
    status: 'planned',
    resources: [1],
    services: [3],
    bundle_id: 1,
    total_price_snapshot: 360,
  },
  {
    id: 3,
    salon_id: 2,
    client_id: 3,
    start_at: '2026-02-26T13:00:00',
    end_at: '2026-02-26T14:00:00',
    status: 'done',
    resources: [3],
    services: [4],
    total_price_snapshot: 140,
  },
]
