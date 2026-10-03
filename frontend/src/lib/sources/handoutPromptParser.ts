export interface PromptExhibitItem {
  type: 'row' | 'metric' | 'bullet' | 'text';
  cols?: string[];
  value?: string;
  label?: string;
  text?: string;
}

export interface PromptSection {
  title: string;
  isTable: boolean;
  isMetricGrid: boolean;
  items: PromptExhibitItem[];
  calloutText: string;
}

export interface ParsedCasePrompt {
  narrative: string;
  sections: PromptSection[];
}

export function parseCasePrompt(rawPrompt?: string): ParsedCasePrompt {
  const raw = rawPrompt || '';
  if (!raw) {
    return { narrative: '', sections: [] };
  }

  // Split by markdown headings starting with '### '
  const parts = raw.split(/\n(?=###\s+)/);
  const narrative = parts[0].replace(/^###\s+.*?\n/, '').trim();
  const sections: PromptSection[] = [];

  for (let i = 1; i < parts.length; i++) {
    const part = parts[i].trim();
    if (!part) continue;
    const lines = part.split('\n');
    const headingLine = lines[0].replace(/^###\s+/, '').trim();
    const bodyLines = lines.slice(1);

    const items: PromptExhibitItem[] = [];
    let calloutText = '';
    let isTable = false;
    let isMetricGrid = false;

    for (const line of bodyLines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      if (
        trimmed.toLowerCase().startsWith('the catch:') ||
        trimmed.toLowerCase().startsWith('note:') ||
        trimmed.toLowerCase().startsWith('constraint:')
      ) {
        calloutText = trimmed;
        continue;
      }

      // Detect bullet or numbered items: '• ', '- ', '1. '
      const bulletMatch = trimmed.match(/^([•\-\*]|\d+\.)\s*(.*)$/);
      if (bulletMatch) {
        const itemText = bulletMatch[2].trim();

        // Pipe-separated table row: 'col1 | col2 | col3'
        if (itemText.includes('|')) {
          isTable = true;
          const cols = itemText.split('|').map((c) => c.trim());
          items.push({ type: 'row', cols });
        }
        // Metric key-value card: 'Value — Label' or 'Value - Label'
        else if (itemText.includes('—') || itemText.includes(' - ')) {
          isMetricGrid = true;
          const sep = itemText.includes('—') ? '—' : ' - ';
          const [val, ...rest] = itemText.split(sep);
          items.push({ type: 'metric', value: val.trim(), label: rest.join(sep).trim() });
        }
        // Standard bullet item
        else {
          items.push({ type: 'bullet', text: itemText });
        }
      } else {
        items.push({ type: 'text', text: trimmed });
      }
    }

    sections.push({
      title: headingLine,
      isTable,
      isMetricGrid: isMetricGrid && !isTable,
      items,
      calloutText,
    });
  }

  return {
    narrative,
    sections,
  };
}
