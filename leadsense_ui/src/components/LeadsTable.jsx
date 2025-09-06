function LeadsTable({ leads, onLeadClick, onSaveLead, savedLeadIds = new Set(), savingLead = null, loading = false }) {
  if (leads.length === 0) {
    return (
      <div className="text-gray-500 text-center py-8">
        {loading ? 'Discovering leads...' : 'No leads discovered yet. Click "Find Leads" to start.'}
      </div>
    )
  }

  const isLeadSaved = (lead) => {
    const key = `${lead.company_name}-${lead.website_url || ''}`
    return savedLeadIds.has(key)
  }

  const handleSaveClick = (e, lead, index) => {
    e.stopPropagation()
    if (onSaveLead && !isLeadSaved(lead)) {
      onSaveLead(lead, index)
    }
  }

  const truncateText = (text, maxLength = 30) => {
    if (!text) return 'N/A'
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-48">
              Company
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Type
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Website
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Contact
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Description
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Pain Points
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Proposed Solution
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {leads.map((lead, index) => {
            const saved = isLeadSaved(lead)
            const isSaving = savingLead === index
            
            return (
              <tr 
                key={index} 
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => onLeadClick(index)}
              >
                <td className="px-6 py-4 w-48">
                  <div className="text-sm font-medium text-gray-900 truncate" title={lead.company_name || 'N/A'}>
                    {truncateText(lead.company_name, 25)}
                  </div>
                  {lead.address && (
                    <div className="text-sm text-gray-500 truncate" title={lead.address}>
                      {truncateText(lead.address, 20)}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    lead.company_type === 'Startup' ? 'bg-green-100 text-green-800' :
                    lead.company_type === 'SME' ? 'bg-blue-100 text-blue-800' :
                    lead.company_type === 'Larger company' ? 'bg-purple-100 text-purple-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {lead.company_type || 'N/A'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {lead.website_url ? (
                    <a 
                      href={lead.website_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-indigo-600 hover:text-indigo-900 text-sm"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Visit Website
                    </a>
                  ) : (
                    <span className="text-gray-400 text-sm">N/A</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {lead.contact_email && (
                      <div>
                        <a 
                          href={`mailto:${lead.contact_email}`} 
                          className="text-indigo-600 hover:text-indigo-900"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {lead.contact_email}
                        </a>
                      </div>
                    )}
                    {lead.phone_number && (
                      <div className="text-sm text-gray-500">
                        <a 
                          href={`tel:${lead.phone_number}`} 
                          className="text-gray-600 hover:text-gray-900"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {lead.phone_number}
                        </a>
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-900 max-w-xs">
                    {lead.description || 'No description available'}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-900 max-w-xs">
                    {lead.pain_points && lead.pain_points.length > 0 ? (
                      <ul className="list-disc list-inside space-y-1">
                        {lead.pain_points.slice(0, 2).map((point, idx) => (
                          <li key={idx} className="text-xs">{truncateText(point, 40)}</li>
                        ))}
                        {lead.pain_points.length > 2 && (
                          <li className="text-xs text-gray-500">+{lead.pain_points.length - 2} more</li>
                        )}
                      </ul>
                    ) : (
                      <span className="text-gray-400 text-sm">No pain points identified</span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-900 max-w-xs">
                    {lead.proposed_solution || 'No solution proposed'}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex gap-2">
                    {saved ? (
                      <span className="text-gray-500 text-sm">Saved</span>
                    ) : (
                      <button
                        onClick={(e) => handleSaveClick(e, lead, index)}
                        disabled={isSaving}
                        className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                          isSaving 
                            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            : 'bg-green-600 text-white hover:bg-green-700'
                        }`}
                      >
                        {isSaving ? 'Saving...' : 'Save'}
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default LeadsTable

