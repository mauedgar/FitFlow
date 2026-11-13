import { UserRole } from '../types';

// A verified backend role determines navigation, never a locally decoded JWT.
// Unknown roles stay on the public landing instead of redirecting in a loop.
export function verifiedRoleDestination(role: UserRole): string {
  switch (role) {
    case UserRole.ADMIN:
      return '/admin';
    case UserRole.FRONT_DESK:
      return '/front-desk';
    case UserRole.TEACHER:
      return '/teacher';
    case UserRole.CLIENT:
      return '/home';
    // Historical trainer is not an authoritative server role.
    default:
      return '/landing';
  }
}
