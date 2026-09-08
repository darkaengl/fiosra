# Fiosra Frontend Design System & Screen Specifications
### Next.js 14 Web Applications • Canonical Product Blueprint (Phases 1–5)

This directory hosts the web client applications for Fiosra. The user interface embodies **Structured Exploration** and **Quietly Futuristic** design—restrained, spacious, and calm.

---

## 🎨 Design Tokens & System Standards

### 1. Color System
```css
:root {
  /* Foundations */
  --color-bone: #F6F5F1;      /* Primary Light Background (Warm neutral) */
  --color-obsidian: #111315;  /* Primary Dark Surface / High-Authority Text */
  --color-graphite: #23272B;  /* Secondary Dark Surface */
  --color-cloud: #E9E8E3;     /* Secondary Light Surface & Card Borders */
  --color-slate: #6D7378;     /* Supporting Text & Metadata */

  /* Accents */
  --color-horizon-blue: #4F6BFF; /* Primary Accent (Active states, focus, motion) */
  --color-aurora: #7B61FF;       /* Secondary Accent (Intelligence & transitions) */
  --color-signal-green: #5FAF7A; /* Positive Progress (Muted, mature completion) */
  --color-amber: #D89A3A;        /* Attention (Signals requiring review/context) */
  --color-deep-red: #B74C4C;     /* Critical Destructive Error ONLY (Never for student math feedback) */
}
```

### 2. Typography
- **Brand / Display**: *Instrument Sans*
- **Interface & Text**: *Inter* or *Geist* (high legibility, tabular numbers)
- **Math**: KaTeX

### 3. Spatial System & Corner Radii
- **Spacing Scale**: `4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px, 96px`
- **Corner Radii**:
  - Small (`6px`): Input fields, inline badges, pills
  - Standard (`10px`): Cards, containers, buttons
  - Large (`16px`): Modal overlays, floating toolbars
  - Feature (`24px`): Immersive focus canvases

---

## 🖥️ Screen & Surface Inventory

### 1. Student Experience
1. **Student Home & Orientation**:
   - Concise layout answering: *What should I work on now? Where am I? What's next?*
   - Avoids dashboard noise.
2. **Learning Workspace (`/student/workspace/[id]`)**:
   - **Top**: Course context and problem orientation.
   - **Center**: Dominant active work canvas (symbolic math / steps).
   - **Contextual AI**: Pops in with Socratic guidance when requested, then recedes. **No persistent split-screen chatbox.**
   - **Focus Mode**: Collapses all navigation and secondary metadata to zero noise.
3. **Reasoning Trace Surface (`/student/trace/[id]`)**:
   - Visual metaphor: **The Emergent Path** ($\circ\text{───}\circ\text{───}\bullet\text{───}\circ$).
   - Interactive nodes: *Exploration $\to$ Concept Shift $\to$ Development $\to$ Revision $\to$ Finalisation*.
   - Allows review and **Re-Engage** before deliberate final submission.

### 2. Educator Experience
1. **Workspace & Course Overview (`/educator/courses`)**:
   - Syllabus grounding, module structure, and assignment publishing.
2. **Observability & Signal Triage (`/educator/signals`)**:
   - Prioritized queue: `Signal -> Context -> Interpretation -> Action`.
   - Answers: *"What deserves my attention right now?"* (No walls of charts).
3. **Evidence Dossier Review (`/educator/dossier/[id]`)**:
   - Side-by-side view of final work + interactive Reasoning Trace.
   - Cited verbatim student quotes supporting each rubric criterion.
   - **1-Click Grade Confirmation**.

---

## 🚫 Critical UX Invariants (What to Avoid)
1. **No Chatbot Dominance**: The AI is an ambient tool inside the workspace, not a full-screen conversational agent.
2. **No Red for Educational Errors**: Misconceptions and mistakes trigger neutral or amber Socratic inquiry, never alarming red banners.
3. **No Gamification Gimmicks**: No badges, streak counters, points, or celebratory confetti. Progress is quiet, adult, and earned.
4. **No Surface Proliferation**: Resist "cards-inside-cards-inside-modals". Use clean typography and whitespace for hierarchy.
