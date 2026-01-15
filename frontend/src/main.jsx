import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import "./index.css"
import Home from"./Home.jsx"
import Results from "./Results.jsx"

function AppRouter() {
  const [path, setPath] = useState(window.location.pathname)
  useEffect(() => {
    const onPop = () => setPath(window.location.pathname)
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  if (path === '/search') {
    return <Results />
  }
  return <Home />
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AppRouter />
    
  </StrictMode>,
)
