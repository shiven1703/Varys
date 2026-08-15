import { HttpClient } from '@angular/common/http';
import { Inject, Injectable, InjectionToken } from '@angular/core';
import { Observable } from 'rxjs';

export const API_BASE_URL = new InjectionToken<string>('API_BASE_URL');

export interface LivenessResponse {
  status: 'ok';
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
}
