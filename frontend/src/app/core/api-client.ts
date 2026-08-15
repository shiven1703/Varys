import { HttpClient } from '@angular/common/http';
import { Inject, Injectable, InjectionToken } from '@angular/core';
import { Observable } from 'rxjs';

export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL');

export interface LivenessResponse {
  status: 'ok';
}

export interface AuthenticatedUser {
  id: string;
  username: string;
}

export interface LoginResponse {
  user: AuthenticatedUser;
  csrf_token: string;
}

export interface CsrfTokenResponse {
  csrf_token: string;
}

export interface Run {
  id: string;
  kind: string;
  trade_date: string | null;
  state: string;
  requested_action: string | null;
  created_at: string;
  updated_at: string;
}

export interface RunEvent {
  sequence: number;
  event_type: string;
  from_state: string | null;
  to_state: string | null;
  created_at: string;
}

export interface PackageFile {
  name: string;
  sha256: string;
  size_bytes: number;
  row_count: number | null;
}

export interface DataPackage {
  id: string;
  run_id: string;
  kind: string;
  version: number;
  state: string;
  size_bytes: number | null;
  sha256: string | null;
  files: PackageFile[];
}

@Injectable({ providedIn: 'root' })
export class VarysApiClient {
  constructor(
    private readonly http: HttpClient,
    @Inject(API_BASE_URL) private readonly apiBaseUrl: string
  ) {}

  getLiveness(): Observable<LivenessResponse> {
    return this.http.get<LivenessResponse>(`${this.apiBaseUrl}/api/health/live`);
  }

  login(username: string, password: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(
      `${this.apiBaseUrl}/api/v1/auth/login`,
      { username, password },
      { withCredentials: true }
    );
  }

  currentUser(): Observable<AuthenticatedUser> {
    return this.http.get<AuthenticatedUser>(
      `${this.apiBaseUrl}/api/v1/auth/current-user`,
      { withCredentials: true }
    );
  }

  refreshCsrfToken(): Observable<CsrfTokenResponse> {
    return this.http.post<CsrfTokenResponse>(
      `${this.apiBaseUrl}/api/v1/auth/csrf`,
      null,
      { withCredentials: true }
    );
  }

  logout(csrfToken: string): Observable<void> {
    return this.http.post<void>(
      `${this.apiBaseUrl}/api/v1/auth/logout`,
      null,
      { headers: { 'X-CSRF-Token': csrfToken }, withCredentials: true }
    );
  }

  createDailyRun(tradeDate: string, csrfToken: string): Observable<Run> {
    return this.http.post<Run>(
      `${this.apiBaseUrl}/api/v1/runs/daily`,
      { trade_date: tradeDate },
      { headers: { 'X-CSRF-Token': csrfToken }, withCredentials: true }
    );
  }

  getRun(runId: string): Observable<Run> {
    return this.http.get<Run>(`${this.apiBaseUrl}/api/v1/runs/${runId}`, {
      withCredentials: true
    });
  }

  getRunEvents(runId: string): Observable<RunEvent[]> {
    return this.http.get<RunEvent[]>(
      `${this.apiBaseUrl}/api/v1/runs/${runId}/events`,
      { withCredentials: true }
    );
  }

  listPackages(): Observable<DataPackage[]> {
    return this.http.get<DataPackage[]>(`${this.apiBaseUrl}/api/v1/packages`, {
      withCredentials: true
    });
  }

  packageDownloadUrl(packageId: string): string {
    return `${this.apiBaseUrl}/files/packages/${packageId}`;
  }
}
