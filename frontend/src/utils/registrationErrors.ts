/** Candidate Issue #43: safe display of FastAPI registration validation errors. */
export const PASSWORD_POLICY_MESSAGE =
  'La contraseña debe tener como máximo 72 bytes UTF-8 y no contener caracteres NUL.';

type ValidationIssue = { loc?: unknown };

export function registrationErrorMessage(status: number, detail: unknown): string {
  if (status === 422) {
    if (
      Array.isArray(detail) &&
      detail.some((item: unknown) => {
        if (item === null || typeof item !== 'object') return false;
        const loc = (item as ValidationIssue).loc;
        return Array.isArray(loc) && loc.includes('password');
      })
    ) {
      return PASSWORD_POLICY_MESSAGE;
    }
    return 'Revisá el nombre, apellido, correo y contraseña ingresados.';
  }

  // Only a documented public duplicate-email conflict is safe to show.
  // Unknown 400 and every 5xx error must not leak arbitrary backend detail.
  if (status === 400 && detail === 'El email ya está registrado.') {
    return 'El email ya está registrado.';
  }
  return 'Error al registrar la cuenta.';
}

// The page must not display arbitrary Error.message values from transport,
// unexpected thrown code or future server errors.
export function publicRegistrationErrorMessage(error: unknown): string {
  const message = error !== null && typeof error === 'object' && 'message' in error
    ? (error as { message?: unknown }).message
    : null;
  const safeMessages = [
    PASSWORD_POLICY_MESSAGE,
    'Revisá el nombre, apellido, correo y contraseña ingresados.',
    'El email ya está registrado.',
    'Error al registrar la cuenta.',
    'Ocurrió un error de red inesperado.',
  ];
  return typeof message === 'string' && safeMessages.includes(message)
    ? message
    : 'Error al registrar la cuenta.';
}
