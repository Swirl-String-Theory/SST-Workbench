import { Injectable, signal, computed } from '@angular/core';
import { DEFAULT_CONTENT, Paper, SiteContent } from '../models/site-content';

const STORAGE_KEY = 'physics_cms_content';

@Injectable({ providedIn: 'root' })
export class CmsService {
  private readonly _content = signal<SiteContent>(this.loadContent());
  private readonly _isAdmin = signal(false);

  readonly content = this._content.asReadonly();
  readonly isAdmin = this._isAdmin.asReadonly();

  readonly authorLastName = computed(() => {
    const parts = this._content().author.name.split(' ');
    return parts.length > 1 ? parts[1].toUpperCase() : parts[0].toUpperCase();
  });

  private loadContent(): SiteContent {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? (JSON.parse(saved) as SiteContent) : DEFAULT_CONTENT;
    } catch {
      return DEFAULT_CONTENT;
    }
  }

  private persist(): void {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(this._content()));
  }

  updateContent(content: SiteContent): void {
    this._content.set(content);
    this.persist();
  }

  resetToDefault(): void {
    this._content.set(DEFAULT_CONTENT);
    this.persist();
  }

  setAdmin(value: boolean): void {
    this._isAdmin.set(value);
  }

  updateHeroField(key: keyof SiteContent['hero'], value: string): void {
    const c = this._content();
    this.updateContent({ ...c, hero: { ...c.hero, [key]: value } });
  }

  updatePaperTitle(id: string, title: string): void {
    const c = this._content();
    const papers = c.papers.map((p) => (p.id === id ? { ...p, title } : p));
    this.updateContent({ ...c, papers });
  }

  removePaper(id: string): void {
    const c = this._content();
    this.updateContent({ ...c, papers: c.papers.filter((p) => p.id !== id) });
  }

  addPaper(): void {
    const c = this._content();
    const newPaper: Paper = {
      id: Date.now().toString(),
      title: 'New Research Paper',
      color: 'text-physics-cyan',
      tag: 'Addendum',
    };
    this.updateContent({ ...c, papers: [...c.papers, newPaper] });
  }
}
