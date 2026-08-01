// src/utils/formatters.ts (NUEVO)

/**
 * Formatea una fecha a 'YYYY-MM-DD'.
 * @param date - Objeto Date o string de fecha.
 * @returns string en formato 'YYYY-MM-DD'.
 */
export const getFormattedDate = (date: Date | string): string => {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = (d.getMonth() + 1).toString().padStart(2, '0');
  const day = d.getDate().toString().padStart(2, '0');
  return `${year}-${month}-${day}`;
};

/**
 * Formatea un string de fecha/hora ISO a 'DD/MM/YYYY HH:MM'.
 * @param datetimeString - String de fecha/hora ISO (ej. "2023-11-06T19:00:00Z").
 * @returns string en formato 'DD/MM/YYYY HH:MM'.
 */
export const getFormattedDateTime = (datetimeString: string): string => {
  const d = new Date(datetimeString);
  return d.toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Formatea un string de hora a 'HH:MM'.
 * @param timeString - String de hora (ej. "19:00:00").
 * @returns string en formato 'HH:MM'.
 */
export const getFormattedTime = (timeString: string): string => {
  // Asume que el string ya está en formato HH:MM:SS y toma solo las primeras 5.
  return timeString.substring(0, 5);
};