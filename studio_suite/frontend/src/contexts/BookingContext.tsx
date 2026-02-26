import React, { createContext, useContext, useMemo, useState } from 'react'
import {
  mockAppointments,
  mockBundles,
  mockClients,
  mockColorProducts,
  mockPerformedServiceLines,
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
  PerformedServiceLine,
  PriceListItem,
  Salon,
  ServiceCatalogItem,
  StaffResource,
  StaffRole,
  UpdateBundleItemPriceInput,
  UpdateBundlePriceInput,
  UpdatePriceInput,
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

type CompleteAppointmentLineInput = {
  service_id: number
  worker_id: number
  worker_role_id: number
  price_snapshot: number
  color_product_id?: number
}

type CompleteAppointmentInput = {
  appointment_id: number
  performed_at: string
  lines: CompleteAppointmentLineInput[]
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
  performedServiceLines: PerformedServiceLine[]
  addClient: (input: CreateClientInput) => ClientCard
  addAppointment: (input: CreateAppointmentInput) => Appointment
  completeAppointment: (input: CompleteAppointmentInput) => void
  estimateTotal: (salonId: number, serviceIds: number[], bundleId?: number) => number
  getAppointmentRevenue: (appointmentId: number) => number
  updateServicePrice: (input: UpdatePriceInput) => void
  updateBundlePrice: (input: UpdateBundlePriceInput) => void
  updateBundleItemPrice: (input: UpdateBundleItemPriceInput) => void
}

const BookingContext = createContext<BookingContextType | undefined>(undefined)
const PRICE_LIST_STORAGE_KEY = 'booking_price_list_v1'
const BUNDLE_STORAGE_KEY = 'booking_bundle_list_v1'

const resolveServicePrice = (salonId: number, serviceId: number, list: PriceListItem[]) =>
  list.find((item) => item.salon_id === salonId && item.service_id === serviceId)?.price ?? 0

export const BookingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [clients, setClients] = useState<ClientCard[]>(mockClients)
  const [appointments, setAppointments] = useState<Appointment[]>(mockAppointments)
  const [performedServiceLines, setPerformedServiceLines] = useState<PerformedServiceLine[]>(mockPerformedServiceLines)
  const [priceListItems, setPriceListItems] = useState<PriceListItem[]>(() => {
    try {
      const raw = localStorage.getItem(PRICE_LIST_STORAGE_KEY)
      if (!raw) return mockPriceListItems
      const parsed = JSON.parse(raw) as PriceListItem[]
      return Array.isArray(parsed) && parsed.length > 0 ? parsed : mockPriceListItems
    } catch {
      return mockPriceListItems
    }
  })
  const [bundles, setBundles] = useState<BundleCatalog[]>(() => {
    try {
      const raw = localStorage.getItem(BUNDLE_STORAGE_KEY)
      if (!raw) return mockBundles
      const parsed = JSON.parse(raw) as BundleCatalog[]
      return Array.isArray(parsed) && parsed.length > 0 ? parsed : mockBundles
    } catch {
      return mockBundles
    }
  })

  const estimateTotal = (salonId: number, serviceIds: number[], bundleId?: number) => {
    if (bundleId) {
      const bundle = bundles.find((item) => item.id === bundleId)
      return bundle?.price ?? 0
    }
    return serviceIds.reduce((sum, serviceId) => sum + resolveServicePrice(salonId, serviceId, priceListItems), 0)
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

  const completeAppointment = (input: CompleteAppointmentInput) => {
    const nextLineId = performedServiceLines.reduce((maxId, line) => Math.max(maxId, line.id), 0) + 1
    const createdLines: PerformedServiceLine[] = input.lines.map((line, index) => ({
      id: nextLineId + index,
      appointment_id: input.appointment_id,
      service_id: line.service_id,
      worker_id: line.worker_id,
      worker_role_id: line.worker_role_id,
      price_snapshot: line.price_snapshot,
      performed_at: input.performed_at,
      color_product_id: line.color_product_id,
    }))

    const revenue = createdLines.reduce((sum, line) => sum + line.price_snapshot, 0)

    setPerformedServiceLines((prev) => [
      ...prev.filter((line) => line.appointment_id !== input.appointment_id),
      ...createdLines,
    ])

    setAppointments((prev) =>
      prev.map((appointment) =>
        appointment.id === input.appointment_id
          ? {
              ...appointment,
              status: 'done',
              total_price_snapshot: revenue,
            }
          : appointment,
      ),
    )
  }

  const getAppointmentRevenue = (appointmentId: number) => {
    const lines = performedServiceLines.filter((line) => line.appointment_id === appointmentId)
    if (lines.length > 0) {
      return lines.reduce((sum, line) => sum + line.price_snapshot, 0)
    }
    return appointments.find((appointment) => appointment.id === appointmentId)?.total_price_snapshot ?? 0
  }

  const updateServicePrice = (input: UpdatePriceInput) => {
    setPriceListItems((prev) => {
      const next = prev.map((item) =>
        item.id === input.price_list_item_id ? { ...item, price: Math.max(0, Number(input.price) || 0) } : item,
      )
      localStorage.setItem(PRICE_LIST_STORAGE_KEY, JSON.stringify(next))
      return next
    })
  }

  const updateBundlePrice = (input: UpdateBundlePriceInput) => {
    setBundles((prev) => {
      const next = prev.map((bundle) =>
        bundle.id === input.bundle_id ? { ...bundle, price: Math.max(0, Number(input.price) || 0) } : bundle,
      )
      localStorage.setItem(BUNDLE_STORAGE_KEY, JSON.stringify(next))
      return next
    })
  }

  const updateBundleItemPrice = (input: UpdateBundleItemPriceInput) => {
    setBundles((prev) => {
      const next = prev.map((bundle) => {
        if (bundle.id !== input.bundle_id) return bundle
        const items = bundle.items.map((item, index) => {
          if (index !== input.item_index) return item
          if (input.override_price === undefined || Number.isNaN(input.override_price)) {
            const { override_price, ...rest } = item
            return rest
          }
          return { ...item, override_price: Math.max(0, Number(input.override_price) || 0) }
        })
        return { ...bundle, items }
      })
      localStorage.setItem(BUNDLE_STORAGE_KEY, JSON.stringify(next))
      return next
    })
  }

  const value = useMemo(
    () => ({
      salons: mockSalons,
      staffRoles: mockStaffRoles,
      resources: mockResources,
      clients,
      services: mockServices,
      priceListItems,
      bundles,
      colorProducts: mockColorProducts,
      appointments,
      performedServiceLines,
      addClient,
      addAppointment,
      completeAppointment,
      estimateTotal,
      getAppointmentRevenue,
      updateServicePrice,
      updateBundlePrice,
      updateBundleItemPrice,
    }),
    [appointments, bundles, clients, performedServiceLines, priceListItems],
  )

  return <BookingContext.Provider value={value}>{children}</BookingContext.Provider>
}

export const useBooking = () => {
  const context = useContext(BookingContext)
  if (!context) throw new Error('useBooking must be used within BookingProvider')
  return context
}
