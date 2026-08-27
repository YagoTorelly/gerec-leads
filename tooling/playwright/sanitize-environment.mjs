export function withoutNoColor(environment) {
  return Object.fromEntries(Object.entries(environment).filter(([name]) => name !== "NO_COLOR"));
}
