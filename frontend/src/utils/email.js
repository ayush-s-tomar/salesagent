// Helpers for acting on a generated email draft.

// Splits "Subject: ...\n\nbody" into { subject, body }. Without a Subject line,
// the whole text is the body.
export function splitEmail(text) {
  const raw = String(text || '').replace(/\r\n/g, '\n');
  const m = raw.match(/^\s*Subject:\s*([^\n]*)(?:\n+([\s\S]*))?$/i);
  if (m) return { subject: m[1].trim(), body: (m[2] || '').trim() };
  return { subject: '', body: raw.trim() };
}

// A mailto: link that opens the visitor's default mail app with the draft filled in.
export function mailtoHref(text) {
  const { subject, body } = splitEmail(text);
  return 'mailto:?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
}

export function emailFileName(name) {
  const slug = String(name || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return (slug || 'lead') + '-email.txt';
}

export function downloadTextFile(text, filename) {
  const blob = new Blob([String(text || '')], { type: 'text/plain;charset=utf-8' });
  const href = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = href;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(href);
}