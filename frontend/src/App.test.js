import { render, screen } from '@testing-library/react';
import App from './App';

test('renders Hướng dẫn Button', () => {
  render(<App />);
  const linkElement = screen.getByText(/Hướng dẫn/i);
  expect(linkElement).toBeInTheDocument();
});
