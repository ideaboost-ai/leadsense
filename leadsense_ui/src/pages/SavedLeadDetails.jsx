import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import '../styles/prose.css'

function SavedLeadDetails() {
  const { leadId } = useParams()
  const navigate = useNavigate()
  const [lead, setLead] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [proposalsLoading, setProposalsLoading] = useState(false)
  const [copiedEmail, setCopiedEmail] = useState({})
  const [copiedLinkedin, setCopiedLinkedin] = useState({})
  const [selectedEmailVersion, setSelectedEmailVersion] = useState('formal')
  const [selectedLinkedinVersion, setSelectedLinkedinVersion] = useState('formal')
  const [formData, setFormData] = useState({
    status: '',
    priority: '',
    notes: ''
  })

  useEffect(() => {
    fetchLeadDetails()
  }, [leadId])

  const fetchLeadDetails = async () => {
    try {
      setLoading(true)
      const res = await fetch(`/api/leads/saved`)
      if (!res.ok) {
        throw new Error(`Failed to fetch leads: ${res.status}`)
      }
      const leads = await res.json()
      const foundLead = leads.find(l => l.id === parseInt(leadId))
      
      if (!foundLead) {
        setError('Lead not found')
        return
      }
      
      setLead(foundLead)
      setFormData({
        status: foundLead.status,
        priority: foundLead.priority,
        notes: foundLead.notes || ''
      })
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      const res = await fetch(`/api/leads/${leadId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      
      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || `Failed to update lead: ${res.status}`)
      }
      
      const updatedLead = await res.json()
      setLead(prev => ({ ...prev, ...updatedLead }))
      setEditing(false)
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleCancel = () => {
    setFormData({
      status: lead.status,
      priority: lead.priority,
      notes: lead.notes || ''
    })
    setEditing(false)
  }

  // Function to generate both email and LinkedIn proposals
  const generateProposals = async () => {
    if (!lead) return
    
    setProposalsLoading(true)
    try {
      const response = await fetch(`/api/saved-leads/${leadId}/generate-proposals`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `Failed to generate proposals: ${response.status}`)
      }
      
      const data = await response.json()
      setLead(prevLead => ({ 
        ...prevLead, 
        automation_email: data.automation_email,
        linkedin_message: data.linkedin_message,
        updated_at: data.updated_at
      }))
    } catch (err) {
      console.error('Error generating proposals:', err)
      setError(err.message)
    } finally {
      setProposalsLoading(false)
    }
  }

  // Function to copy text to clipboard
  const copyToClipboard = async (text, type, version = null) => {
    try {
      await navigator.clipboard.writeText(text)
      if (type === 'email') {
        setCopiedEmail(prev => ({ ...prev, [version]: true }))
        setTimeout(() => setCopiedEmail(prev => ({ ...prev, [version]: false })), 2000)
      } else if (type === 'linkedin') {
        setCopiedLinkedin(prev => ({ ...prev, [version]: true }))
        setTimeout(() => setCopiedLinkedin(prev => ({ ...prev, [version]: false })), 2000)
      }
    } catch (err) {
      console.error('Failed to copy text: ', err)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading lead details...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-4">
            <button
              onClick={() => navigate('/')}
              className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!lead) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Lead Not Found</h2>
            <p className="text-gray-600 mb-4">The lead you're looking for doesn't exist or has been deleted.</p>
            <button
              onClick={() => navigate('/')}
              className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    )
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'new': return 'bg-blue-100 text-blue-800'
      case 'contacted': return 'bg-yellow-100 text-yellow-800'
      case 'qualified': return 'bg-green-100 text-green-800'
      case 'rejected': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'low': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="rounded border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50"
            >
              ← Back to Dashboard
            </button>
          </div>
          <div>
            {editing ? (
              <div className="flex gap-2">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  onClick={handleCancel}
                  disabled={saving}
                  className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 disabled:opacity-50"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setEditing(true)}
                className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
              >
                Edit Lead
              </button>
            )}
          </div>
        </div>

        {/* Lead Information Card */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* Header Section */}
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-8 text-white">
            <h2 className="text-3xl font-bold mb-2">{lead.company_name || 'Company Name Not Available'}</h2>
            {lead.address && (
              <p className="text-indigo-100 text-lg">{lead.address}</p>
            )}
            {lead.website_url && (
              <a 
                href={lead.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block mt-3 bg-white bg-opacity-20 hover:bg-opacity-30 rounded px-4 py-2 text-sm font-medium transition-colors"
              >
                Visit Website →
              </a>
            )}
          </div>

          {/* Content Section */}
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Contact Information */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  Contact Information
                </h3>
                <div className="space-y-3">
                  {lead.contact_email && (
                    <div>
                      <span className="text-sm font-medium text-gray-500">Email:</span>
                      <div>
                        <a 
                          href={`mailto:${lead.contact_email}`}
                          className="text-indigo-600 hover:text-indigo-800 font-medium"
                        >
                          {lead.contact_email}
                        </a>
                      </div>
                    </div>
                  )}
                  {lead.phone_number && (
                    <div>
                      <span className="text-sm font-medium text-gray-500">Phone:</span>
                      <div>
                        <a 
                          href={`tel:${lead.phone_number}`}
                          className="text-indigo-600 hover:text-indigo-800 font-medium"
                        >
                          {lead.phone_number}
                        </a>
                      </div>
                    </div>
                  )}
                  {!lead.contact_email && !lead.phone_number && (
                    <p className="text-gray-500 italic">No contact information available</p>
                  )}
                </div>
              </div>

              {/* Company Details */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                  Company Details
                </h3>
                <div className="space-y-3">
                  {lead.address && (
                    <div>
                      <span className="text-sm font-medium text-gray-500">Address:</span>
                      <p className="text-gray-900">{lead.address}</p>
                    </div>
                  )}
                  {lead.website_url && (
                    <div>
                      <span className="text-sm font-medium text-gray-500">Website:</span>
                      <div>
                        <a 
                          href={lead.website_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-600 hover:text-indigo-800 font-medium"
                        >
                          {lead.website_url}
                        </a>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Status and Priority */}
            <div className="mt-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Lead Status & Priority
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Status */}
                <div>
                  <span className="text-sm font-medium text-gray-500">Status:</span>
                  <div className="mt-1">
                    {editing ? (
                      <select
                        name="status"
                        value={formData.status}
                        onChange={handleInputChange}
                        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                      >
                        <option value="new">New</option>
                        <option value="contacted">Contacted</option>
                        <option value="qualified">Qualified</option>
                        <option value="rejected">Rejected</option>
                      </select>
                    ) : (
                      <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(lead.status)}`}>
                        {lead.status}
                      </span>
                    )}
                  </div>
                </div>

                {/* Priority */}
                <div>
                  <span className="text-sm font-medium text-gray-500">Priority:</span>
                  <div className="mt-1">
                    {editing ? (
                      <select
                        name="priority"
                        value={formData.priority}
                        onChange={handleInputChange}
                        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                      </select>
                    ) : (
                      <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getPriorityColor(lead.priority)}`}>
                        {lead.priority}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Notes */}
            <div className="mt-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Notes
              </h3>
              {editing ? (
                <textarea
                  name="notes"
                  value={formData.notes}
                  onChange={handleInputChange}
                  rows={4}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Add notes about this lead..."
                />
              ) : (
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-gray-700 leading-relaxed">
                    {lead.notes || 'No notes added'}
                  </p>
                </div>
              )}
            </div>

            {/* Description */}
            {lead.description && (
              <div className="mt-8">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Company Description
                </h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-gray-700 leading-relaxed">{lead.description}</p>
                </div>
              </div>
            )}

            {/* Automation Proposal */}
            {lead.automation_proposal && (
              <div className="mt-8">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  Automation Proposal
                </h3>
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                  <p className="text-indigo-800 leading-relaxed">{lead.automation_proposal}</p>
                </div>
              </div>
            )}

            {/* Generate Proposals Section */}
            <div className="mt-8">
              <div className="flex justify-start mb-6">
                <button
                  onClick={generateProposals}
                  disabled={proposalsLoading}
                  className="rounded bg-gradient-to-r from-indigo-600 to-blue-600 text-white px-4 py-2 text-sm font-medium hover:from-indigo-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {proposalsLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Generating...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                      Generate Messages
                    </>
                  )}
                </button>
              </div>

              {/* Email Proposal */}
              <div className="mb-6">
                <h4 className="text-md font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 19v-8.93a2 2 0 01.89-1.664l7-4.666a2 2 0 012.22 0l7 4.666A2 2 0 0121 10.07V19M3 19a2 2 0 002 2h14a2 2 0 002-2M3 19l6.75-4.5M21 19l-6.75-4.5M3 10l6.75 4.5M21 10l-6.75 4.5m0 0l-1.14.76a2 2 0 01-2.22 0l-1.14-.76" />
                  </svg>
                  Email Proposals
                </h4>
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                  {lead.automation_email ? (
                    <div>
                      {/* Email Version Tabs */}
                      <div className="flex gap-2 mb-4">
                        <button
                          onClick={() => setSelectedEmailVersion('formal')}
                          className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                            selectedEmailVersion === 'formal'
                              ? 'bg-indigo-600 text-white'
                              : 'bg-white text-indigo-600 hover:bg-indigo-100'
                          }`}
                        >
                          Formal
                        </button>
                        <button
                          onClick={() => setSelectedEmailVersion('semi_formal')}
                          className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                            selectedEmailVersion === 'semi_formal'
                              ? 'bg-indigo-600 text-white'
                              : 'bg-white text-indigo-600 hover:bg-indigo-100'
                          }`}
                        >
                          Semi-Formal
                        </button>
                        <button
                          onClick={() => setSelectedEmailVersion('informal')}
                          className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                            selectedEmailVersion === 'informal'
                              ? 'bg-indigo-600 text-white'
                              : 'bg-white text-indigo-600 hover:bg-indigo-100'
                          }`}
                        >
                          Informal
                        </button>
                      </div>
                      
                      {/* Email Content */}
                      <div className="text-indigo-800 leading-relaxed mb-3 prose prose-indigo max-w-none">
                        <ReactMarkdown>{lead.automation_email[selectedEmailVersion]}</ReactMarkdown>
                      </div>
                      
                      {/* Copy Button */}
                      <button
                        onClick={() => copyToClipboard(lead.automation_email[selectedEmailVersion], 'email', selectedEmailVersion)}
                        className="text-sm bg-indigo-600 text-white px-3 py-1 rounded hover:bg-indigo-700 transition-colors"
                      >
                        {copiedEmail[selectedEmailVersion] ? 'Copied!' : 'Copy Email'}
                      </button>
                    </div>
                  ) : (
                    <p className="text-gray-500 italic">
                      Click "Generate Messages" to create personalized email proposals
                    </p>
                  )}
                </div>
              </div>

              {/* LinkedIn Message */}
              <div>
                <h4 className="text-md font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                  LinkedIn Messages
                </h4>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  {lead.linkedin_message ? (
                    <div>
                      {/* LinkedIn Version Tabs */}
                      <div className="flex gap-2 mb-4">
                        <button
                          onClick={() => setSelectedLinkedinVersion('formal')}
                          className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                            selectedLinkedinVersion === 'formal'
                              ? 'bg-blue-600 text-white'
                              : 'bg-white text-blue-600 hover:bg-blue-100'
                          }`}
                        >
                          Formal
                        </button>
                        <button
                          onClick={() => setSelectedLinkedinVersion('semi_formal')}
                          className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                            selectedLinkedinVersion === 'semi_formal'
                              ? 'bg-blue-600 text-white'
                              : 'bg-white text-blue-600 hover:bg-blue-100'
                          }`}
                        >
                          Semi-Formal
                        </button>
                        <button
                          onClick={() => setSelectedLinkedinVersion('informal')}
                          className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                            selectedLinkedinVersion === 'informal'
                              ? 'bg-blue-600 text-white'
                              : 'bg-white text-blue-600 hover:bg-blue-100'
                          }`}
                        >
                          Informal
                        </button>
                      </div>
                      
                      {/* LinkedIn Message Content */}
                      <div className="text-blue-800 leading-relaxed mb-3 prose prose-blue max-w-none">
                        <ReactMarkdown>{lead.linkedin_message[selectedLinkedinVersion]}</ReactMarkdown>
                      </div>
                      
                      {/* Copy Button */}
                      <button
                        onClick={() => copyToClipboard(lead.linkedin_message[selectedLinkedinVersion], 'linkedin', selectedLinkedinVersion)}
                        className="text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 transition-colors"
                      >
                        {copiedLinkedin[selectedLinkedinVersion] ? 'Copied!' : 'Copy Message'}
                      </button>
                    </div>
                  ) : (
                    <p className="text-gray-500 italic">
                      Click "Generate Messages" to create personalized LinkedIn messages
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Additional Information */}
            <div className="mt-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Additional Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <span className="text-sm font-medium text-gray-500">Discovered Date:</span>
                  <p className="text-gray-900 mt-1">
                    {new Date(lead.discovered_at).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-500">Last Updated:</span>
                  <p className="text-gray-900 mt-1">
                    {new Date(lead.updated_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              
              {lead.discovered_sectors && (
                <div className="mt-4">
                  <span className="text-sm font-medium text-gray-500">Discovered Sectors:</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {(() => {
                      try {
                        const sectors = JSON.parse(lead.discovered_sectors)
                        return sectors.map((sector, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
                          >
                            {sector}
                          </span>
                        ))
                      } catch (error) {
                        return (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                            {lead.discovered_sectors}
                          </span>
                        )
                      }
                    })()}
                  </div>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="mt-8 pt-6 border-t border-gray-200">
              <div className="flex gap-3">
                {lead.contact_email && (
                  <a 
                    href={`mailto:${lead.contact_email}`}
                    className="rounded bg-indigo-600 text-white px-6 py-3 font-medium hover:bg-indigo-700 transition-colors"
                  >
                    Send Email
                  </a>
                )}
                {lead.phone_number && (
                  <a 
                    href={`tel:${lead.phone_number}`}
                    className="rounded bg-green-600 text-white px-6 py-3 font-medium hover:bg-green-700 transition-colors"
                  >
                    Call Now
                  </a>
                )}
                {lead.website_url && (
                  <a 
                    href={lead.website_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="rounded border border-gray-300 text-gray-700 px-6 py-3 font-medium hover:bg-gray-50 transition-colors"
                  >
                    Visit Website
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SavedLeadDetails
