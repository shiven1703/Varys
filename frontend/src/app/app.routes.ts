import { Routes } from '@angular/router';

import { authenticatedGuard } from './core/auth.guard';
import { DailyDataComponent } from './daily-data/daily-data.component';
import { LoginComponent } from './login/login.component';
import { ShellComponent } from './shell/shell.component';
import { PlaceholderPageComponent } from './shared/placeholder-page.component';

export const routes: Routes = [
  {
    path: 'login',
    component: LoginComponent
  },
  {
    path: '',
    component: ShellComponent,
    canActivateChild: [authenticatedGuard],
    children: [
      { path: 'daily-data', component: DailyDataComponent },
      {
        path: 'files-packages',
        component: PlaceholderPageComponent,
        data: { title: 'Packages' }
      },
      {
        path: 'runs-diagnostics',
        component: PlaceholderPageComponent,
        data: { title: 'Diagnostics' }
      },
      { path: '', pathMatch: 'full', redirectTo: 'daily-data' },
      { path: '**', redirectTo: 'daily-data' }
    ]
  },
  { path: '**', redirectTo: 'daily-data' }
];
