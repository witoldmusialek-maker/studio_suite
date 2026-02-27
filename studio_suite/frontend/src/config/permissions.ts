import { User } from '../types'

export type AppSection =
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
  admin: ['dashboard', 'calendar', 'clients', 'resources', 'services', 'bundles', 'colors', 'inventory', 'reports', 'users'],
  manager: ['dashboard', 'calendar', 'clients', 'resources', 'services', 'bundles', 'colors', 'inventory', 'reports', 'users'],
  employee: ['dashboard', 'inventory'],
  receptionist: ['dashboard', 'calendar', 'clients', 'inventory'],
}

export const canAccess = (user: User | null | undefined, section: AppSection): boolean => {
  if (!user) return false
  return roleSections[user.role]?.includes(section) ?? false
}

export const canAccessSection = canAccess

export const getDefaultRouteForUser = (user: User | null | undefined): string => {
  if (!user) return '/login'
  if (canAccess(user, 'dashboard')) return '/dashboard'
  return '/no-access'
}
