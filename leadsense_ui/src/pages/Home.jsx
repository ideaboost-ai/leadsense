import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import CollapsibleSection from '../components/CollapsibleSection'
import CompanyProfile from '../components/CompanyProfile'
import SectorsList from '../components/SectorsList'
import LeadsTable from '../components/LeadsTable'
import SavedLeadsTable from '../components/SavedLeadsTable'
import useLocalStorage from '../hooks/useLocalStorage'

const DEFAULT_PROFILE = {
  company_name: 'AutoAI Solutions',
  location: 'Zurich, Switzerland',
  description: 'Tailored software solutions including AI integration.',
  team_size: 5,
  core_services: ['process automation', 'AI integration'],
  languages: ['English', 'German'],
  special_offer: ''
}

function Home() {
  const apiBase = import.meta.env.VITE_API_URL || '/api'
  const navigate = useNavigate()

  const [sectors, setSectors] = useState([])
  const [selectedSectors, setSelectedSectors] = useState(new Set())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  // Company profile state
  const [companyProfile, setCompanyProfile] = useState(DEFAULT_PROFILE)
  const [profileId, setProfileId] = useState(null)
  const [profileLoading, setProfileLoading] = useState(false)
  const [profileSaving, setProfileSaving] = useState(false)
  const [profileError, setProfileError] = useState('')

  // Discovered leads state with localStorage
  const [leads, setLeads] = useLocalStorage('leadsense_leads', [])
  const [queriesUsed, setQueriesUsed] = useState([])
  const [leadsLoading, setLeadsLoading] = useState(false)
  const [leadsError, setLeadsError] = useState('')

  // Saved leads state
  const [savedLeads, setSavedLeads] = useState([])
  const [savedLeadsLoading, setSavedLeadsLoading] = useState(false)
  const [savedLeadsError, setSavedLeadsError] = useState('')
  const [savingLead, setSavingLead] = useState(null)
  const [savedLeadIds, setSavedLeadIds] = useState(new Set())

  // Settings state
  const [maxQueries, setMaxQueries] = useState(2)
  const [sectorPrecision, setSectorPrecision] = useState("medium")
  const [sectorCount, setSectorCount] = useState(1)
  const [settingsLoading, setSettingsLoading] = useState(false)
  const [settingsSaving, setSettingsSaving] = useState(false)
  const [settingsError, setSettingsError] = useState('')
  const [settingsId, setSettingsId] = useState(null)


  const refreshSectors = async () => {
    setError('')
    setLoading(true)
    try {
      const res = await fetch(`${apiBase}/sectors/identify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profile: companyProfile,
          sector_precision: sectorPrecision,
          sector_count: sectorCount
        })
      })
      

      if (!res.ok) throw new Error(`Failed to refresh sectors: ${res.status}`)
      const data = await res.json()
      setSectors(data)
    } catch (e) {
      setError(e.message || 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const fetchSectors = async () => {
    setError('')
    setLoading(true)
    try {
      const res = await fetch(`${apiBase}/sectors`)
      if (!res.ok) throw new Error(`Failed to fetch sectors: ${res.status}`)
      const data = await res.json()
      setSectors(data)
    } catch (e) {
      setError(e.message || 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const fetchCompanyProfile = async () => {
    setProfileError('')
    setProfileLoading(true)
    try {
      const res = await fetch(`${apiBase}/company-profiles`)
      if (!res.ok) throw new Error(`Failed to fetch profiles: ${res.status}`)
      const profiles = await res.json()
      console.log(profiles);
      if (profiles.length > 0) {
        // Use the first profile (most recent)
        const profile = profiles[0]
        setCompanyProfile({
          company_name: profile.company_name,
          location: profile.location,
          description: profile.description,
          team_size: profile.team_size,
          core_services: profile.core_services,
          languages: profile.languages,
          special_offer: profile.special_offer || ''
        })
        setProfileId(profile.id)
      }
    } catch (e) {
      setProfileError(e.message || 'Unknown error')
    } finally {
      setProfileLoading(false)
    }
  }

  const fetchSavedLeads = async () => {
    setSavedLeadsError('')
    setSavedLeadsLoading(true)
    try {
      const res = await fetch(`${apiBase}/leads/saved`)
      if (!res.ok) throw new Error(`Failed to fetch saved leads: ${res.status}`)
      const data = await res.json()
      setSavedLeads(data)
      
      // Update saved lead IDs for tracking
      const savedIds = new Set()
      data.forEach(lead => {
        const key = `${lead.company_name}-${lead.website_url || ''}`
        savedIds.add(key)
      })
      setSavedLeadIds(savedIds)
    } catch (e) {
      setSavedLeadsError(e.message || 'Unknown error')
    } finally {
      setSavedLeadsLoading(false)
    }
  }

  const saveCompanyProfile = async () => {
    setProfileError('')
    setProfileSaving(true)
    try {
      const url = profileId 
        ? `${apiBase}/company-profiles/${profileId}`
        : `${apiBase}/company-profiles`
      
      const method = profileId ? 'PUT' : 'POST'
      
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(companyProfile)
      })
      
      if (!res.ok) throw new Error(`Failed to save profile: ${res.status}`)
      
      const savedProfile = await res.json()
      setProfileId(savedProfile.id)
    } catch (e) {
      setProfileError(e.message || 'Unknown error')
    } finally {
      setProfileSaving(false)
    }
  }

  const saveLead = async (lead, index) => {
    if (!profileId) {
      setLeadsError('Please save your company profile first')
      return
    }

    setSavingLead(index)
    try {
      const selectedSectorNames = sectors
        .filter(s => selectedSectors.has(s.id))
        .map(s => s.name)

      const res = await fetch(`${apiBase}/leads/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lead: lead,
          discovered_sectors: selectedSectorNames
        })
      })
      
      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || `Failed to save lead: ${res.status}`)
      }
      
      const savedLead = await res.json()
      
      // Update saved leads list
      setSavedLeads(prev => [savedLead, ...prev])
      
      // Update saved lead IDs
      const key = `${lead.company_name}-${lead.website_url || ''}`
      setSavedLeadIds(prev => new Set([...prev, key]))
      
    } catch (e) {
      setLeadsError(e.message || 'Unknown error')
    } finally {
      setSavingLead(null)
    }
  }

  const discoverLeads = async () => {
    // Validation
    if (!profileId) {
      setLeadsError('Please save your company profile first')
      return
    }
    
    if (selectedSectors.size === 0) {
      setLeadsError('Please select at least one sector')
      return
    }

    setLeadsError('')
    setLeadsLoading(true)
    try {
      const selectedSectorNames = sectors
        .filter(s => selectedSectors.has(s.id))
        .map(s => s.name)

      const res = await fetch(`${apiBase}/leads/discover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sectors: selectedSectorNames,
          profile: companyProfile,
          max_queries: maxQueries
        })
      })
      
      if (!res.ok) throw new Error(`Failed to discover leads: ${res.status}`)
      
      const data = await res.json()
      setLeads(data.companies)
      setQueriesUsed(data.queries_used)
    } catch (e) {
      setLeadsError(e.message || 'Unknown error')
    } finally {
      setLeadsLoading(false)
    }
  }

  const handleLeadClick = (leadIndex) => {
    const lead = leads[leadIndex]
    if (lead) {
      navigate(`/lead/${leadIndex}`, { state: { lead } })
    }
  }

  const handleSavedLeadClick = (leadId) => {
    navigate(`/saved-lead/${leadId}`)
  }

  const deleteLead = async (leadId) => {
    try {
      const res = await fetch(`${apiBase}/leads/${leadId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || `Failed to delete lead: ${res.status}`)
      }
      
      // Remove the lead from the local state
      setSavedLeads(prev => prev.filter(lead => lead.id !== leadId))
      
      // Update saved lead IDs
      const deletedLead = savedLeads.find(lead => lead.id === leadId)
      if (deletedLead) {
        const key = `${deletedLead.company_name}-${deletedLead.website_url || ''}`
        setSavedLeadIds(prev => {
          const newSet = new Set(prev)
          newSet.delete(key)
          return newSet
        })
      }
      
    } catch (e) {
      setSavedLeadsError(e.message || 'Unknown error')
    }
  }

  const toggleSectorSelection = (sectorId) => {
    setSelectedSectors(prev => {
      const newSet = new Set(prev)
      if (newSet.has(sectorId)) {
        newSet.delete(sectorId)
      } else {
        newSet.add(sectorId)
      }
      return newSet
    })
  }

  const fetchSettings = async () => {
    setSettingsError('')
    setSettingsLoading(true)
    try {
      const res = await fetch(`${apiBase}/settings`)
      if (!res.ok) throw new Error(`Failed to fetch settings: ${res.status}`)
      const settings = await res.json()
      
      setSectorCount(settings.sector_count)
      setSectorPrecision(settings.sector_precision)
      setMaxQueries(settings.max_queries)
      setSettingsId(settings.id)
    } catch (e) {
      setSettingsError(e.message || 'Unknown error')
    } finally {
      setSettingsLoading(false)
    }
  }

  const saveSettings = async () => {
    if (!profileId) {
      setSettingsError('Please save your company profile first')
      return
    }

    setSettingsError('')
    setSettingsSaving(true)
    try {
      const res = await fetch(`${apiBase}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sector_count: sectorCount,
          sector_precision: sectorPrecision,
          max_queries: maxQueries
        })
      })
      
      if (!res.ok) throw new Error(`Failed to save settings: ${res.status}`)
      
      const savedSettings = await res.json()
      setSettingsId(savedSettings.id)
    } catch (e) {
      setSettingsError(e.message || 'Unknown error')
    } finally {
      setSettingsSaving(false)
    }
  }

  useEffect(() => {
    fetchSectors()
    fetchCompanyProfile()
    fetchSavedLeads()
    fetchSettings()
  }, [])

  const selectedCount = selectedSectors.size
  const canDiscoverLeads = profileId && selectedCount > 0

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-semibold">Leadsense</h1>
        </div>

        {error && <div className="mb-4 text-sm text-red-600">{error}</div>}
        {profileError && <div className="mb-4 text-sm text-red-600">{profileError}</div>}
        {leadsError && <div className="mb-4 text-sm text-red-600">{leadsError}</div>}
        {savedLeadsError && <div className="mb-4 text-sm text-red-600">{savedLeadsError}</div>}
        {settingsError && <div className="mb-4 text-sm text-red-600">{settingsError}</div>}

        {/* Company Profile Section */}
        <CollapsibleSection 
          title="Company Profile" 
          badge={profileId ? "Saved" : null}
          defaultCollapsed={true}
          className="mb-6"
        >
          <CompanyProfile
            profile={companyProfile}
            onProfileChange={setCompanyProfile}
            onSave={saveCompanyProfile}
            onRefresh={fetchCompanyProfile}
            isSaving={profileSaving}
            isRefreshing={profileLoading}
            hasProfileId={!!profileId}
          />
        </CollapsibleSection>

        {/* Settings Section */}
        <CollapsibleSection 
          title="Settings" 
          badge={settingsId ? "Saved" : "Configuration"}
          defaultCollapsed={true}
          className="mb-6"
        >
          <div className="p-4 bg-white rounded-lg border">
            <div className="space-y-4">
              <div>
                <label htmlFor="sectorCount" className="block text-sm font-medium text-gray-700 mb-2">
                  Number of Sectors to Recommend
                </label>
                <input
                  id="sectorCount"
                  type="number"
                  min="1"
                  max="5"
                  value={sectorCount}
                  onChange={(e) => setSectorCount(parseInt(e.target.value) || 1)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Number of sectors the AI should recommend (1-5)
                </p>
              </div>
              <div>
                <label htmlFor="sectorPrecision" className="block text-sm font-medium text-gray-700 mb-2">
                  Sector Precision Level
                </label>
                <select
                  id="sectorPrecision"
                  value={sectorPrecision}
                  onChange={(e) => setSectorPrecision(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="general">General - Broad industries (e.g., healthcare, logistics)</option>
                  <option value="medium">Medium - Sub-sectors (e.g., dental clinics, local logistics)</option>
                  <option value="precise">Precise - Specific niches (e.g., family-owned dental clinics in Zurich)</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Controls how specific the sector recommendations will be
                </p>
              </div>
              <div>
                <label htmlFor="maxQueries" className="block text-sm font-medium text-gray-700 mb-2">
                  Maximum Queries per Sector
                </label>
                <input
                  id="maxQueries"
                  type="number"
                  min="1"
                  max="10"
                  value={maxQueries}
                  onChange={(e) => setMaxQueries(parseInt(e.target.value) || 1)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Number of search queries to generate for each selected sector (1-10)
                </p>
              </div>
              
              {/* Save Settings Button */}
              <div className="pt-4 border-t border-gray-200">
                <button 
                  onClick={saveSettings}
                  disabled={!profileId || settingsSaving}
                  className="rounded bg-blue-600 text-white px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {settingsSaving ? 'Saving Settings...' : 'Save Settings'}
                </button>
                {settingsId && (
                  <span className="ml-3 text-sm text-green-600">
                    Settings saved successfully
                  </span>
                )}
              </div>
            </div>
          </div>
        </CollapsibleSection>

        {/* Sectors Section */}
        <CollapsibleSection 
          title="Sectors" 
          badge={selectedCount > 0 ? `${selectedCount} selected` : "No sectors selected"}
          defaultCollapsed={true}
          className="mb-6"
        >
          <SectorsList
            sectors={sectors}
            selectedSectors={selectedSectors}
            onSectorToggle={toggleSectorSelection}
            onRefresh={refreshSectors}
            loading={loading}
          />
        </CollapsibleSection>

        {/* Find Leads Button */}
        <div className="mb-6 ml-3">
          <button 
            onClick={discoverLeads}
            disabled={!canDiscoverLeads || leadsLoading}
            className="rounded bg-green-600 text-white px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {leadsLoading ? 'Discovering Leads...' : 'Find Leads'}
          </button>
        </div>

        {/* Discovered Leads Section */}
        <CollapsibleSection 
          title="Discovered Leads" 
          badge={leads.length > 0 ? `${leads.length} leads` : null}
          defaultCollapsed={false}
          className="mb-6"
        >
          {/* Queries Used Section */}
          {queriesUsed.length > 0 && (
            <CollapsibleSection 
              title="Search Queries Used" 
              badge={`${queriesUsed.length} queries`}
              defaultCollapsed={true}
              className="mb-4"
            >
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-sm text-blue-800 mb-3">
                  The following search queries were used to discover the leads below:
                </p>
                <ul className="space-y-2">
                  {queriesUsed.map((query, index) => (
                    <li key={index} className="text-sm text-blue-700">
                      <span className="font-medium">{query.sector}</span> ({query.language}): 
                      <span className="ml-1 italic">"{query.query}"</span>
                    </li>
                  ))}
                </ul>
              </div>
            </CollapsibleSection>
          )}
          
          <LeadsTable
            leads={leads}
            onLeadClick={handleLeadClick}
            onSaveLead={saveLead}
            savedLeadIds={savedLeadIds}
            savingLead={savingLead}
            loading={leadsLoading}
          />
        </CollapsibleSection>

        {/* Saved Leads Section */}
        <CollapsibleSection 
          title="Saved Leads" 
          badge={savedLeads.length > 0 ? `${savedLeads.length} leads` : null}
          defaultCollapsed={false}
        >
          <SavedLeadsTable
            leads={savedLeads}
            onLeadClick={handleSavedLeadClick}
            onDeleteLead={deleteLead}
            loading={savedLeadsLoading}
          />
        </CollapsibleSection>
      </div>
    </div>
  )
}

export default Home
