import { de } from './de';

export function t(key: string): string {
  const keys = key.split('.');
  let current: unknown = de;
  for (const k of keys) {
    if (current && typeof current === 'object' && k in current) {
      current = (current as Record<string, unknown>)[k];
    } else {
      return key;
    }
  }
  return typeof current === 'string' ? current : key;
}

export { de };