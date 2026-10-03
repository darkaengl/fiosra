// Print utility functions for Assignment Brief Handout and PDF primary source exhibits

export function printAssignmentSheet(title?: string): void {
    const sheet = document.querySelector('.academic-sheet');
    if (!sheet) {
      window.print();
      return;
    }

    const existingFrame = document.getElementById('print-brief-frame');
    if (existingFrame) {
      existingFrame.remove();
    }
    const printFrame = document.createElement('iframe') as HTMLIFrameElement;
    printFrame.id = 'print-brief-frame';
    printFrame.style.position = 'fixed';
    printFrame.style.right = '0';
    printFrame.style.bottom = '0';
    printFrame.style.width = '0';
    printFrame.style.height = '0';
    printFrame.style.border = '0';
    printFrame.style.visibility = 'hidden';
    document.body.appendChild(printFrame);

    const frameDoc = printFrame.contentDocument || printFrame.contentWindow?.document;
    if (!frameDoc) return;
    const assignmentTitle = title || 'Academic Assignment Brief';
    frameDoc.open();
    frameDoc.write(`<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>${assignmentTitle}</title>
  <style>
    @page {
      size: A4 portrait;
      margin: 10mm 12mm 10mm 12mm;
    }
    * {
      box-sizing: border-box;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    html, body {
      margin: 0;
      padding: 0;
      background: #ffffff;
      color: #111827;
      font-family: "Georgia", Georgia, "Times New Roman", serif;
      font-size: 11px;
      line-height: 1.42;
    }
    .academic-sheet {
      width: 100%;
      max-width: 100%;
      background: #ffffff;
      padding: 0;
      margin: 0;
    }
    .sheet-page {
      position: relative;
      box-sizing: border-box;
      background: #ffffff;
    }
    .sheet-page-1 {
      page-break-after: always;
      break-after: page;
      padding-bottom: 2mm;
    }
    .sheet-page-2 {
      page-break-before: always;
      break-before: page;
      page-break-after: always;
      break-after: page;
      padding-top: 2mm;
      padding-bottom: 2mm;
    }
    .sheet-page-3 {
      page-break-before: always;
      break-before: page;
      padding-top: 2mm;
    }
    .sheet-page-break {
      page-break-before: always;
      break-before: page;
      height: 0;
      margin: 0;
      padding: 0;
      border: none;
      visibility: hidden;
    }
    .sheet-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 2px solid #0f172a;
      padding-bottom: 8px;
      margin-bottom: 10px;
    }
    .inst-logo {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 1.2px;
      color: #475569;
    }
    .inst-course {
      font-size: 14px;
      font-weight: 800;
      color: #0f172a;
      margin-top: 2px;
    }
    .inst-dept {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 10.5px;
      color: #64748b;
      margin-top: 1px;
    }
    .sheet-meta {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 9.5px;
      color: #475569;
      line-height: 1.45;
      text-align: right;
    }
    .sheet-meta span {
      font-weight: 700;
      color: #0f172a;
    }
    .sheet-title-block {
      margin-bottom: 10px;
    }
    .sheet-title-block h1 {
      font-size: 18px;
      font-weight: 800;
      color: #0f172a;
      margin: 0 0 3px;
      line-height: 1.2;
    }
    .sheet-purpose {
      font-size: 11px;
      font-style: italic;
      color: #475569;
      margin: 0;
      line-height: 1.4;
    }
    .sheet-section {
      margin-bottom: 11px;
      page-break-inside: avoid;
    }
    .sheet-sec-heading {
      display: flex;
      align-items: center;
      gap: 6px;
      border-bottom: 1.5px solid #0f172a;
      padding-bottom: 3px;
      margin-bottom: 7px;
    }
    .sec-num {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 9px;
      font-weight: 800;
      background: #0f172a;
      color: #ffffff;
      padding: 1px 5px;
      border-radius: 2px;
      letter-spacing: 0.5px;
    }
    .sheet-sec-title {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.4px;
      text-transform: uppercase;
      color: #0f172a;
      margin: 0;
    }
    .sheet-narrative-text {
      font-size: 11px;
      line-height: 1.45;
      color: #1e293b;
      margin: 0 0 8px;
    }
    .sub-sec-title {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 10px;
      font-weight: 700;
      color: #334155;
      text-transform: uppercase;
      letter-spacing: 0.3px;
      margin: 6px 0 4px;
    }
    .economics-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 6px;
      margin-bottom: 8px;
    }
    .metric-card {
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 4px;
      padding: 5px 7px;
    }
    .metric-label {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 9px;
      font-weight: 700;
      color: #64748b;
      text-transform: uppercase;
    }
    .metric-val {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 13px;
      font-weight: 800;
      color: #0f172a;
      margin: 1px 0;
    }
    .metric-note {
      font-size: 8.5px;
      color: #475569;
      line-height: 1.25;
    }
    .sheet-table {
      width: 100%;
      border-collapse: collapse;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 9.5px;
      margin-bottom: 8px;
    }
    .sheet-table th, .sheet-table td {
      border: 1px solid #cbd5e1;
      padding: 4px 6px;
      vertical-align: middle;
      text-align: left;
    }
    .sheet-table th {
      background: #f1f5f9;
      color: #0f172a;
      font-weight: 700;
      font-size: 9px;
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }
    .badge-accent {
      font-weight: 700;
      color: #0369a1;
    }
    .text-muted-sm {
      color: #475569;
      font-size: 9px;
    }
    .survey-boundary-block {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
      margin-bottom: 8px;
    }
    .survey-box {
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-left: 3px solid #0284c7;
      border-radius: 4px;
      padding: 5px 8px;
    }
    .survey-hdr {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 3px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 9.5px;
    }
    .sample-tag {
      font-size: 8.5px;
      color: #64748b;
    }
    .survey-list {
      list-style: none;
      padding: 0;
      margin: 0;
      font-size: 9px;
      line-height: 1.35;
      color: #334155;
    }
    .constraint-callout {
      background: #fffbeb;
      border: 1px solid #fde68a;
      border-left: 3px solid #d97706;
      border-radius: 4px;
      padding: 5px 8px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }
    .callout-badge {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 8.5px;
      font-weight: 800;
      letter-spacing: 0.5px;
      color: #92400e;
    }
    .constraint-callout p {
      margin: 2px 0 0;
      font-size: 9.5px;
      font-weight: 600;
      color: #78350f;
      line-height: 1.3;
    }
    .ground-rules-box {
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 4px;
      padding: 6px 8px;
    }
    .rules-title {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 9.5px;
      font-weight: 700;
      color: #0f172a;
      text-transform: uppercase;
      margin-bottom: 4px;
      letter-spacing: 0.3px;
    }
    .rules-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 4px 10px;
    }
    .rule-item {
      display: flex;
      align-items: flex-start;
      gap: 5px;
      font-size: 9px;
      line-height: 1.35;
      color: #334155;
    }
    .rule-index {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 8px;
      font-weight: 800;
      background: #e2e8f0;
      color: #334155;
      border-radius: 50%;
      width: 14px;
      height: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      margin-top: 1px;
    }
    /* Page 2 Elements */
    .page-continuation-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1.5px solid #0f172a;
      padding-bottom: 4px;
      margin-bottom: 10px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 9.5px;
      font-weight: 700;
      color: #475569;
    }
    .page-num-pill {
      background: #0f172a;
      color: #ffffff;
      padding: 1px 6px;
      border-radius: 3px;
      font-size: 8.5px;
    }
    .frameworks-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
      margin-bottom: 8px;
    }
    .framework-card {
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-left: 3px solid #475569;
      border-radius: 4px;
      padding: 5px 7px;
    }
    .fw-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2px;
    }
    .fw-sec {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 8.5px;
      font-weight: 800;
      color: #0f172a;
      background: #e2e8f0;
      padding: 0 4px;
      border-radius: 2px;
    }
    .fw-concept {
      font-size: 8px;
      font-weight: 600;
      color: #64748b;
    }
    .fw-title {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 9.5px;
      font-weight: 700;
      color: #0f172a;
      margin-bottom: 2px;
    }
    .fw-app {
      font-size: 8.5px;
      line-height: 1.35;
      color: #475569;
    }
    .sheet-rubric-table {
      width: 100%;
      border-collapse: collapse;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 9px;
      margin-bottom: 8px;
    }
    .sheet-rubric-table th, .sheet-rubric-table td {
      border: 1px solid #cbd5e1;
      padding: 4px 6px;
      vertical-align: top;
      text-align: left;
    }
    .sheet-rubric-table th {
      background: #f1f5f9;
      color: #0f172a;
      font-weight: 700;
      font-size: 8.5px;
      text-transform: uppercase;
      letter-spacing: 0.3px;
    }
    .sheet-rubric-table tr {
      page-break-inside: avoid;
    }
    .weight-tag {
      display: inline-block;
      font-size: 8.5px;
      font-weight: 800;
      background: #e2e8f0;
      color: #1e293b;
      padding: 0 4px;
      border-radius: 2px;
      margin-left: 3px;
    }
    .crit-sub {
      font-size: 8px;
      color: #64748b;
      margin-top: 1px;
      line-height: 1.25;
    }
    .lvl-title {
      font-weight: 700;
      display: block;
      color: #0f172a;
      font-size: 8.5px;
      margin-bottom: 1px;
    }
    .lvl-desc {
      font-size: 8px;
      color: #475569;
      line-height: 1.3;
    }
    .goals-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 4px 10px;
      margin-bottom: 8px;
    }
    .goal-item {
      display: flex;
      align-items: flex-start;
      gap: 5px;
      font-size: 8.5px;
      line-height: 1.35;
      color: #334155;
    }
    .goal-check {
      color: #15803d;
      font-weight: bold;
      font-size: 9px;
      flex-shrink: 0;
    }
    .integrity-card {
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-left: 3px solid #0f172a;
      border-radius: 4px;
      padding: 6px 8px;
    }
    .integrity-title {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 9px;
      font-weight: 700;
      color: #0f172a;
      margin-bottom: 2px;
    }
    .integrity-text {
      font-size: 8.5px;
      line-height: 1.35;
      color: #475569;
      margin-bottom: 6px;
    }
    .sign-block {
      display: flex;
      justify-content: space-between;
      border-top: 1px dashed #cbd5e1;
      padding-top: 4px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 8.5px;
      color: #64748b;
    }
    .no-print {
      display: none !important;
    }
  </style>
</head>
<body>
  <article class="academic-sheet">
    ${sheet.innerHTML}
  </article>
</body>
</html>`);
    frameDoc.close();

    setTimeout(() => {
      try {
        printFrame.contentWindow?.focus();
        printFrame.contentWindow?.print();
      } catch (e) {
        console.error('Frame print failed, falling back to window.print():', e);
        window.print();
      }
    }, 300);
  }


export function printSourcePdf(sourceUrl?: string): void {
  if (!sourceUrl) return;
  let printFrame = document.getElementById('print-pdf-source-frame') as HTMLIFrameElement | null;
  if (printFrame) {
    printFrame.remove();
  }
  printFrame = document.createElement('iframe');
  printFrame.id = 'print-pdf-source-frame';
  printFrame.style.position = 'fixed';
  printFrame.style.right = '0';
  printFrame.style.bottom = '0';
  printFrame.style.width = '0';
  printFrame.style.height = '0';
  printFrame.style.border = '0';
  printFrame.style.visibility = 'hidden';
  document.body.appendChild(printFrame);

  let hasPrinted = false;
  const triggerPrint = () => {
    if (hasPrinted) return;
    hasPrinted = true;
    try {
      printFrame?.contentWindow?.focus();
      printFrame?.contentWindow?.print();
    } catch {
      window.open(sourceUrl, '_blank');
    }
  };

  printFrame.onload = triggerPrint;
  printFrame.src = sourceUrl;
  // Timeout fallback if onload doesn't trigger for PDF plugin
  setTimeout(triggerPrint, 1200);
}
