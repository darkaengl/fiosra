export function routeParams() {
  if (typeof window === 'undefined') return new URLSearchParams('');
  const hash = window.location.hash || '';
  const queryIndex = hash.indexOf('?');
  const hashParams = new URLSearchParams(queryIndex >= 0 ? hash.slice(queryIndex + 1) : '');
  const searchParams = new URLSearchParams(window.location.search || '');
  const merged = new URLSearchParams();
  for (const [k, v] of searchParams.entries()) merged.set(k, v);
  for (const [k, v] of hashParams.entries()) merged.set(k, v);
  return merged;
}

export const COHORT_STUDENTS = [
  { id: 'julian_hayes', name: 'Julian Hayes', initials: 'JH', trap: 'Library Footfall Trap' },
  { id: 'elena_rostova', name: 'Elena Rostova', initials: 'ER', trap: 'Menu Bloat Trap' },
  { id: 'marcus_chen', name: 'Marcus Chen', initials: 'MC', trap: 'Superficial Arithmetic' },
  { id: 'priya_patel', name: 'Priya Patel', initials: 'PP', trap: 'Disjointed Mix Fallacy' },
  { id: 'david_kim', name: 'David Kim', initials: 'DK', trap: 'Library Footfall + Arithmetic' },
  { id: 'maya_lin', name: 'Maya Lin', initials: 'ML', trap: 'Menu Bloat + Disjointed Mix' },
  { id: 'liam_oconnor', name: 'Liam O\'Connor', initials: 'LO', trap: 'Library Footfall Trap' },
  { id: 'sofia_rodriguez', name: 'Sofia Rodriguez', initials: 'SR', trap: 'Superficial Arithmetic & Bloat' },
  { id: 'aisha_almansoor', name: 'Aisha Al-Mansoor', initials: 'AA', trap: 'Disjointed Mix Fallacy' },
  { id: 'lucas_bennett', name: 'Lucas Bennett', initials: 'LB', trap: 'Library Footfall & Mix' },
  { id: 'clara_oswald', name: 'Clara Oswald', initials: 'CO', trap: 'Live Demo · Blank Canvas' },
];

export function getStudentId() {
  const storageKey = 'fiosra.student-id';
  const params = routeParams();
  const fromParam = params.get('student_id');
  if (fromParam) {
    localStorage.setItem(storageKey, fromParam);
    return fromParam;
  }
  const existing = localStorage.getItem(storageKey);
  if (existing && COHORT_STUDENTS.some((s) => s.id === existing)) {
    return existing;
  }
  const defaultStudent = 'julian_hayes';
  localStorage.setItem(storageKey, defaultStudent);
  return defaultStudent;
}

export function setStudentId(studentId) {
  const storageKey = 'fiosra.student-id';
  localStorage.setItem(storageKey, studentId);
}

export function sessionStorageKey(assignmentId, studentId) {
  return `fiosra.session.${assignmentId}.${studentId}`;
}

export function sessionAccessTokenStorageKey(sessionId) {
  return `fiosra.session-access.${sessionId}`;
}

export async function responseError(response, fallback) {
  const payload = await response.json().catch(() => ({}));
  return payload.detail || payload.message || fallback;
}

export function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? '—' : date.toLocaleString();
}
