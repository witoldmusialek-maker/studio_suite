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

export const canAccess = (user: User | null | undefined, section: AppSection): boolean => {
  if (!user) return false
  if (user.is_superadmin) {
    return section === 'tenants'
  }
  return roleSections[user.role]?.includes(section) ?? false
}

export const canAccessSection = canAccess

export const getDefaultRouteForUser = (user: User | null | undefined): string => {
  if (!user) return '/login'
  if (user.is_superadmin) return '/tenants'
  if (canAccess(user, 'dashboard')) return '/dashboard'
  return '/no-access'
}
