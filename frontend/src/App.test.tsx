import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from './App'

// Mock the router for testing
const AppWithRouter = () => (
  <MemoryRouter initialEntries={['/dashboard']}>
    <App />
  </MemoryRouter>
)

describe('App', () => {
  it('renders without crashing', () => {
    render(<AppWithRouter />)
    // Check if the main layout elements are present
    expect(document.querySelector('.ant-layout')).toBeInTheDocument()
  })

  it('renders COT Studio in header', () => {
    render(<AppWithRouter />)
    expect(screen.getByText('COT Studio')).toBeInTheDocument()
  })

  it('renders dashboard content', () => {
    render(<AppWithRouter />)
    expect(screen.getByText('仪表板')).toBeInTheDocument()
  })
})