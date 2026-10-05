import { defineConfig } from '@playwright/test';
export default defineConfig({ testDir: './e2e', workers: 1, use: { baseURL: process.env['E2E_BASE_URL'] || 'http://127.0.0.1:4200', headless: true, ...(process.env['E2E_CHROME'] ? { channel: 'chrome' } : {}) }, reporter: 'list' });
