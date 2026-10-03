export function isTypingTarget(target: EventTarget | null): boolean {
  if (!target || !(target instanceof HTMLElement)) return false;
  const tagName = target.tagName ? target.tagName.toUpperCase() : '';
  if (tagName === 'INPUT' || tagName === 'TEXTAREA' || tagName === 'SELECT') return true;
  if (target.isContentEditable) return true;
  if (typeof target.closest === 'function') {
    if (target.closest('[contenteditable="true"], .prose-mirror, .cm-editor, input, textarea, [role="textbox"]')) {
      return true;
    }
  }
  return false;
}

export interface ZenLayoutState {
  isSourcesCollapsed: boolean;
  isSourcesExpanded: boolean;
  isGutterCollapsed: boolean;
}

export function enterZenMode(currentLayout: ZenLayoutState): {
  savedLayout: ZenLayoutState;
} {
  if (typeof document !== 'undefined') {
    document.body.classList.add('fiosra-zen-mode');
    const elem = document.documentElement;
    if (elem.requestFullscreen) {
      elem.requestFullscreen().catch(() => {});
    } else if ((elem as any).webkitRequestFullscreen) {
      (elem as any).webkitRequestFullscreen();
    }
    window.dispatchEvent(new CustomEvent('fiosra:zen-change', { detail: { active: true } }));
  }
  return {
    savedLayout: { ...currentLayout },
  };
}

export function exitZenMode(): void {
  if (typeof document !== 'undefined') {
    document.body.classList.remove('fiosra-zen-mode');
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
    } else if ((document as any).webkitFullscreenElement) {
      (document as any).webkitExitFullscreen();
    }
    window.dispatchEvent(new CustomEvent('fiosra:zen-change', { detail: { active: false } }));
  }
}
