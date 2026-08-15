import { Component } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from '../core/auth.service';

@Component({
  selector: 'app-shell',
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './shell.component.html',
  styleUrl: './shell.component.scss'
})
export class ShellComponent {
  protected readonly navigation = [
    { path: '/daily-data', label: 'Daily run' },
    { path: '/files-packages', label: 'Packages' },
    { path: '/runs-diagnostics', label: 'Diagnostics' }
  ];

  constructor(
    protected readonly auth: AuthService,
    private readonly router: Router
  ) {}

  protected signOut(): void {
    this.auth.logout().subscribe(() => void this.router.navigateByUrl('/login'));
  }
}
