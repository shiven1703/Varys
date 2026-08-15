import { ApplicationConfig } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { providePrimeNG } from 'primeng/config';
import { provideRouter } from '@angular/router';

import { API_BASE_URL } from './core/api-client';
import { environment } from './core/environment';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(),
    providePrimeNG(),
    provideRouter(routes),
    { provide: API_BASE_URL, useValue: environment.apiBaseUrl }
  ]
};
