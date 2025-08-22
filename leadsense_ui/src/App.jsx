import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import LeadDetails from './pages/LeadDetails'
import SavedLeadDetails from './pages/SavedLeadDetails'

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/lead/:leadId" element={<LeadDetails />} />
          <Route path="/saved-lead/:leadId" element={<SavedLeadDetails />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
