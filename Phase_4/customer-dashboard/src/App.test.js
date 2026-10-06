import { render, screen } from '@testing-library/react';
import App from './App';

// Old CRA test retained for reference before LAB_ML4:
// test('renders learn react link', () => {
//   render(<App />);
//   const linkElement = screen.getByText(/learn react/i);
//   expect(linkElement).toBeInTheDocument();
// });

test('renders the loading state while the dashboard summary loads', () => {
  render(<App />);
  expect(screen.getByText('Loading...')).toBeInTheDocument();
});
