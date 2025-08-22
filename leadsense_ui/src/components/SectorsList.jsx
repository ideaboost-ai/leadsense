function SectorsList({ 
  sectors, 
  selectedSectors, 
  onSectorToggle, 
  onRefresh,
  loading = false 
}) {
  if (sectors.length === 0 && !loading) {
    return (
      <div className="space-y-4">
        <div className="text-gray-600">No sectors found.</div>
        {onRefresh && (
          <div className="flex">
            <button 
              onClick={onRefresh}
              disabled={loading}
              className="rounded bg-indigo-600 text-white px-4 py-2 disabled:opacity-50"
            >
              {loading ? 'Loading…' : 'Refresh Sectors'}
            </button>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <ul className="divide-y">
        {sectors.map((sector) => (
          <li key={sector.id} className="p-4">
            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                checked={selectedSectors.has(sector.id)}
                onChange={() => onSectorToggle(sector.id)}
                className="mt-1 w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
              />
              <div className="flex-1">
                <p className="font-medium">{sector.name}</p>
                {sector.relevance_reason && (
                  <p className="text-sm text-gray-600 mt-1">{sector.relevance_reason}</p>
                )}
                {sector.description && (
                  <p className="text-sm text-gray-500 mt-1">{sector.description}</p>
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>
      {onRefresh && (
        <div className="flex">
          <button 
            onClick={onRefresh}
            disabled={loading}
            className="rounded bg-indigo-600 text-white px-4 py-2 disabled:opacity-50"
          >
            {loading ? 'Loading…' : 'Refresh Sectors'}
          </button>
        </div>
      )}
    </div>
  )
}

export default SectorsList

