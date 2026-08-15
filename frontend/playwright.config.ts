import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://127.0.0.1:8000',
  },
  webServer: {
    command: 'docker compose build app && docker compose up --no-build --detach --wait',
    url: 'http://127.0.0.1:8000/api/health/live',
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
