import { splitEmail, mailtoHref, emailFileName } from './email';

test('splits subject and body', () => {
  expect(splitEmail('Subject: Hello there\n\nLine one\nLine two')).toEqual({
    subject: 'Hello there',
    body: 'Line one\nLine two',
  });
});

test('without a Subject line the whole text is the body', () => {
  expect(splitEmail('Just a body')).toEqual({ subject: '', body: 'Just a body' });
});

test('handles Windows line endings', () => {
  expect(splitEmail('Subject: Hi\r\n\r\nBody here')).toEqual({ subject: 'Hi', body: 'Body here' });
});

test('a subject with no body gives an empty body', () => {
  expect(splitEmail('Subject: Only a subject')).toEqual({ subject: 'Only a subject', body: '' });
});

test('mailto link encodes subject and body', () => {
  expect(mailtoHref('Subject: Hello there\n\nLine one\nLine two')).toBe(
    'mailto:?subject=Hello%20there&body=Line%20one%0ALine%20two'
  );
});

test('mailto link for empty text is safe', () => {
  expect(mailtoHref('')).toBe('mailto:?subject=&body=');
  expect(mailtoHref(null)).toBe('mailto:?subject=&body=');
});

test('file name is a readable slug', () => {
  expect(emailFileName('Satya Nadella')).toBe('satya-nadella-email.txt');
  expect(emailFileName('  Dr. Jane O\'Neil!! ')).toBe('dr-jane-o-neil-email.txt');
});

test('file name falls back when the name is missing', () => {
  expect(emailFileName('')).toBe('lead-email.txt');
  expect(emailFileName(undefined)).toBe('lead-email.txt');
});