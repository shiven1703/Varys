import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  protected readonly navigation = [
    { path: '/dashboard', label: 'Dashboard' },
    { path: '/daily-data', label: 'Daily Data' },
    { path: '/historical-backfill', label: 'Historical Backfill' },
    { path: '/files-packages', label: 'Files and Packages' },
    { path: '/runs-diagnostics', label: 'Runs and Diagnostics' },
    { path: '/settings-users', label: 'Settings and Users' }
  ];
}
