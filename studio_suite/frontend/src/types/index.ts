export interface User {
  id: number
  username: string
  role:
    | 'admin'
    | 'manager'
    | 'manager_main'
    | 'manager_salon'
    | 'employee'
    | 'receptionist'
  full_name?: string
  assigned_salon_ids?: number[]
  linked_staff_id?: number
  linked_staff_name?: string
  linked_salon_id?: number
  linked_salon_name?: string
  totp_enabled?: boolean
  tenant_id?: number
  is_superadmin?: boolean
  licensed_modules?: string[]
  legacy_caisse_enabled?: boolean
}

export interface Salon {
  id: number
  name: string
  city: string
  code?: string
  is_active?: boolean
}

export interface StaffRole {
  id: number
  code: string
  name: string
}

export interface StaffResource {
  id: number
  salon_id: number
  name: string
  role_ids: number[]
}

export interface ClientCard {
  id: number
  full_name: string
  phone: string
  email?: string
  notes?: string
}

export interface ServiceCatalogItem {
  id: number
  code: string
  name: string
  duration_minutes: number
}

export interface PriceListItem {
  id: number
  salon_id: number
  service_id: number
  price: number
}

export interface BundleItem {
  service_id: number
  override_price?: number
}

export interface BundleCatalog {
  id: number
  salon_id: number
  code: string
  name: string
  price: number
  items: BundleItem[]
}

export interface UpdatePriceInput {
  price_list_item_id: number
  price: number
}

export interface UpdateBundlePriceInput {
  bundle_id: number
  price: number
}

export interface UpdateBundleItemPriceInput {
  bundle_id: number
  item_index: number
  override_price?: number
}

export interface ColorProduct {
  id: number
  code: string
  name: string
  brand: string
}

export interface Appointment {
  id: number
  salon_id: number
  client_id: number
  start_at: string
  end_at: string
  status: 'pending' | 'planned' | 'confirmed' | 'done' | 'cancelled' | 'no_show' | 'started' | 'in_progress' | 'completed'
  allow_overlap?: boolean
  resources: number[]
  services: number[]
  bundle_id?: number
  total_price_snapshot: number
}

export interface PerformedServiceLine {
  id: number
  appointment_id: number
  service_id: number
  service_name_snapshot?: string
  worker_id: number
  worker_role_id: number
  list_price_snapshot?: number
  discount_allocated_snapshot?: number
  sold_as_bundle?: boolean
  bundle_id_snapshot?: number
  price_snapshot: number
  performed_at: string
  color_product_id?: number
}
