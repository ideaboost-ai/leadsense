import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'

function LeadDetails() {
  const { leadIndex } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [lead, setLead] = useState(null)
  const [loading, setLoading] = useState(true)

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
