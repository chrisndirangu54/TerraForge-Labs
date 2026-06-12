import { describe, expect, it } from 'vitest';
import { phase4Routes } from './routes';

describe('phase4Routes', () => {
  it('includes core mission control paths', () => {
    const paths = phase4Routes.map((route) => route.path);
    expect(paths).toContain('/financial');
    expect(paths).toContain('/deposit');
    expect(paths).toContain('/settings');
    expect(paths).toContain('/admin');
    expect(paths).toContain('/ar');
  });
});