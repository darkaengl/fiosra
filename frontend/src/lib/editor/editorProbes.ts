export async function fetchLLMEpistemicClassification({
  sessionId,
  sessionAccessToken,
  paragraphText,
  oraclePressure,
}: {
  sessionId: string;
  sessionAccessToken?: string;
  paragraphText: string;
  oraclePressure?: string;
}) {
  if (!sessionId || !paragraphText || paragraphText.trim().length < 20) return null;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(sessionAccessToken ? { 'X-Fiosra-Session-Token': sessionAccessToken } : {}),
  };
  const response = await fetch(`/learning-documents/sessions/${sessionId}/probes/epistemic-classify`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      text: paragraphText.trim(),
      oracle_pressure: oraclePressure,
    }),
  });
  if (!response.ok) return null;
  return await response.json();
}

export async function fetchSentenceInquiry({
  sessionId,
  sessionAccessToken,
  sentenceText,
  moveType = 'challenge',
  epistemicType = 'claim',
  oraclePressure = 'socratic',
}: {
  sessionId: string;
  sessionAccessToken?: string;
  sentenceText: string;
  moveType?: string;
  epistemicType?: string;
  oraclePressure?: string;
}) {
  if (!sessionId || !sentenceText) return null;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(sessionAccessToken ? { 'X-Fiosra-Session-Token': sessionAccessToken } : {}),
  };
  const response = await fetch(`/learning-documents/sessions/${sessionId}/probes/sentence-inquire`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      sentence: sentenceText.trim(),
      epistemic_type: epistemicType,
      move_type: moveType,
      oracle_pressure: oraclePressure,
    }),
  });
  if (!response.ok) return null;
  return await response.json();
}
