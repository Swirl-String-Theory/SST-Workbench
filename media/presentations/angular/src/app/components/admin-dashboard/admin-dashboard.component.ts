import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  LucideAngularModule,
  Settings,
  RotateCcw,
  X,
  Plus,
  Trash2,
} from 'lucide-angular';
import { CmsService } from '../../services/cms.service';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [
    FormsModule,
    LucideAngularModule.pick({ Settings, RotateCcw, X, Plus, Trash2 }),
  ],
  templateUrl: './admin-dashboard.component.html',
})
export class AdminDashboardComponent {
  readonly cms = inject(CmsService);

  readonly icons = { Settings, RotateCcw, X, Plus, Trash2 };

  openAdmin(): void {
    this.cms.setAdmin(true);
  }

  closeAdmin(): void {
    this.cms.setAdmin(false);
  }
}
