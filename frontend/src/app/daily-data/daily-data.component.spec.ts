import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { of } from 'rxjs';

import { AuthService } from '../core/auth.service';
import { VarysApiClient } from '../core/api-client';
import { DailyDataComponent } from './daily-data.component';

describe('DailyDataComponent', () => {
  let fixture: ComponentFixture<DailyDataComponent>;

  beforeEach(async () => {
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
            getRun: () => of({
              id: 'run-1',
              kind: 'daily',
              trade_date: '2026-08-15',
              state: 'RUNNING',
              requested_action: null,
              created_at: '2026-08-15T12:00:00Z',
              updated_at: '2026-08-15T12:00:00Z'
            }),
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

    fixture = TestBed.createComponent(DailyDataComponent);
    fixture.detectChanges();
  });

  afterEach(() => sessionStorage.clear());

  it('keeps an incomplete package unavailable for download', () => {
    const unavailable = fixture.nativeElement.querySelector('.download.unavailable');

    expect(unavailable?.textContent).toContain('Download unavailable');
    expect(fixture.nativeElement.querySelector('a.download')).toBeNull();
  });
});
