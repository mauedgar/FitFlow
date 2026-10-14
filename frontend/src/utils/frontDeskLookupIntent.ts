// Product-local identity guard for asynchronous Front Desk document lookup.
// The visible input is authoritative; even A -> B -> A does not revalidate an
// earlier response for A because each edit increments the monotonic revision.
export interface LookupIntent {
  revision: number;
  document: string;
}

export const nextLookupIntent = (current: LookupIntent, document: string): LookupIntent => ({
  revision: current.revision + 1,
  document: document.trim(),
});

export const isCurrentLookupIntent = (
  current: LookupIntent,
  responseFor: LookupIntent,
): boolean =>
  current.revision === responseFor.revision &&
  current.document === responseFor.document &&
  current.document.length > 0;
