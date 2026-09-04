import { Component, HostListener, inject, signal } from '@angular/core';
import { LucideAngularModule, ArrowDown, Menu, X, FileText } from 'lucide-angular';
import { CmsService } from './services/cms.service';
import { AdminDashboardComponent } from './components/admin-dashboard/admin-dashboard.component';
import { HeroSceneComponent } from './components/hero-scene/hero-scene.component';
import { ElectronScaleDerivationComponent } from './components/electron-scale-derivation/electron-scale-derivation.component';
import { MassInvariantSectionComponent } from './components/mass-invariant-section/mass-invariant-section.component';
import {
  TorusKnotsTableComponent,
  HyperbolicKnotsTableComponent,
  KnotGlossaryComponent,
} from './components/knot-table/knot-table.component';
import { StarshipCoilSimulatorComponent } from './components/starship-coil-simulator/starship-coil-simulator.component';
import { UnifiedEnergyChartComponent } from './components/unified-energy-chart/unified-energy-chart.component';
import { VortexRingCalculatorComponent } from './components/vortex-ring-calculator/vortex-ring-calculator.component';
import { RotatingFluidSceneComponent } from './components/rotating-fluid-scene/rotating-fluid-scene.component';
import { AuthorCardComponent } from './components/author-card/author-card.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    LucideAngularModule.pick({ ArrowDown, Menu, X, FileText }),
    AdminDashboardComponent,
    HeroSceneComponent,
    ElectronScaleDerivationComponent,
    MassInvariantSectionComponent,
    TorusKnotsTableComponent,
    HyperbolicKnotsTableComponent,
    KnotGlossaryComponent,
    StarshipCoilSimulatorComponent,
    UnifiedEnergyChartComponent,
    VortexRingCalculatorComponent,
    RotatingFluidSceneComponent,
    AuthorCardComponent,
  ],
  templateUrl: './app.component.html',
})
export class AppComponent {
  readonly cms = inject(CmsService);
  readonly scrolled = signal(false);
  readonly menuOpen = signal(false);
  readonly icons = { ArrowDown, Menu, X, FileText };

  @HostListener('window:scroll')
  onScroll(): void {
    this.scrolled.set(window.scrollY > 50);
  }

  scrollToTop(): void {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  scrollToSection(id: string, event: Event): void {
    event.preventDefault();
    this.menuOpen.set(false);
    const element = document.getElementById(id);
    if (!element) return;
    const headerOffset = 100;
    const offset =
      element.getBoundingClientRect().top + window.pageYOffset - headerOffset;
    window.scrollTo({ top: offset, behavior: 'smooth' });
  }

  toggleMenu(): void {
    this.menuOpen.update((v) => !v);
  }
}
