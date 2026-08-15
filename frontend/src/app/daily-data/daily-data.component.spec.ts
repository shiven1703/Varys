import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { of } from 'rxjs';
import { vi } from 'vitest';

import { AuthService } from '../core/auth.service';
import { VarysApiClient } from '../core/api-client';
import { DailyDataComponent } from './daily-data.component';

describe('DailyDataComponent', () => {
  let fixture: ComponentFixture<DailyDataComponent>;
  let runRequests: number;

  beforeEach(async () => {
    runRequests = 0;
    sessionStorage.setItem('varys.daily-run-id', 'run-1');
    await TestBed.configureTestingModule({
      imports: [DailyDataComponent],
      providers: [
        {
          provide: AuthService,
          useValue: { csrfToken: signal('csrf-token') }
        },
        {
          provide: VarysApiClient,
          useValue: {
            getRun: () => {
              runRequests += 1;
              return of({
                id: 'run-1',
                kind: 'daily',
                trade_date: '2026-08-15',
                state: 'RUNNING',
                requested_action: null,
                created_at: '2026-08-15T12:00:00Z',
                updated_at: '2026-08-15T12:00:00Z'
              });
            },
            getRunEvents: () => of([]),
            listPackages: () => of([{
              id: 'package-1',
              run_id: 'run-1',
              kind: 'daily',
              version: 1,
              state: 'BUILDING',
              size_bytes: null,
              sha256: null,
              files: []
            }]),
            packageDownloadUrl: () => '/files/packages/package-1'
          }
        }
      ]
    }).compileComponents();

    vi.useFakeTimers();
    fixture = TestBed.createComponent(DailyDataComponent);
    fixture.detectChanges();
  });

  afterEach(() => {
    fixture.destroy();
    vi.useRealTimers();
    sessionStorage.clear();
  });

  it('keeps an incomplete package unavailable for download', () => {
    const unavailable = fixture.nativeElement.querySelector('.download.unavailable');

    expect(unavailable?.textContent).toContain('Download unavailable');
    expect(fixture.nativeElement.querySelector('a.download')).toBeNull();
  });

  it('refreshes a non-terminal run until it changes state', () => {
    expect(runRequests).toBe(1);

    vi.advanceTimersByTime(1000);

    expect(runRequests).toBe(2);
  });

});
