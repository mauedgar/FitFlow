// Product-local business calendar. The backend's FITFLOW_TIMEZONE value is
// projected into the frontend build as VITE_FITFLOW_TIMEZONE.
const businessTimezone = import.meta.env.VITE_FITFLOW_TIMEZONE ?? 'America/Argentina/Buenos_Aires';

// Validate at module initialization: never silently inherit the browser zone.
new Intl.DateTimeFormat('en-US', { timeZone: businessTimezone }).format(new Date());

export const businessDateKey = (instant: Date): string => {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: businessTimezone, year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(instant);
  const part = (type: string): string => {
    const value = parts.find((item) => item.type === type)?.value;
    if (value === undefined) throw new Error(`Missing ${type} business date part`);
    return value;
  };
  return `${part('year')}-${part('month')}-${part('day')}`;
};

// Date keys, not browser-local Date objects, define each calendar column.
const calendarDate = (key: string): Date => new Date(`${key}T12:00:00.000Z`);
const advanceDateKey = (key: string, days: number): string => {
  const date = calendarDate(key);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
};

export const currentBusinessWeek = (now: Date = new Date()): string[] => {
  const today = businessDateKey(now);
  const mondayOffset = (calendarDate(today).getUTCDay() + 6) % 7;
  const monday = advanceDateKey(today, -mondayOffset);
  return Array.from({ length: 7 }, (_, day) => advanceDateKey(monday, day));
};

export const businessDayLabel = (key: string): string =>
  new Intl.DateTimeFormat('es-AR', {
    timeZone: 'UTC', weekday: 'short', day: '2-digit', month: '2-digit',
  }).format(calendarDate(key));

export const businessTimeLabel = (iso: string): string =>
  new Intl.DateTimeFormat('es-AR', {
    timeZone: businessTimezone, hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).format(new Date(iso));
