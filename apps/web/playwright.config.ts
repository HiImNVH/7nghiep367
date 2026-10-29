import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: ['browser/**/*.spec.ts', 'accessibility/**/*.spec.ts'],
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:5173', permissions: ['camera'],
    viewport: { width: 1440, height: 900 },
    launchOptions: {
      ...(process.env.VISIGN_BROWSER_CHANNEL ? { channel: process.env.VISIGN_BROWSER_CHANNEL } : {}),
      args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'],
    },
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run dev -- --port 5173 --strictPort',
    url: 'http://127.0.0.1:5173', reuseExistingServer: !process.env.CI,
  },
});
