export interface User {
  id: number
  username: string
  role:
    | 'admin'
    | 'manager'
    | 'receptionist'
    | 'operator_displays'
    | 'operator_bells'
    | 'operator'
  full_name?: string
  assigned_salon_ids?: number[]
}

export interface Display {
  id: number
  name: string
  mac_address: string
  ip_address?: string
  status: 'online' | 'offline' | 'error'
  orientation: number
  resolution_width: number
  resolution_height: number
  group_id?: number
  floor?: string
  position_x?: number
  position_y?: number
  last_seen?: string
  cache_size_mb: number
  created_at: string
}

export interface Content {
  id: number
  filename: string
  original_filename: string
  type: 'image' | 'pdf' | 'excel' | 'video'
  file_path: string
  thumbnail_path?: string
  video_processed: boolean
  file_size_mb?: number
  created_at: string
}

export interface Schedule {
  id: number
  name: string
  content_id: number
  display_id?: number
  group_id?: number
  start_time: string
  end_time: string
  start_date?: string
  end_date?: string
  days_of_week?: number[]
  priority: number
  display_duration_seconds?: number
  active: boolean
}

export interface Group {
  id: number
  name: string
  type: 'horizontal' | 'vertical' | 'mixed' | 'single'
  floor?: string
  layout_config?: any
}

export interface Alert {
  id: number
  display_id: number
  alert_type: string
  severity: 'info' | 'warning' | 'error' | 'critical'
  message: string
  resolved: boolean
  created_at: string
}

export interface BellSchedule {
  id: number
  name: string
  bell_time: string
  event_type?: string  // 'lesson' | 'break'
  days_of_week?: number[]
  start_date?: string
  end_date?: string
  sound_file_path?: string
  volume: number
  play_on_displays?: boolean
  display_ids?: number[]
  group_id?: number
  playlist_id?: number
  active: boolean
}

export interface Salon {
  id: number
  name: string
  city: string
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
  status: 'planned' | 'confirmed' | 'done' | 'cancelled'
  resources: number[]
  services: number[]
  bundle_id?: number
  total_price_snapshot: number
}



