import { useState } from 'react'

const DEFAULT_PROFILE = {
  company_name: 'AutoAI Solutions',
  location: 'Zurich, Switzerland',
  description: 'Tailored software solutions including AI integration.',
  team_size: 5,
  core_services: ['process automation', 'AI integration'],
  languages: ['English', 'German'],
  special_offer: ''
}

function CompanyProfile({ 
  profile, 
  onProfileChange, 
  onSave, 
  onRefresh,
  isSaving = false, 
  isRefreshing = false,
  hasProfileId = false 
}) {
  const [isEditing, setIsEditing] = useState(false)

  const handleSave = async () => {
    await onSave()
    setIsEditing(false)
  }

  return (
    <div className="space-y-4">
      {isEditing ? (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Company Name</label>
            <input 
              type="text"
              value={profile.company_name}
              onChange={(e) => onProfileChange({...profile, company_name: e.target.value})}
              className="w-full rounded border border-gray-300 p-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Location</label>
            <input 
              type="text"
              value={profile.location}
              onChange={(e) => onProfileChange({...profile, location: e.target.value})}
              className="w-full rounded border border-gray-300 p-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea 
              value={profile.description}
              onChange={(e) => onProfileChange({...profile, description: e.target.value})}
              rows={3}
              className="w-full rounded border border-gray-300 p-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Team Size</label>
            <input 
              type="number"
              value={profile.team_size}
              onChange={(e) => onProfileChange({...profile, team_size: parseInt(e.target.value) || 0})}
              className="w-full rounded border border-gray-300 p-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Core Services (comma separated)</label>
            <input 
              type="text"
              value={profile.core_services.join(', ')}
              onChange={(e) => onProfileChange({
                ...profile, 
                core_services: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
              })}
              className="w-full rounded border border-gray-300 p-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Languages (comma separated)</label>
            <input 
              type="text"
              value={profile.languages.join(', ')}
              onChange={(e) => onProfileChange({
                ...profile, 
                languages: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
              })}
              className="w-full rounded border border-gray-300 p-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Special Offer</label>
            <textarea 
              value={profile.special_offer || ''}
              onChange={(e) => onProfileChange({...profile, special_offer: e.target.value})}
              rows={3}
              placeholder="Describe any special offers or promotions..."
              className="w-full rounded border border-gray-300 p-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div className="flex gap-2">
            <button 
              onClick={handleSave}
              disabled={isSaving}
              className="rounded bg-indigo-600 text-white px-4 py-2 disabled:opacity-50"
            >
              {isSaving ? 'Saving...' : 'Save Profile'}
            </button>
            <button 
              onClick={() => setIsEditing(false)}
              className="rounded border border-gray-300 px-4 py-2"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <div>
            <span className="text-sm font-medium text-gray-500">Company Name:</span>
            <p className="text-gray-900">{profile.company_name}</p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-500">Location:</span>
            <p className="text-gray-900">{profile.location}</p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-500">Description:</span>
            <p className="text-gray-900">{profile.description}</p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-500">Team Size:</span>
            <p className="text-gray-900">{profile.team_size}</p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-500">Core Services:</span>
            <p className="text-gray-900">{profile.core_services.join(', ')}</p>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-500">Languages:</span>
            <p className="text-gray-900">{profile.languages.join(', ')}</p>
          </div>
          {profile.special_offer && (
            <div>
              <span className="text-sm font-medium text-gray-500">Special Offer:</span>
              <p className="text-gray-900">{profile.special_offer}</p>
            </div>
          )}
          <div className="flex gap-2">
            <button 
              onClick={() => setIsEditing(true)}
              className="rounded bg-indigo-600 text-white px-4 py-2"
            >
              Edit Profile
            </button>
            {onRefresh && (
              <button 
                onClick={onRefresh}
                disabled={isRefreshing}
                className="rounded border border-gray-300 px-4 py-2 disabled:opacity-50"
              >
                {isRefreshing ? 'Loading…' : 'Refresh Profile'}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default CompanyProfile

