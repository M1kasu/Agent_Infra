export function createLogicalClock(start = "2026-08-16T09:00:00.000Z") {
  let cursor = new Date(start).getTime();
  return function now() {
    const value = new Date(cursor).toISOString();
    cursor += 137;
    return value;
  };
}

