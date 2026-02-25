import React, { createContext, useContext, useMemo, useState } from 'react'
import {
  mockAppointments,
  mockBundles,
  mockClients,
  mockColorProducts,
  mockPriceListItems,
  mockResources,
  mockSalons,
  mockServices,
  mockStaffRoles,
} from '../mocks/bookingData'
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
} from '../types'

type CreateClientInput = {
  full_name: string
  phone: string
  email?: string
}

type CreateAppointmentInput = {
  salon_id: number
  client_id: number
  start_at: string
  end_at: string
  resources: number[]
  services: number[]
  bundle_id?: number
}

type BookingContextType = {
  salons: Salon[]
  staffRoles: StaffRole[]
  resources: StaffResource[]
  clients: ClientCard[]
  services: ServiceCatalogItem[]
  priceListItems: PriceListItem[]
  bundles: BundleCatalog[]
  colorProducts: ColorProduct[]
  appointments: Appointment[]
  addClient: (input: CreateClientInput) => ClientCard
  addAppointment: (input: CreateAppointmentInput) => Appointment
  estimateTotal: (salonId: number, serviceIds: number[], bundleId?: number) => number
}

const BookingContext = createContext<BookingContextType | undefined>(undefined)

const resolveServicePrice = (salonId: number, serviceId: number, list: PriceListItem[]) =>
  list.find((item) => item.salon_id === salonId && item.service_id === serviceId)?.price ?? 0

export const BookingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [clients, setClients] = useState<ClientCard[]>(mockClients)
  const [appointments, setAppointments] = useState<Appointment[]>(mockAppointments)

  const estimateTotal = (salonId: number, serviceIds: number[], bundleId?: number) => {
    if (bundleId) {
      const bundle = mockBundles.find((item) => item.id === bundleId)
      return bundle?.price ?? 0
    }
    return serviceIds.reduce((sum, serviceId) => sum + resolveServicePrice(salonId, serviceId, mockPriceListItems), 0)
  }

  const addClient = (input: CreateClientInput) => {
    const newClient: ClientCard = {
      id: clients.reduce((maxId, client) => Math.max(maxId, client.id), 0) + 1,
      full_name: input.full_name,
      phone: input.phone,
      email: input.email,
    }
    setClients((prev) => [...prev, newClient])
    return newClient
  }

  const addAppointment = (input: CreateAppointmentInput) => {
    const total = estimateTotal(input.salon_id, input.services, input.bundle_id)
    const next: Appointment = {
      id: appointments.reduce((maxId, item) => Math.max(maxId, item.id), 0) + 1,
      salon_id: input.salon_id,
      client_id: input.client_id,
      start_at: input.start_at,
      end_at: input.end_at,
      status: 'planned',
      resources: input.resources,
      services: input.services,
      bundle_id: input.bundle_id,
      total_price_snapshot: total,
    }

    setAppointments((prev) => [...prev, next])
    return next
  }

  const value = useMemo(
    () => ({
      salons: mockSalons,
      staffRoles: mockStaffRoles,
      resources: mockResources,
      clients,
      services: mockServices,
      priceListItems: mockPriceListItems,
      bundles: mockBundles,
      colorProducts: mockColorProducts,
      appointments,
      addClient,
      addAppointment,
      estimateTotal,
    }),
    [appointments, clients],
  )

  return <BookingContext.Provider value={value}>{children}</BookingContext.Provider>
}

export const useBooking = () => {
  const context = useContext(BookingContext)
  if (!context) throw new Error('useBooking must be used within BookingProvider')
  return context
}
