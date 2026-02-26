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
  PerformedServiceLine,
} from '../types'
import { legacyBundles, legacyPriceListItems, legacyServices } from './legacyImportedCatalog'
import {
  legacyAppointments,
  legacyClients,
  legacyPerformedServiceLines,
  legacyResources,
} from './legacyOperationalSeed'

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
  { id: 4, code: 'RECEPCJONISTA', name: 'Recepcjonista' },
]

export const mockResources: StaffResource[] = [
  ...legacyResources,
  { id: 5001, salon_id: 2, name: 'Wiktoria Demo', role_ids: [1, 3] },
]

export const mockClients: ClientCard[] = legacyClients

export const mockServices: ServiceCatalogItem[] = legacyServices

export const mockPriceListItems: PriceListItem[] = [
  ...legacyPriceListItems,
  ...legacyPriceListItems.map((row, index) => ({
    ...row,
    id: legacyPriceListItems.length + index + 1,
    salon_id: 2,
  })),
]

export const mockBundles: BundleCatalog[] = legacyBundles

export const mockColorProducts: ColorProduct[] = [
  { id: 1, code: 'C-7.1', name: 'Popielaty blond 7.1', brand: 'Luma Color' },
  { id: 2, code: 'C-6.3', name: 'Ciemny blond zloto 6.3', brand: 'Luma Color' },
]

export const mockAppointments: Appointment[] = legacyAppointments

export const mockPerformedServiceLines: PerformedServiceLine[] = legacyPerformedServiceLines
