import { Injectable, computed, signal } from '@angular/core';
import { Observable, catchError, map, of, switchMap, tap } from 'rxjs';

import { AuthenticatedUser, LoginResponse, VarysApiClient } from './api-client';

const CSRF_STORAGE_KEY = 'varys.csrf-token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  readonly user = signal<AuthenticatedUser | null>(null);
  readonly csrfToken = signal<string | null>(sessionStorage.getItem(CSRF_STORAGE_KEY));
  readonly isAuthenticated = computed(() => this.user() !== null);

  constructor(private readonly api: VarysApiClient) {}

  login(username: string, password: string): Observable<LoginResponse> {
    return this.api.login(username, password).pipe(
      tap((response) => this.setSession(response))
    );
  }

  restore(): Observable<boolean> {
    return this.api.currentUser().pipe(
      switchMap((user) =>
        this.api.refreshCsrfToken().pipe(
          tap((response) => {
            this.user.set(user);
            this.csrfToken.set(response.csrf_token);
            sessionStorage.setItem(CSRF_STORAGE_KEY, response.csrf_token);
          }),
          map(() => true)
        )
      ),
      catchError(() => {
        this.clearSession();
        return of(false);
      })
    );
  }

  logout(): Observable<void> {
    const csrfToken = this.csrfToken();
    if (csrfToken === null) {
      this.clearSession();
      return of(undefined);
    }
    return this.api.logout(csrfToken).pipe(
      tap({ next: () => this.clearSession() }),
      catchError(() => {
        this.clearSession();
        return of(undefined);
      })
    );
  }

  private setSession(response: LoginResponse): void {
    this.user.set(response.user);
    this.csrfToken.set(response.csrf_token);
    sessionStorage.setItem(CSRF_STORAGE_KEY, response.csrf_token);
  }

  private clearSession(): void {
    this.user.set(null);
    this.csrfToken.set(null);
    sessionStorage.removeItem(CSRF_STORAGE_KEY);
  }
}
