/**
 * Generic Loader component with subtle pulse animation.
 * Matches AI "thinking" state - text with gentle opacity pulse, no dots.
 * Text is configurable via setText().
 */
export class Loader {
    private textEl: HTMLElement;
    private baseText: string;
  
    constructor(options: {
      /** The text container element (e.g. loading-text div) - will be populated with text */
      container: HTMLElement;
      text?: string;
    }) {
      const container = options.container;
      this.baseText = options.text ?? 'INITIALIZING';
  
      container.textContent = '';
      container.classList.add('loader-animated');
  
      this.textEl = document.createElement('span');
      this.textEl.className = 'loader-text';
      this.textEl.textContent = this.baseText;
  
      container.appendChild(this.textEl);
    }
  
    /** Update the loader text */
    setText(text: string): void {
      this.baseText = text;
      this.textEl.textContent = text;
    }
  
    /** Clean up */
    destroy(): void {
      // No interval to clear
    }
  }
  