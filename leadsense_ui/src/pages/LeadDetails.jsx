import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import '../styles/prose.css'

function LeadDetails() {
  const { leadIndex } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [lead, setLead] = useState(null)
  const [loading, setLoading] = useState(true)
  const [proposalsLoading, setProposalsLoading] = useState(false)
  const [copiedEmail, setCopiedEmail] = useState(false)
  const [copiedLinkedin, setCopiedLinkedin] = useState(false)
  const [companyProfile, setCompanyProfile] = useState(null)

  useEffect(() => {
    // Get lead from navigation state first
    if (location.state && location.state.lead) {
      setLead(location.state.lead)
      setLoading(false)
      return
    }

    // Fallback to localStorage if no state (for backward compatibility)
    const cachedLeads = localStorage.getItem('leadsense_leads')
    if (cachedLeads) {
      try {
        const leads = JSON.parse(cachedLeads)
        const leadIndexNum = parseInt(leadIndex)
        if (leads && leads[leadIndexNum]) {
          setLead(leads[leadIndexNum])
        }
      } catch (e) {
        console.error('Error parsing cached leads:', e)
      }
    }
    setLoading(false)
  }, [leadIndex, location.state])

  // Fetch company profile on component mount
  useEffect(() => {
    const fetchCompanyProfile = async () => {
      try {
        const response = await fetch('/api/company-profiles')
        if (response.ok) {
          const profiles = await response.json()
          if (profiles.length > 0) {
            setCompanyProfile(profiles[0])
          }
        }
      } catch (err) {
        console.error('Error fetching company profile:', err)
      }
    }
    
    fetchCompanyProfile()
  }, [])

  // Function to generate both email and LinkedIn proposals
  const generateProposals = async () => {
    if (!lead || !companyProfile) return
    
    setProposalsLoading(true)
    try {
      const response = await fetch(`/api/leads/generate-proposals`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          lead: {
            company_name: lead.company_name || '',
            website_url: lead.website_url || '',
            description: lead.description || '',
            linkedin_info: lead.linkedin_info || null,
            lead_reasoning: lead.automation_proposal || '',
            sector: lead.sector || '',
            location: lead.location || '',
            confidence_score: lead.confidence_score || 0.8
          },
          company_profile: {
            company_name: companyProfile.company_name,
            location: companyProfile.location,
            description: companyProfile.description,
            team_size: companyProfile.team_size,
            core_services: companyProfile.core_services,
            languages: companyProfile.languages,
            special_offer: companyProfile.special_offer || ''
          }
        })
      })
      const data = await response.json()
      setLead(prevLead => ({ 
        ...prevLead, 
        automation_email: data.automation_email,
        linkedin_message: data.linkedin_message
      }))
    } catch (err) {
      console.error('Error generating proposals:', err)
    } finally {
      setProposalsLoading(false)
    }
  }

  // Function to copy text to clipboard
  const copyToClipboard = async (text, type) => {
    try {
      await navigator.clipboard.writeText(text)
      if (type === 'email') {
        setCopiedEmail(true)
        setTimeout(() => setCopiedEmail(false), 2000)
      } else if (type === 'linkedin') {
        setCopiedLinkedin(true)
        setTimeout(() => setCopiedLinkedin(false), 2000)
      }
    } catch (err) {
      console.error('Failed to copy text: ', err)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Loading lead details...</div>
      </div>
    )
  }

  if (!lead) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-gray-600 mb-4">Lead not found</div>
          <button 
            onClick={() => navigate('/')}
            className="rounded bg-indigo-600 text-white px-4 py-2"
          >
            Back to Leads
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-4xl px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => navigate('/')}
              className="rounded border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50"
            >
              ← Back to Leads
            </button>
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
                  disabled={proposalsLoading || !companyProfile}
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
                  Email Proposal
                </h4>
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                  {lead.automation_email ? (
                    <div>
                      <div className="text-indigo-800 leading-relaxed mb-3 prose prose-indigo max-w-none">
                        <ReactMarkdown>{lead.automation_email}</ReactMarkdown>
                      </div>
                      <button
                        onClick={() => copyToClipboard(lead.automation_email, 'email')}
                        className="text-sm bg-indigo-600 text-white px-3 py-1 rounded hover:bg-indigo-700 transition-colors"
                      >
                        {copiedEmail ? 'Copied!' : 'Copy Email'}
                      </button>
                    </div>
                  ) : (
                    <p className="text-gray-500 italic">
                      {!companyProfile 
                        ? "Company profile not found. Please set up your company profile first."
                        : "Click \"Generate Messages\" to create a personalized email proposal"
                      }
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
                  LinkedIn Message
                </h4>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  {lead.linkedin_message ? (
                    <div>
                      <div className="text-blue-800 leading-relaxed mb-3 prose prose-blue max-w-none">
                        <ReactMarkdown>{lead.linkedin_message}</ReactMarkdown>
                      </div>
                      <button
                        onClick={() => copyToClipboard(lead.linkedin_message, 'linkedin')}
                        className="text-sm bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 transition-colors"
                      >
                        {copiedLinkedin ? 'Copied!' : 'Copy Message'}
                      </button>
                    </div>
                  ) : (
                    <p className="text-gray-500 italic">
                      {!companyProfile 
                        ? "Company profile not found. Please set up your company profile first."
                        : "Click \"Generate Messages\" to create a personalized LinkedIn message"
                      }
                    </p>
                  )}
                </div>
              </div>
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

export default LeadDetails
