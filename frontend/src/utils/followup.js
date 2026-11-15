// Describes a deal's follow-up date for display. Returns null when there is nothing
// to show: no valid date, or the deal is already closed.
export function followUpStatus(dateStr, stage, today = new Date()) {
  if (!dateStr || !/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return null;
  if (stage === 'Closed Won' || stage === 'Closed Lost') return null;
  const pad = n => String(n).padStart(2, '0');
  const todayStr = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
  if (dateStr < todayStr) return { label: `Follow-up overdue (${dateStr})`, overdue: true };
  if (dateStr === todayStr) return { label: 'Follow up today', overdue: false };
  return { label: `Follow up ${dateStr}`, overdue: false };
}