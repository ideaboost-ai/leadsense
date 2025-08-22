import { useState } from 'react'

function CollapsibleSection({ 
  title, 
  children, 
  badge, 
  defaultCollapsed = true,
  className = ""
}) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed)

  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      <div 
        className="flex items-center justify-between p-4 cursor-pointer border-b"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-medium">{title}</h2>
          {badge && (
            <span className="bg-indigo-100 text-indigo-800 text-sm px-2 py-1 rounded-full">
              {badge}
            </span>
          )}
        </div>
        <svg 
          className={`w-5 h-5 transition-transform ${isCollapsed ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
      
      {!isCollapsed && (
        <div className="p-4">
          {children}
        </div>
      )}
    </div>
  )
}

export default CollapsibleSection

