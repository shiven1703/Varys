import { Routes } from '@angular/router';

import { PlaceholderPageComponent } from './shared/placeholder-page.component';

export const routes: Routes = [
  {
    path: 'dashboard',
    component: PlaceholderPageComponent,
    data: { title: 'Dashboard' }
  },
  {
    path: 'daily-data',
    component: PlaceholderPageComponent,
    data: { title: 'Daily Data' }
  },
  {
    path: 'historical-backfill',
    component: PlaceholderPageComponent,
    data: { title: 'Historical Backfill' }
  },
  {
    path: 'files-packages',
    component: PlaceholderPageComponent,
    data: { title: 'Files and Packages' }
  },
  {
    path: 'runs-diagnostics',
    component: PlaceholderPageComponent,
    data: { title: 'Runs and Diagnostics' }
  },
  {
    path: 'settings-users',
    component: PlaceholderPageComponent,
    data: { title: 'Settings and Users' }
  },
  { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
  { path: '**', redirectTo: 'dashboard' }
];
