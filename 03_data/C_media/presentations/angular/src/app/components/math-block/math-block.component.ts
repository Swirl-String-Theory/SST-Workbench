import { Component, Input, OnChanges } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import katex from 'katex';

@Component({
  selector: 'app-math-block',
  standalone: true,
  template: `
    @if (block) {
      <div class="my-4 overflow-x-auto" [innerHTML]="rendered"></div>
    } @else {
      <span [innerHTML]="rendered"></span>
    }
  `,
})
export class MathBlockComponent implements OnChanges {
  @Input() math = '';
  @Input() block = false;

  rendered: SafeHtml = '';

  constructor(private sanitizer: DomSanitizer) {}

  ngOnChanges(): void {
    const html = katex.renderToString(this.math, {
      displayMode: this.block,
      throwOnError: false,
    });
    this.rendered = this.sanitizer.bypassSecurityTrustHtml(html);
  }
}
