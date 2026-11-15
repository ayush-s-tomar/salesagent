import ErrorBoundary from './ErrorBoundary';

test('starts without an error', () => {
  expect(new ErrorBoundary({}).state).toEqual({ hasError: false });
});

test('an error switches the boundary into its error state', () => {
  expect(ErrorBoundary.getDerivedStateFromError(new Error('boom'))).toEqual({ hasError: true });
});