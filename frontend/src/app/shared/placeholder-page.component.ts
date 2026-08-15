import { Component, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-placeholder-page',
  template: `
    <section>
      <h1>{{ title }}</h1>
      <p>This operational view is not available yet.</p>
    </section>
  `
})
export class PlaceholderPageComponent {
  private readonly route = inject(ActivatedRoute);
  protected readonly title = this.route.snapshot.data['title'] as string;
}
