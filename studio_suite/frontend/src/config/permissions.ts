import { User } from '../types'

export type AppSection =
  | 'tenants'
  | 'stocktake_legacy'
  | 'help'
  | 'dashboard'
  | 'calendar'
  | 'clients'
  | 'resources'
  | 'services'
  | 'bundles'
  | 'colors'
  | 'inventory'
  | 'reports'
  | 'users'

const roleSections: Record<User['role'], AppSection[]> = {
  admin: ['dashboard', 'calendar', 'clients', 'resources', 'services', 'bundles', 'colors', 'inventory', 'reports', 'users', 'stocktake_legacy', 'help'],
  manager: ['dashboard', 'calendar', 'clients', 'resources', 'services', 'bundles', 'colors', 'inventory', 'reports', 'users', 'stocktake_legacy', 'help'],
  manager_main: ['dashboard', 'calendar', 'clients', 'resources', 'services', 'bundles', 'colors', 'inventory', 'reports', 'users', 'stocktake_legacy', 'help'],
  manager_salon: ['dashboard', 'calendar', 'clients', 'resources', 'services', 'colors', 'inventory', 'reports', 'users', 'stocktake_legacy', 'help'],
  employee: ['dashboard', 'inventory', 'help'],
  receptionist: ['dashboard', 'calendar', 'clients', 'stocktake_legacy', 'help'],
}

const sectionModules: Partial<Record<AppSection, string[]>> = {
  dashboard: ['BOOKING'],
  calendar: ['BOOKING'],
  clients: ['BOOKING'],
  resources: ['BOOKING'],
  services: ['BOOKING'],
  bundles: ['BOOKING'],
  users: ['BOOKING'],
  colors: ['INVENTORY'],
  inventory: ['INVENTORY'],
  stocktake_legacy: ['INVENTORY'],
  reports: ['REPORTS'],
}

export const hasModuleLicense = (user: User | null | undefined, moduleCode: string): boolean => {
  if (!user) return false
  if (user.is_superadmin) return true
  const code = String(moduleCode || '').trim().toUpperCase()
  if (!code) return true
  const licensed = new Set((user.licensed_modules || []).map((item) => item.trim().toUpperCase()).filter(Boolean))
  return licensed.has(code)
}

export const canAccess = (user: User | null | undefined, section: AppSection): boolean => {
  if (!user) return false
  if (user.is_superadmin) {
    return section === 'tenants'
  }
  if (!(roleSections[user.role]?.includes(section) ?? false)) return false
  const requiredModules = sectionModules[section] || []
  if (requiredModules.length === 0) return true
  return requiredModules.every((code) => hasModuleLicense(user, code))
}

export const canAccessSection = canAccess

export const getDefaultRouteForUser = (user: User | null | undefined): string => {
  if (!user) return '/login'
  if (user.is_superadmin) return '/tenants'
  if (canAccess(user, 'dashboard')) return '/dashboard'
  return '/no-access'
}
