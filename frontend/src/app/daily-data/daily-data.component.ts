import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnDestroy, OnInit, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';

import { AuthService } from '../core/auth.service';
import { DataPackage, Run, RunEvent, VarysApiClient } from '../core/api-client';

const RUN_STORAGE_KEY = 'varys.daily-run-id';
const TERMINAL_RUN_STATES = new Set([
  'COMPLETED',
  'COMPLETED_WITH_WARNINGS',
  'FAILED',
  'CANCELLED'
]);
const REFRESH_INTERVAL_MS = 1000;

@Component({
  selector: 'app-daily-data',
  imports: [FormsModule],
  templateUrl: './daily-data.component.html',
  styleUrl: './daily-data.component.scss'
})
export class DailyDataComponent implements OnInit, OnDestroy {
  protected tradeDate = '2026-08-14';
  protected readonly run = signal<Run | null>(null);
  protected readonly events = signal<RunEvent[]>([]);
  protected readonly packages = signal<DataPackage[]>([]);
  protected readonly starting = signal(false);
  protected readonly refreshing = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly currentPackages = computed(() => {
    const run = this.run();
    return run === null
      ? []
      : this.packages().filter((dataPackage) => dataPackage.run_id === run.id);
  });
  private refreshTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(
    private readonly api: VarysApiClient,
    private readonly auth: AuthService
  ) {}

  ngOnInit(): void {
    this.refresh();
  }

  ngOnDestroy(): void {
    this.cancelScheduledRefresh();
  }

  protected startRun(): void {
    const csrfToken = this.auth.csrfToken();
    if (this.starting() || csrfToken === null) {
      this.error.set('Your sign-in needs to be refreshed before starting a run.');
      return;
    }
    this.starting.set(true);
    this.error.set(null);
    this.api.createDailyRun(this.tradeDate, csrfToken).subscribe({
      next: (run) => {
        sessionStorage.setItem(RUN_STORAGE_KEY, run.id);
        this.run.set(run);
        this.events.set([]);
        this.starting.set(false);
        this.refresh();
      },
      error: (error: unknown) => {
        this.error.set(apiErrorMessage(error));
        this.starting.set(false);
      }
    });
  }

  protected refresh(): void {
    if (this.refreshing()) {
      return;
    }
    this.cancelScheduledRefresh();
    this.refreshing.set(true);
    this.error.set(null);
    const runId = sessionStorage.getItem(RUN_STORAGE_KEY);
    if (runId === null) {
      this.api.listPackages().subscribe({
        next: (packages) => {
          this.packages.set(packages);
          this.refreshing.set(false);
        },
        error: (error: unknown) => this.finishRefreshWithError(error, null)
      });
      return;
    }

    forkJoin({
      packages: this.api.listPackages(),
      run: this.api.getRun(runId),
      events: this.api.getRunEvents(runId)
    }).subscribe({
      next: (result) => {
        this.packages.set(result.packages);
        this.run.set(result.run);
        this.events.set(result.events);
        if (result.run.trade_date !== null) {
          this.tradeDate = result.run.trade_date;
        }
        this.refreshing.set(false);
        this.scheduleRefresh(result.run);
      },
      error: (error: unknown) => this.finishRefreshWithError(error, runId)
    });
  }

  protected canDownload(dataPackage: DataPackage): boolean {
    return dataPackage.state === 'READY' || dataPackage.state === 'READY_WITH_WARNINGS';
  }

  protected downloadUrl(dataPackage: DataPackage): string {
    return this.api.packageDownloadUrl(dataPackage.id);
  }

  protected stateLabel(value: string): string {
    return value.replaceAll('_', ' ').toLowerCase();
  }

  protected stateTone(value: string): string {
    if (value === 'READY' || value === 'COMPLETED') {
      return 'status-success';
    }
    if (value.includes('WARNING') || value === 'PAUSED') {
      return 'status-warning';
    }
    if (value.includes('FAILED') || value === 'QUARANTINED' || value === 'CANCELLED') {
      return 'status-danger';
    }
    return 'status-neutral';
  }

  private finishRefreshWithError(error: unknown, runId: string | null): void {
    if (error instanceof HttpErrorResponse && error.status === 404 && runId !== null) {
      sessionStorage.removeItem(RUN_STORAGE_KEY);
      this.run.set(null);
      this.events.set([]);
      this.refreshing.set(false);
      this.loadPackagesAfterStaleRun();
      return;
    }
    this.error.set(apiErrorMessage(error));
    this.refreshing.set(false);
  }

  private loadPackagesAfterStaleRun(): void {
    this.api.listPackages().subscribe({
      next: (packages) => this.packages.set(packages),
      error: (error: unknown) => this.error.set(apiErrorMessage(error))
    });
  }

  private scheduleRefresh(run: Run): void {
    if (!TERMINAL_RUN_STATES.has(run.state)) {
      this.refreshTimer = setTimeout(() => this.refresh(), REFRESH_INTERVAL_MS);
    }
  }

  private cancelScheduledRefresh(): void {
    if (this.refreshTimer !== null) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }
}

function apiErrorMessage(error: unknown): string {
  if (error instanceof HttpErrorResponse) {
    if (error.status === 409 && error.error?.detail === 'RUN_ALREADY_EXISTS') {
      return 'A non-terminal daily run already exists for this date.';
    }
    if (typeof error.error?.detail === 'string') {
      return error.error.detail;
    }
  }
  return 'Unable to load the latest server state. Please try again.';
}
