import { UserRole } from "../types";

export function roleDestination(role: UserRole): string {
  switch (role) {
    case UserRole.ADMIN: return "/admin";
    case UserRole.CLIENT:
    case UserRole.TEACHER: return "/home";
    case UserRole.FRONT_DESK: return "/front-desk";
    default: return "/landing";
  }
}
