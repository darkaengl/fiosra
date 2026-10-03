import { learnerErrorSummary, responseErrorDetails } from '../api-error.js';

export interface SubmitMilestoneParams {
  sessionId: string;
  learningDocument: any;
  pendingSubmissionKey: string;
  sessionHeaders: () => Record<string, string>;
}

export interface SubmitMilestoneResult {
  success: boolean;
  sessionStatus?: string;
  submittedRevision?: number;
  submittedAt?: string;
  submissionNotice: string;
  submissionError: any;
  pendingSubmissionKey: string;
}

export async function submitMilestoneSession({
  sessionId,
  learningDocument,
  pendingSubmissionKey,
  sessionHeaders,
}: SubmitMilestoneParams): Promise<SubmitMilestoneResult> {
  const documentRevision = learningDocument?.document_revision;
  if (typeof documentRevision !== 'number') {
    const err = {
      code: 'SUBMISSION_BLOCKED',
      message: 'Your document must finish loading before it can be submitted.',
      retryable: false,
    };
    return {
      success: false,
      submissionError: err,
      submissionNotice: learnerErrorSummary(err, { draftPreserved: true }),
      pendingSubmissionKey,
    };
  }

  const key = pendingSubmissionKey || crypto.randomUUID();

  try {
    const res = await fetch(`/events/session/${sessionId}/submit`, {
      method: 'POST',
      headers: {
        ...sessionHeaders(),
        'Idempotency-Key': key,
      },
      body: JSON.stringify({ document_revision: documentRevision }),
    });

    if (!res.ok) {
      const err = await responseErrorDetails(res, 'Your milestone could not be submitted.');
      return {
        success: false,
        submissionError: err,
        submissionNotice: learnerErrorSummary(err, { draftPreserved: true }),
        pendingSubmissionKey: key,
      };
    }

    const submitted = await res.json();
    const notice = submitted.idempotent_replay
      ? `This revision was already submitted ${new Date(submitted.submitted_at).toLocaleString()}.`
      : `Submitted ${new Date(submitted.submitted_at).toLocaleString()}.`;

    return {
      success: true,
      sessionStatus: 'submitted',
      submittedRevision: submitted.document_revision,
      submittedAt: submitted.submitted_at,
      submissionNotice: notice,
      submissionError: null,
      pendingSubmissionKey: '',
    };
  } catch (e) {
    const err = {
      code: 'NETWORK_UNAVAILABLE',
      message: 'The submission service is temporarily unavailable.',
      retryable: true,
    };
    return {
      success: false,
      submissionError: err,
      submissionNotice: learnerErrorSummary(err, { draftPreserved: true }),
      pendingSubmissionKey: key,
    };
  }
}

export async function logSocraticMove({
  sessionId,
  blockId,
  text,
  moveType,
  pressure,
  sessionHeaders,
}: {
  sessionId: string;
  blockId: string;
  text: string;
  moveType: string;
  pressure: string;
  sessionHeaders: () => Record<string, string>;
}): Promise<void> {
  if (!sessionId) return;
  try {
    await fetch(`/events/session/${sessionId}`, {
      method: 'POST',
      headers: sessionHeaders(),
      body: JSON.stringify({
        event_type: 'socratic_move_triggered',
        payload: { block_id: blockId, move_type: moveType, text: text.slice(0, 200), pressure },
      }),
    });
  } catch (e) {
    console.warn('Logging Socratic move:', e);
  }
}

export async function logActionCapsuleCommit({
  sessionId,
  studentId,
  questionId,
  capsule,
  textToInsert,
  sessionHeaders,
}: {
  sessionId: string;
  studentId: string;
  questionId: string;
  capsule: any;
  textToInsert: string;
  sessionHeaders: () => Record<string, string>;
}): Promise<void> {
  if (!sessionId) return;
  try {
    await fetch('/events/log', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...sessionHeaders(),
      },
      body: JSON.stringify({
        session_id: sessionId,
        student_id: studentId,
        question_id: questionId || 'q1',
        event_type: 'action_capsule_committed',
        payload: {
          capsule_id: capsule.capsule_id,
          target_block_id: capsule.target_block_id,
          text: textToInsert,
          provenance: 'action_capsule',
          role: capsule.role || 'claim',
        },
      }),
    });
  } catch (err) {
    console.warn('Failed to log action capsule commit event:', err);
  }
}
