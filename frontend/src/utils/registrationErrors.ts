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
    return 'Revisá los datos ingresados.';
  }

  return typeof detail === 'string' && detail.trim()
    ? detail
    : 'Error al registrar la cuenta.';
}
