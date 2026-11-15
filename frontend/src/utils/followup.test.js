import { followUpStatus } from './followup';

const today = new Date(2026, 9, 26); // 26 Oct 2026 (months are zero-based)

test('a future date is shown as a normal follow-up', () => {
  expect(followUpStatus('2026-10-29', 'Lead', today)).toEqual({ label: 'Follow up 2026-10-29', overdue: false });
});

test('today is called out', () => {
  expect(followUpStatus('2026-10-26', 'Contacted', today)).toEqual({ label: 'Follow up today', overdue: false });
});

test('a past date is overdue', () => {
  expect(followUpStatus('2026-10-20', 'Qualified', today)).toEqual({
    label: 'Follow-up overdue (2026-10-20)',
    overdue: true,
  });
});

test('closed deals show nothing', () => {
  expect(followUpStatus('2026-10-20', 'Closed Won', today)).toBeNull();
  expect(followUpStatus('2026-10-20', 'Closed Lost', today)).toBeNull();
});

test('missing or malformed dates show nothing', () => {
  expect(followUpStatus(null, 'Lead', today)).toBeNull();
  expect(followUpStatus('', 'Lead', today)).toBeNull();
  expect(followUpStatus('soon', 'Lead', today)).toBeNull();
  expect(followUpStatus('26/10/2026', 'Lead', today)).toBeNull();
});

test('month and year boundaries compare correctly', () => {
  expect(followUpStatus('2026-11-01', 'Lead', new Date(2026, 9, 31)).overdue).toBe(false);
  expect(followUpStatus('2026-10-31', 'Lead', new Date(2026, 10, 1)).overdue).toBe(true);
  expect(followUpStatus('2027-01-02', 'Lead', new Date(2026, 11, 31)).overdue).toBe(false);
});