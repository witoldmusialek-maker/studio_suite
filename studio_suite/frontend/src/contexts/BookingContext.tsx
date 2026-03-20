import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

import { api } from '../services/api'
import { useAuth } from './AuthContext'
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

type UpdateClientInput = {
  client_id: number
  full_name?: string
  phone?: string
  email?: string
}

type CreateAppointmentInput = {
  salon_id: number
  client_id: number
  start_at: string
  end_at: string
  resources: number[]
  services: number[]
  allow_overlap?: boolean
  bundle_id?: number
}

type CompleteAppointmentLineInput = {
  resources?: Array<{
    recipe_item_id: number
    product_id: number
    quantity_used: number
  }>
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
  reload: () => Promise<void>
  addClient: (input: CreateClientInput) => Promise<ClientCard>
  updateClient: (input: UpdateClientInput) => Promise<ClientCard>
  deleteClient: (clientId: number) => Promise<void>
  addAppointment: (input: CreateAppointmentInput) => Promise<Appointment>
  completeAppointment: (input: CompleteAppointmentInput) => Promise<void>
  estimateTotal: (salonId: number, serviceIds: number[], bundleId?: number) => number
  getAppointmentRevenue: (appointmentId: number) => number
  updateServicePrice: (input: UpdatePriceInput) => Promise<void>
  updateBundlePrice: (input: UpdateBundlePriceInput) => Promise<void>
  updateBundleItemPrice: (input: UpdateBundleItemPriceInput) => Promise<void>
}

type BookingBootstrap = {
  salons: Array<{ id: number; code: string; name: string; is_active: boolean }>
  staffRoles: StaffRole[]
  resources: StaffResource[]
  clients: ClientCard[]
  services: ServiceCatalogItem[]
  priceListItems: PriceListItem[]
  bundles: BundleCatalog[]
  colorProducts: ColorProduct[]
  appointments: Appointment[]
  performedServiceLines: PerformedServiceLine[]
}

const BookingContext = createContext<BookingContextType | undefined>(undefined)

const resolveServicePrice = (salonId: number, serviceId: number, list: PriceListItem[]) =>
  list.find((item) => item.salon_id === salonId && item.service_id === serviceId)?.price ?? 0

export const BookingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth()
  const [salons, setSalons] = useState<Salon[]>([])
  const [staffRoles, setStaffRoles] = useState<StaffRole[]>([])
  const [resources, setResources] = useState<StaffResource[]>([])
  const [clients, setClients] = useState<ClientCard[]>([])
  const [services, setServices] = useState<ServiceCatalogItem[]>([])
  const [priceListItems, setPriceListItems] = useState<PriceListItem[]>([])
  const [bundles, setBundles] = useState<BundleCatalog[]>([])
  const [colorProducts, setColorProducts] = useState<ColorProduct[]>([])
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [performedServiceLines, setPerformedServiceLines] = useState<PerformedServiceLine[]>([])

  const reload = async () => {
    const res = await api.get<BookingBootstrap>('/booking/bootstrap')
    const data = res.data
    setSalons(
      (data.salons || []).map((row) => ({
        id: row.id,
        name: row.name,
        city: row.code,
        code: row.code,
        is_active: row.is_active,
      })),
    )
    setStaffRoles(data.staffRoles || [])
    setResources(data.resources || [])
    setClients(data.clients || [])
    setServices(data.services || [])
    setPriceListItems(data.priceListItems || [])
    setBundles(data.bundles || [])
    setColorProducts(data.colorProducts || [])
    setAppointments(data.appointments || [])
    setPerformedServiceLines(data.performedServiceLines || [])
  }

  useEffect(() => {
    if (!user) {
      setSalons([])
      setStaffRoles([])
      setResources([])
      setClients([])
      setServices([])
      setPriceListItems([])
      setBundles([])
      setColorProducts([])
      setAppointments([])
      setPerformedServiceLines([])
      return
    }
    reload().catch(() => {
      setSalons([])
      setStaffRoles([])
      setResources([])
      setClients([])
      setServices([])
      setPriceListItems([])
      setBundles([])
      setColorProducts([])
      setAppointments([])
      setPerformedServiceLines([])
    })
  }, [user])

  const estimateTotal = (salonId: number, serviceIds: number[], bundleId?: number) => {
    if (bundleId) {
      const bundle = bundles.find((item) => item.id === bundleId)
      return bundle?.price ?? 0
    }
    return serviceIds.reduce((sum, serviceId) => sum + resolveServicePrice(salonId, serviceId, priceListItems), 0)
  }

  const addClient = async (input: CreateClientInput) => {
    const res = await api.post<ClientCard>('/booking/clients', input)
    const created = res.data
    setClients((prev) => [...prev, created])
    return created
  }

  const updateClient = async (input: UpdateClientInput) => {
    const payload: Record<string, string | undefined> = {}
    if (input.full_name !== undefined) payload.full_name = input.full_name
    if (input.phone !== undefined) payload.phone = input.phone
    if (input.email !== undefined) payload.email = input.email
    const res = await api.patch<ClientCard>(`/booking/clients/${input.client_id}`, payload)
    const updated = res.data
    setClients((prev) => prev.map((row) => (row.id === updated.id ? updated : row)))
    return updated
  }

  const deleteClient = async (clientId: number) => {
    await api.delete(`/booking/clients/${clientId}`)
    setClients((prev) => prev.filter((row) => row.id !== clientId))
  }

  const addAppointment = async (input: CreateAppointmentInput) => {
    const total = estimateTotal(input.salon_id, input.services, input.bundle_id)
    const payload = {
      ...input,
      total_price_snapshot: total,
    }
    const res = await api.post<Appointment>('/booking/appointments', payload)
    const created = res.data
    setAppointments((prev) => [created, ...prev])
    await reload()
    return created
  }

  const completeAppointment = async (input: CompleteAppointmentInput) => {
    const res = await api.post<Appointment>(`/booking/appointments/${input.appointment_id}/perform`, {
      performed_at: input.performed_at,
      lines: input.lines,
    })
    const updated = res.data
    setAppointments((prev) => prev.map((appointment) => (appointment.id === updated.id ? updated : appointment)))
    await reload()
  }

  const getAppointmentRevenue = (appointmentId: number) => {
    const lines = performedServiceLines.filter((line) => line.appointment_id === appointmentId)
    if (lines.length > 0) {
      return lines.reduce((sum, line) => sum + line.price_snapshot, 0)
    }
    return appointments.find((appointment) => appointment.id === appointmentId)?.total_price_snapshot ?? 0
  }

  const updateServicePrice = async (input: UpdatePriceInput) => {
    const row = priceListItems.find((item) => item.id === input.price_list_item_id)
    if (!row) return
    await api.patch(`/legacy/catalog/services/${row.service_id}/price`, {
      price: Math.max(0, Number(input.price) || 0),
    }, {
      params: { salon_id: row.salon_id },
    })
    await reload()
  }

  const updateBundlePrice = async (input: UpdateBundlePriceInput) => {
    await api.patch(`/legacy/catalog/bundles/${input.bundle_id}/price`, {
      price: Math.max(0, Number(input.price) || 0),
    })
    await reload()
  }

  const updateBundleItemPrice = async (input: UpdateBundleItemPriceInput) => {
    const bundle = bundles.find((item) => item.id === input.bundle_id)
    if (!bundle) return
    await api.patch(`/legacy/catalog/bundles/${input.bundle_id}/items/${input.item_index + 1}`, {
      override_price:
        input.override_price === undefined || Number.isNaN(input.override_price)
          ? null
          : Math.max(0, Number(input.override_price) || 0),
    })
    await reload()
  }

  const value = useMemo(
    () => ({
      salons,
      staffRoles,
      resources,
      clients,
      services,
      priceListItems,
      bundles,
      colorProducts,
      appointments,
      performedServiceLines,
      reload,
      addClient,
      updateClient,
      deleteClient,
      addAppointment,
      completeAppointment,
      estimateTotal,
      getAppointmentRevenue,
      updateServicePrice,
      updateBundlePrice,
      updateBundleItemPrice,
    }),
    [
      appointments,
      bundles,
      clients,
      colorProducts,
      updateClient,
      deleteClient,
      performedServiceLines,
      priceListItems,
      reload,
      resources,
      salons,
      services,
      staffRoles,
    ],
  )

  return <BookingContext.Provider value={value}>{children}</BookingContext.Provider>
}

export const useBooking = () => {
  const context = useContext(BookingContext)
  if (!context) throw new Error('useBooking must be used within BookingProvider')
  return context
}
