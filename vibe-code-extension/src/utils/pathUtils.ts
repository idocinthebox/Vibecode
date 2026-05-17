import * as path from 'path';

export function normalizePath(input: string): string {
  return path.normalize(input).replace(/\\/g, '/');
}

export function isSubPath(parent: string, child: string): boolean {
  const rel = path.relative(parent, child);
  return !rel.startsWith('..') && !path.isAbsolute(rel);
}
