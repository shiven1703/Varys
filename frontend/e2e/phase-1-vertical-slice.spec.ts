import { randomBytes, randomUUID } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import { expect, Page, test } from '@playwright/test';

const repositoryRoot = resolve(process.cwd(), '..');
const username = `e2e-${randomBytes(8).toString('hex')}`;
const password = randomBytes(24).toString('base64url');

interface DataPackage {
  id: string;
  run_id: string;
  kind: 'daily';
  version: number;
  state: 'READY' | 'READY_WITH_WARNINGS';
  sha256: string;
}

interface JsonResponse {
  status: number;
  body: unknown;
}

let runId = '';
let readyPackage: DataPackage;

test.describe.serial('Phase 1 fixture vertical slice', () => {
  test.setTimeout(60_000);
  test.beforeAll(() => createAdministrator());

  test('logs in, completes a fixture run, and downloads a verified package', async ({
    page
  }, testInfo) => {
    await login(page);
    await page.getByLabel('Trading date').fill('2026-08-14');
    await page.getByRole('button', { name: 'Start run' }).click();

    await expect(page.locator('.status-panel .status')).toHaveText('completed', {
      timeout: 30_000
    });
    const eventTypes = page.locator('.events strong');
    await expect(eventTypes.filter({ hasText: /^created$/ })).toBeVisible();
    await expect(eventTypes.filter({ hasText: /^claimed$/ })).toBeVisible();
    await expect(eventTypes.filter({ hasText: /^completed$/ })).toBeVisible();

    const packagesResponse = await browserJsonGet(page, '/api/v1/packages');
    expect(packagesResponse.status).toBe(200);
    const packages = packagesResponse.body as DataPackage[];
    runId = await page.locator('.status-panel dd').first().innerText();
    const matchedPackage = packages.find((dataPackage) => dataPackage.run_id === runId);
    expect(matchedPackage).toBeDefined();
    readyPackage = matchedPackage as DataPackage;
    expect(['READY', 'READY_WITH_WARNINGS']).toContain(readyPackage.state);

    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('link', { name: 'Download ZIP' }).click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toBe(`varys-${readyPackage.id}.zip`);
    const archivePath = testInfo.outputPath(download.suggestedFilename());
    await download.saveAs(archivePath);

    verifyDownloadedPackage(archivePath, readyPackage);
  });

  test('blocks an authenticated download while a package is incomplete', async ({
    page
  }) => {
    await login(page);
    const incompletePackageId = createIncompletePackage(runId);

    const response = await browserJsonGet(
      page,
      `/files/packages/${incompletePackageId}`
    );

    expect(response.status).toBe(404);
    expect(response.body).toEqual({
      detail: 'Package is not available'
    });
  });

  test('blocks an unauthenticated package download', async ({ request }) => {
    const response = await request.get(`/files/packages/${readyPackage.id}`);

    expect(response.status()).toBe(401);
    await expect(response.json()).resolves.toEqual({
      detail: 'Authentication required'
    });
  });

  test('logout revokes package access', async ({ page }) => {
    await login(page);
    await page.getByRole('button', { name: 'Sign out' }).click();
    await expect(page).toHaveURL(/\/login$/);

    const response = await browserJsonGet(
      page,
      `/files/packages/${readyPackage.id}`
    );

    expect(response.status).toBe(401);
  });
});

async function login(page: Page): Promise<void> {
  await page.goto('/login');
  await page.getByLabel('Username').fill(username);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/\/daily-data$/);
  await expect(page.getByRole('heading', { name: 'Prepare market data' })).toBeVisible();
}

async function browserJsonGet(page: Page, path: string): Promise<JsonResponse> {
  return page.evaluate(async (requestPath) => {
    const response = await fetch(requestPath, { credentials: 'include' });
    return { status: response.status, body: await response.json() };
  }, path);
}

function createAdministrator(): void {
  runContainerPython(
    `
import json
import sys
from varys.auth import create_user
from varys.config import load_settings
from varys.db import create_session_factory

credentials = json.load(sys.stdin)
settings = load_settings()
with create_session_factory(settings.database_url).begin() as database:
    create_user(database, credentials["username"], credentials["password"])
`,
    { username, password }
  );
}

function createIncompletePackage(parentRunId: string): string {
  const packageId = randomUUID();
  runContainerPython(
    `
import json
import sys
from uuid import UUID
from varys.config import load_settings
from varys.db import create_session_factory
from varys.packages import PackageIdentity, PackageKind, create_package
from varys.runs import Run

values = json.load(sys.stdin)
settings = load_settings()
with create_session_factory(settings.database_url).begin() as database:
    run = database.get(Run, UUID(values["run_id"]))
    if run is None:
        raise RuntimeError("E2E parent run is missing")
    create_package(
        database,
        run.id,
        PackageIdentity(UUID(values["package_id"]), PackageKind.DAILY, 2),
    )
`,
    { run_id: parentRunId, package_id: packageId }
  );
  return packageId;
}

function runContainerPython(code: string, input: object): void {
  const result = spawnSync(
    'docker',
    ['compose', 'exec', '--no-TTY', 'app', 'python', '-c', code],
    {
      cwd: repositoryRoot,
      encoding: 'utf8',
      input: JSON.stringify(input)
    }
  );
  expect(result.status, result.stderr).toBe(0);
}

function verifyDownloadedPackage(
  archivePath: string,
  dataPackage: DataPackage
): void {
  const code = `
import sys
from pathlib import Path
from uuid import UUID
from varys.packages import PackageIdentity, PackageKind, PackageState, inspect_archive

archive = inspect_archive(
    Path(sys.argv[1]),
    PackageIdentity(UUID(sys.argv[2]), PackageKind(sys.argv[3]), int(sys.argv[4])),
)
if archive.sha256 != sys.argv[5]:
    raise RuntimeError("download checksum differs from package metadata")
if archive.state not in (PackageState.READY, PackageState.READY_WITH_WARNINGS):
    raise RuntimeError("downloaded package is not ready")
`;
  const result = spawnSync(
    `${repositoryRoot}/.venv/bin/python`,
    [
      '-c',
      code,
      archivePath,
      dataPackage.id,
      dataPackage.kind,
      String(dataPackage.version),
      dataPackage.sha256
    ],
    {
      cwd: repositoryRoot,
      encoding: 'utf8',
      env: { ...process.env, PYTHONPATH: `${repositoryRoot}/backend` }
    }
  );
  expect(result.status, result.stderr).toBe(0);
}
