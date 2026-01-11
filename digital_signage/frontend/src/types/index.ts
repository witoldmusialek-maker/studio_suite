export interface User {
  id: number
  username: string
  role: 'admin' | 'operator'
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
  days_of_week?: number[]
  priority: number
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
  days_of_week?: number[]
  sound_file_path?: string
  volume: number
  active: boolean
}



