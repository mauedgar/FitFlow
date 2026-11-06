/** Every useAuth login/logout advances this generation before React state changes. */
let generation = 0;
export const getAuthSessionGeneration = (): number => generation;
export const advanceAuthSessionGeneration = (): number => ++generation;
