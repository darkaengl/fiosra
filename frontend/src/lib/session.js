export function routeParams() {
  const hash = typeof window === 'undefined' ? '' : window.location.hash;
  const queryIndex = hash.indexOf('?');
  return new URLSearchParams(queryIndex >= 0 ? hash.slice(queryIndex + 1) : '');
}

export function getStudentId() {
  const storageKey = 'fiosra.student-id';
  const existing = localStorage.getItem(storageKey);
  if (existing) return existing;
  const studentId = `student_${crypto.randomUUID().slice(0, 8)}`;
  localStorage.setItem(storageKey, studentId);
  return studentId;
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
