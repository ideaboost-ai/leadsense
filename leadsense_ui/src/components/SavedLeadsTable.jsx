import React, { useState } from 'react'

function SavedLeadsTable({ leads, onLeadClick, onDeleteLead, loading = false }) {
  const [deleteConfirm, setDeleteConfirm] = useState({ show: false, lead: null })

  if (leads.length === 0) {
    return (
      <div className="text-gray-500 text-center py-8">
        {loading ? 'Loading saved leads...' : 'No saved leads yet. Save leads from the Discovered Leads section to see them here.'}
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

  const truncateText = (text, maxLength = 30) => {
    if (!text) return 'N/A'
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  const handleDeleteClick = (e, lead) => {
    e.stopPropagation()
    setDeleteConfirm({ show: true, lead })
  }

  const confirmDelete = () => {
    if (deleteConfirm.lead && onDeleteLead) {
      onDeleteLead(deleteConfirm.lead.id)
    }
    setDeleteConfirm({ show: false, lead: null })
  }

  const cancelDelete = () => {
    setDeleteConfirm({ show: false, lead: null })
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-48">
                Company
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Website
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Contact
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Priority
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Saved Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {leads.map((lead, index) => (
              <tr 
                key={lead.id} 
                className="hover:bg-gray-50"
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
                  {lead.website_url ? (
                    <a 
                      href={lead.website_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-indigo-600 hover:text-indigo-900 text-sm"
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
                        >
                          {lead.phone_number}
                        </a>
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(lead.status)}`}>
                    {lead.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPriorityColor(lead.priority)}`}>
                    {lead.priority}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(lead.created_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex gap-2">
                    <button
                      onClick={() => onLeadClick(lead.id)}
                      className="text-indigo-600 hover:text-indigo-900"
                    >
                      View
                    </button>
                    <button
                      onClick={(e) => handleDeleteClick(e, lead)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirm.show && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              {/* Icon */}
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              
              {/* Title */}
              <div className="mt-4 text-center">
                <h3 className="text-lg font-medium text-gray-900">
                  Delete Lead
                </h3>
              </div>
              
              {/* Message */}
              <div className="mt-2 px-7 text-center">
                <p className="text-sm text-gray-500">
                  Are you sure you want to delete the lead <strong>"{deleteConfirm.lead?.company_name}"</strong>?
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  This action cannot be undone and will permanently remove this lead from your saved leads.
                </p>
              </div>
              
              {/* Buttons */}
              <div className="flex justify-center gap-3 mt-6">
                <button
                  onClick={cancelDelete}
                  className="px-4 py-2 bg-gray-300 text-gray-700 text-base font-medium rounded-md shadow-sm hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDelete}
                  className="px-4 py-2 bg-red-600 text-white text-base font-medium rounded-md shadow-sm hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                  Delete Lead
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default SavedLeadsTable
