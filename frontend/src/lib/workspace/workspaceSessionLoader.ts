import {
  responseError,
  sessionAccessTokenStorageKey,
  sessionStorageKey,
} from '../session.js';

export interface DiscoveredSession {
  courseId: string;
  assignmentId: string;
  assignment: any;
  sessionId: string;
  sessionAccessToken: string;
  sessionStatus: string;
  submittedRevision: number | null;
  submittedAt: string;
}

export async function discoverAndInitializeSession({
  routeCourseId,
  routeAssignmentId,
  studentId,
}: {
  routeCourseId: string;
  routeAssignmentId: string;
  studentId: string;
}): Promise<DiscoveredSession | null> {
  let courseId = routeCourseId;
  let assignmentId = routeAssignmentId;
  let assignment: any = null;

  if (assignmentId) {
    const response = await fetch(`/assignments/${assignmentId}`);
    if (!response.ok) throw new Error(await responseError(response, 'The requested assignment could not be loaded.'));
    const found = await response.json();
    if (found.status === 'published') {
      assignment = found;
    } else {
      assignment = null;
    }
  } else if (courseId) {
    const response = await fetch(`/assignments?course_id=${encodeURIComponent(courseId)}&status=published`);
    if (response.ok) {
      const assignments = await response.json();
      const pub = assignments.filter((a: any) => a.status === 'published');
      assignment = pub[0] || null;
      assignmentId = assignment?.assignment_id || '';
    }
  }

  if (!assignment && !courseId) {
    try {
      const coursesRes = await fetch('/courses');
      if (coursesRes.ok) {
        const coursesList = await coursesRes.json();
        const courses = Array.isArray(coursesList) ? coursesList : coursesList.courses || [];
        for (const c of courses) {
          const cid = c.course_id || c.id;
          if (!cid) continue;
          const res = await fetch(`/assignments?course_id=${encodeURIComponent(cid)}&status=published`);
          if (res.ok) {
            const list = await res.json();
            const pubList = list.filter((a: any) => a.status === 'published');
            if (pubList.length > 0) {
              assignment = pubList[0];
              assignmentId = assignment.assignment_id;
              courseId = cid;
              break;
            }
          }
        }
      }
    } catch (err) {
      console.warn('Auto-discovering published assignment:', err);
    }
  }

  if (!assignment && !courseId) {
    try {
      const directRes = await fetch('/assignments');
      if (directRes.ok) {
        const allList = await directRes.json();
        const pubList = allList.filter((a: any) => a.status === 'published');
        if (pubList.length > 0) {
          assignment = pubList[0];
          assignmentId = assignment.assignment_id;
        }
      }
    } catch (err) {
      console.warn('Direct assignment fallback fetch:', err);
    }
  }

  if (!assignment) return null;

  let sessionId = '';
  let sessionAccessToken = '';
  let sessionStatus = '';
  let submittedRevision: number | null = null;
  let submittedAt = '';

  const key = sessionStorageKey(assignmentId, studentId);
  const persistedSessionId = localStorage.getItem(key);
  const persistedAccessToken = persistedSessionId
    ? localStorage.getItem(sessionAccessTokenStorageKey(persistedSessionId))
    : '';

  if (persistedSessionId && persistedAccessToken) {
    const existing = await fetch(`/events/session/${persistedSessionId}`, {
      headers: { 'X-Fiosra-Session-Token': persistedAccessToken },
    });
    if (existing.ok) {
      const session = (await existing.json()).session;
      if (['active', 'submitted', 'completed'].includes(session.status) && session.assignment_id === assignmentId) {
        sessionId = persistedSessionId;
        sessionAccessToken = persistedAccessToken;
        sessionStatus = session.status;
        submittedRevision = session.submitted_document_revision ?? null;
        submittedAt = session.submitted_at || '';
      } else {
        localStorage.removeItem(key);
      }
    } else {
      localStorage.removeItem(key);
    }
  }

  if (!sessionId) {
    try {
      const listRes = await fetch(`/events/sessions?student_id=${encodeURIComponent(studentId)}&assignment_id=${encodeURIComponent(assignmentId)}`);
      if (listRes.ok) {
        const sData = await listRes.json();
        const existingList = sData.sessions || [];
        if (existingList.length > 0) {
          const targetSess = existingList[existingList.length - 1];
          const recRes = await fetch(`/events/session/${targetSess.session_id}/reconnect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: studentId }),
          });
          if (recRes.ok) {
            const recData = await recRes.json();
            sessionId = recData.session_id;
            sessionAccessToken = recData.access_token;
            sessionStatus = recData.status;
            submittedRevision = targetSess.submitted_document_revision ?? null;
            submittedAt = targetSess.submitted_at || '';
            localStorage.setItem(key, sessionId);
            localStorage.setItem(sessionAccessTokenStorageKey(sessionId), sessionAccessToken);
          }
        }
      }
    } catch (e) {
      console.warn('Could not reconnect to existing student session:', e);
    }
  }

  if (!sessionId) {
    const response = await fetch('/events/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: studentId,
        assignment_id: assignmentId,
        current_question_id: assignment.question_id,
      }),
    });
    if (!response.ok) throw new Error(await responseError(response, 'A reasoning session could not be started.'));
    const created = await response.json();
    sessionId = created.session_id;
    sessionAccessToken = created.access_token;
    sessionStatus = created.status;
    localStorage.setItem(key, sessionId);
    localStorage.setItem(sessionAccessTokenStorageKey(sessionId), sessionAccessToken);
  }

  return {
    courseId,
    assignmentId,
    assignment,
    sessionId,
    sessionAccessToken,
    sessionStatus,
    submittedRevision,
    submittedAt,
  };
}
