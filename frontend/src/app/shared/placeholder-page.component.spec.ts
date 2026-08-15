import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';

import { PlaceholderPageComponent } from './placeholder-page.component';

describe('PlaceholderPageComponent', () => {
  let fixture: ComponentFixture<PlaceholderPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PlaceholderPageComponent],
      providers: [
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { data: { title: 'Daily Data' } } }
        }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(PlaceholderPageComponent);
    fixture.detectChanges();
  });

  it('renders its configured empty-state title', () => {
    expect(fixture.nativeElement.textContent).toContain('Daily Data');
    expect(fixture.nativeElement.textContent).toContain('not available yet');
  });
});
