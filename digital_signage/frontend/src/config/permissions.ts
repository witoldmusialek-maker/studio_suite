import { User } from '../types'
import { FEATURE_FLAGS } from './features'

export type AppSection =
  | 'dashboard'
  | 'monitoring'
  | 'alerts'
  | 'reports'
  | 'displays'
  | 'groups'
  | 'content'
  | 'schedules'
  | 'bells'
  | 'adminUsers'

const roleSections: Record<User['role'], AppSection[]> = {
  admin: [
    'dashboard',
    'monitoring',
    'alerts',
    'reports',
    'displays',
    'groups',
    'content',
    'schedules',
    'bells',
    'adminUsers',
  ],
  operator_displays: [
    'monitoring',
    'displays',
    'groups',
    'content',
    'schedules',
  ],
  operator_bells: [
    'bells',
  ],
  operator: [ // legacy role -> operator wyświetlaczy
    'monitoring',
    'displays',
    'groups',
    'content',
    'schedules',
  ],
}

export const canAccess = (user: User | null | undefined, section: AppSection): boolean => {
  if (!user) return false
  return roleSections[user.role]?.includes(section) ?? false
}

const isSectionEnabled = (section: AppSection): boolean => {
  if (section === 'dashboard') return false
  if (section === 'monitoring') return FEATURE_FLAGS.monitoring
  if (section === 'alerts') return FEATURE_FLAGS.alerts
  if (section === 'reports') return FEATURE_FLAGS.reports
  if (section === 'displays' || section === 'groups') return FEATURE_FLAGS.displays
  if (section === 'content' || section === 'schedules') return FEATURE_FLAGS.content
  if (section === 'bells') return FEATURE_FLAGS.bells
  if (section === 'adminUsers') return FEATURE_FLAGS.adminUsers
  return true
}

export const canAccessSection = (user: User | null | undefined, section: AppSection): boolean => {
  return canAccess(user, section) && isSectionEnabled(section)
}

export const getDefaultRouteForUser = (user: User | null | undefined): string => {
  if (!user) return '/login'
  if (canAccessSection(user, 'monitoring')) return '/status'
  if (canAccessSection(user, 'bells')) return '/bells/model'
  if (canAccessSection(user, 'displays')) return '/displays'
  if (canAccessSection(user, 'content')) return '/content'
  return '/no-access'
}
