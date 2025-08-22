#!/usr/bin/env python
"""
Simple database module for leadsense project.
Handles SQLite3 database operations for caching sector information.
"""

import sqlite3
import threading
import json
from typing import List, Dict, Optional


class DatabaseManager:
    """Manages SQLite3 database operations."""
    
    def __init__(self, db_path: str = "leadsense.db"):
        self.db_path = db_path
        self.connection = None
        self._connection_lock = threading.Lock()
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the database and create tables."""
        # check_same_thread=False allows using the same connection across threads,
        # guarded by _connection_lock where write operations happen.
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """Create sectors, company_profiles, and leads tables if they don't exist."""
        cursor = self.connection.cursor()
        
        # Create sectors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                relevance_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create company_profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT NOT NULL,
                team_size INTEGER NOT NULL,
                core_services TEXT NOT NULL,  -- JSON array as string
                languages TEXT NOT NULL,      -- JSON array as string
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create leads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                website_url TEXT,
                address TEXT,
                contact_email TEXT,
                phone_number TEXT,
                description TEXT,
                automation_proposal TEXT,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                discovered_by_profile_id INTEGER,
                discovered_sectors TEXT,
                status TEXT DEFAULT 'new',
                priority TEXT DEFAULT 'medium',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (discovered_by_profile_id) REFERENCES company_profiles(id)
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_leads_company_name ON leads(company_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_leads_discovered_at ON leads(discovered_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_leads_profile_id ON leads(discovered_by_profile_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_leads_active ON leads(is_active)')
        
        self.connection.commit()
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class SectorManager:
    """Manages sector-related database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def add_sector(self, name: str, description: str = None, relevance_reason: str = None) -> int:
        """Add a new sector to the database."""
        with self.db_manager._connection_lock:
            cursor = self.db_manager.connection.cursor()
            cursor.execute('''
                INSERT INTO sectors (name, description, relevance_reason)
                VALUES (?, ?, ?)
            ''', (name, description, relevance_reason))
            sector_id = cursor.lastrowid
            self.db_manager.connection.commit()
            return sector_id
    
    def get_sector_by_name(self, name: str) -> Optional[Dict]:
        """Get sector information by name."""
        cursor = self.db_manager.connection.cursor()
        cursor.execute('''
            SELECT * FROM sectors 
            WHERE name = ? AND is_active = 1
        ''', (name,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_sectors(self) -> List[Dict]:
        """Get all active sectors."""
        cursor = self.db_manager.connection.cursor()
        cursor.execute('''
            SELECT * FROM sectors 
            WHERE is_active = 1 
            ORDER BY name
        ''')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_sector_by_id(self, sector_id: int) -> Optional[Dict]:
        """Get sector information by id."""
        cursor = self.db_manager.connection.cursor()
        cursor.execute('''
            SELECT * FROM sectors 
            WHERE id = ? AND is_active = 1
        ''', (sector_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


class CompanyProfileManager:
    """Manages company profile-related database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def add_company_profile(self, profile: Dict) -> int:
        """Add a new company profile to the database."""
        with self.db_manager._connection_lock:
            cursor = self.db_manager.connection.cursor()
            cursor.execute('''
                INSERT INTO company_profiles 
                (company_name, location, description, team_size, core_services, languages)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                profile['company_name'],
                profile['location'],
                profile['description'],
                profile['team_size'],
                json.dumps(profile['core_services']),
                json.dumps(profile['languages'])
            ))
            profile_id = cursor.lastrowid
            self.db_manager.connection.commit()
            return profile_id
    
    def get_company_profile_by_id(self, profile_id: int) -> Optional[Dict]:
        """Get company profile by id."""
        cursor = self.db_manager.connection.cursor()
        cursor.execute('''
            SELECT * FROM company_profiles 
            WHERE id = ? AND is_active = 1
        ''', (profile_id,))
        row = cursor.fetchone()
        if row:
            profile = dict(row)
            # Parse JSON arrays back to lists
            profile['core_services'] = json.loads(profile['core_services'])
            profile['languages'] = json.loads(profile['languages'])
            return profile
        return None
    
    def get_all_company_profiles(self) -> List[Dict]:
        """Get all active company profiles."""
        cursor = self.db_manager.connection.cursor()
        cursor.execute('''
            SELECT * FROM company_profiles 
            WHERE is_active = 1 
            ORDER BY created_at DESC
        ''')
        rows = cursor.fetchall()
        profiles = []
        for row in rows:
            profile = dict(row)
            # Parse JSON arrays back to lists
            profile['core_services'] = json.loads(profile['core_services'])
            profile['languages'] = json.loads(profile['languages'])
            profiles.append(profile)
        return profiles
    
    def update_company_profile(self, profile_id: int, profile: Dict) -> bool:
        """Update an existing company profile."""
        with self.db_manager._connection_lock:
            cursor = self.db_manager.connection.cursor()
            cursor.execute('''
                UPDATE company_profiles 
                SET company_name = ?, location = ?, description = ?, 
                    team_size = ?, core_services = ?, languages = ?, 
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
            ''', (
                profile['company_name'],
                profile['location'],
                profile['description'],
                profile['team_size'],
                json.dumps(profile['core_services']),
                json.dumps(profile['languages']),
                profile_id
            ))
            self.db_manager.connection.commit()
            return cursor.rowcount > 0
    
    def delete_company_profile(self, profile_id: int) -> bool:
        """Soft delete a company profile by setting is_active = 0."""
        with self.db_manager._connection_lock:
            cursor = self.db_manager.connection.cursor()
            cursor.execute('''
                UPDATE company_profiles 
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (profile_id,))
            self.db_manager.connection.commit()
            return cursor.rowcount > 0


class LeadManager:
    """Manages lead-related database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def add_lead(self, lead: Dict, discovered_by_profile_id: int = None, discovered_sectors: List[str] = None) -> int:
        """Add a new lead to the database."""
        with self.db_manager._connection_lock:
            cursor = self.db_manager.connection.cursor()
            cursor.execute('''
                INSERT INTO leads 
                (company_name, website_url, address, contact_email, phone_number, 
                 description, automation_proposal, discovered_by_profile_id, discovered_sectors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lead.get('company_name', ''),
                lead.get('website_url'),
                lead.get('address'),
                lead.get('contact_email'),
                lead.get('phone_number'),
                lead.get('description'),
                lead.get('automation_proposal'),
                discovered_by_profile_id,
                json.dumps(discovered_sectors) if discovered_sectors else None
            ))
            lead_id = cursor.lastrowid
            self.db_manager.connection.commit()
            return lead_id
    
    def add_leads_batch(self, leads: List[Dict], discovered_by_profile_id: int = None, discovered_sectors: List[str] = None) -> List[int]:
        """Add multiple leads to the database."""
        lead_ids = []
        with self.db_manager._connection_lock:
            cursor = self.db_manager.connection.cursor()
            for lead in leads:
                cursor.execute('''
                    INSERT INTO leads 
                    (company_name, website_url, address, contact_email, phone_number, 
                     description, automation_proposal, discovered_by_profile_id, discovered_sectors)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    lead.get('company_name', ''),
                    lead.get('website_url'),
                    lead.get('address'),
                    lead.get('contact_email'),
                    lead.get('phone_number'),
                    lead.get('description'),
                    lead.get('automation_proposal'),
                    discovered_by_profile_id,
                    json.dumps(discovered_sectors) if discovered_sectors else None
                ))
                lead_ids.append(cursor.lastrowid)
            self.db_manager.connection.commit()
        return lead_ids
    
    def get_lead_by_id(self, lead_id: int) -> Optional[Dict]:
        """Get lead by id."""
        cursor = self.db_manager.connection.cursor()
        cursor.execute('''
            SELECT * FROM leads 
            WHERE id = ? AND is_active = 1
        ''', (lead_id,))
        row = cursor.fetchone()
        if row:
            lead = dict(row)
            # Parse JSON arrays back to lists
            if lead.get('discovered_sectors'):
                lead['discovered_sectors'] = json.loads(lead['discovered_sectors'])
            return lead
        return None
    
    def get_all_leads(self) -> List[Dict]:
        """Get all active leads."""
        cursor = self.db_manager.connection.cursor()
        cursor.execute('''
            SELECT * FROM leads 
            WHERE is_active = 1 
            ORDER BY discovered_at DESC
        ''')
        rows = cursor.fetchall()
        leads = []
        for row in rows:
            lead = dict(row)
            # Parse JSON arrays back to lists
            if lead.get('discovered_sectors'):
                lead['discovered_sectors'] = json.loads(lead['discovered_sectors'])
            leads.append(lead)
        return leads
    
    def get_leads_by_profile(self, discovered_by_profile_id: int) -> List[Dict]:
        """Get leads discovered by a specific company profile."""
        cursor = self.db_manager.connection.cursor()
        cursor.execute('''
            SELECT * FROM leads 
            WHERE discovered_by_profile_id = ? AND is_active = 1 
            ORDER BY discovered_at DESC
        ''', (discovered_by_profile_id,))
        rows = cursor.fetchall()
        leads = []
        for row in rows:
            lead = dict(row)
            # Parse JSON arrays back to lists
            if lead.get('discovered_sectors'):
                lead['discovered_sectors'] = json.loads(lead['discovered_sectors'])
            leads.append(lead)
        return leads
    
    def get_leads_by_status(self, status: str) -> List[Dict]:
        """Get leads by status."""
        cursor = self.db_manager.connection.cursor()
        cursor.execute('''
            SELECT * FROM leads 
            WHERE status = ? AND is_active = 1 
            ORDER BY discovered_at DESC
        ''', (status,))
        rows = cursor.fetchall()
        leads = []
        for row in rows:
            lead = dict(row)
            # Parse JSON arrays back to lists
            if lead.get('discovered_sectors'):
                lead['discovered_sectors'] = json.loads(lead['discovered_sectors'])
            leads.append(lead)
        return leads
    
    def search_leads(self, search_term: str) -> List[Dict]:
        """Search leads by company name, description, or automation proposal."""
        cursor = self.db_manager.connection.cursor()
        search_pattern = f'%{search_term}%'
        cursor.execute('''
            SELECT * FROM leads 
            WHERE (company_name LIKE ? OR description LIKE ? OR automation_proposal LIKE ?) 
            AND is_active = 1 
            ORDER BY discovered_at DESC
        ''', (search_pattern, search_pattern, search_pattern))
        rows = cursor.fetchall()
        leads = []
        for row in rows:
            lead = dict(row)
            # Parse JSON arrays back to lists
            if lead.get('discovered_sectors'):
                lead['discovered_sectors'] = json.loads(lead['discovered_sectors'])
            leads.append(lead)
        return leads
    
    def update_lead_status(self, lead_id: int, status: str) -> bool:
        """Update lead status."""
        with self.db_manager._connection_lock:
            cursor = self.db_manager.connection.cursor()
            cursor.execute('''
                UPDATE leads 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
            ''', (status, lead_id))
            self.db_manager.connection.commit()
            return cursor.rowcount > 0
    
    def update_lead_priority(self, lead_id: int, priority: str) -> bool:
        """Update lead priority."""
        with self.db_manager._connection_lock:
            cursor = self.db_manager.connection.cursor()
            cursor.execute('''
                UPDATE leads 
                SET priority = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
            ''', (priority, lead_id))
            self.db_manager.connection.commit()
            return cursor.rowcount > 0
    
    def update_lead_notes(self, lead_id: int, notes: str) -> bool:
        """Update lead notes."""
        with self.db_manager._connection_lock:
            cursor = self.db_manager.connection.cursor()
            cursor.execute('''
                UPDATE leads 
                SET notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
            ''', (notes, lead_id))
            self.db_manager.connection.commit()
            return cursor.rowcount > 0
    
    def update_lead_fields(self, lead_id: int, status: str = None, priority: str = None, notes: str = None) -> bool:
        """Update specific lead fields (status, priority, notes) without affecting other fields."""
        with self.db_manager._connection_lock:
            cursor = self.db_manager.connection.cursor()
            
            # Build dynamic UPDATE query based on provided fields
            update_parts = []
            params = []
            
            if status is not None:
                update_parts.append("status = ?")
                params.append(status)
            
            if priority is not None:
                update_parts.append("priority = ?")
                params.append(priority)
            
            if notes is not None:
                update_parts.append("notes = ?")
                params.append(notes)
            
            if not update_parts:
                return False  # No fields to update
            
            update_parts.append("updated_at = CURRENT_TIMESTAMP")
            params.append(lead_id)
            
            query = f'''
                UPDATE leads 
                SET {', '.join(update_parts)}
                WHERE id = ? AND is_active = 1
            '''
            
            cursor.execute(query, params)
            self.db_manager.connection.commit()
            return cursor.rowcount > 0
    
    def update_lead(self, lead_id: int, lead_data: Dict) -> bool:
        """Update lead information."""
        with self.db_manager._connection_lock:
            cursor = self.db_manager.connection.cursor()
            cursor.execute('''
                UPDATE leads 
                SET company_name = ?, website_url = ?, address = ?, contact_email = ?, 
                    phone_number = ?, description = ?, automation_proposal = ?, 
                    status = ?, priority = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
            ''', (
                lead_data.get('company_name', ''),
                lead_data.get('website_url'),
                lead_data.get('address'),
                lead_data.get('contact_email'),
                lead_data.get('phone_number'),
                lead_data.get('description'),
                lead_data.get('automation_proposal'),
                lead_data.get('status', 'new'),
                lead_data.get('priority', 'medium'),
                lead_data.get('notes'),
                lead_id
            ))
            self.db_manager.connection.commit()
            return cursor.rowcount > 0
    
    def delete_lead(self, lead_id: int) -> bool:
        """Soft delete a lead by setting is_active = 0."""
        with self.db_manager._connection_lock:
            cursor = self.db_manager.connection.cursor()
            cursor.execute('''
                UPDATE leads 
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (lead_id,))
            self.db_manager.connection.commit()
            return cursor.rowcount > 0
    
    def get_lead_stats(self) -> Dict:
        """Get lead statistics."""
        cursor = self.db_manager.connection.cursor()
        
        # Total leads
        cursor.execute('SELECT COUNT(*) FROM leads WHERE is_active = 1')
        total_leads = cursor.fetchone()[0]
        
        # Leads by status
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM leads 
            WHERE is_active = 1 
            GROUP BY status
        ''')
        status_counts = dict(cursor.fetchall())
        
        # Leads by priority
        cursor.execute('''
            SELECT priority, COUNT(*) as count 
            FROM leads 
            WHERE is_active = 1 
            GROUP BY priority
        ''')
        priority_counts = dict(cursor.fetchall())
        
        # Recent leads (last 30 days)
        cursor.execute('''
            SELECT COUNT(*) 
            FROM leads 
            WHERE is_active = 1 
            AND discovered_at >= datetime('now', '-30 days')
        ''')
        recent_leads = cursor.fetchone()[0]
        
        return {
            'total_leads': total_leads,
            'status_counts': status_counts,
            'priority_counts': priority_counts,
            'recent_leads': recent_leads
        }


def get_or_create_sector(db_manager: DatabaseManager, name: str, description: str = None, 
                        relevance_reason: str = None) -> Dict:
    """Get a sector if it exists, or create it if it doesn't."""
    sector_manager = SectorManager(db_manager)
    sector = sector_manager.get_sector_by_name(name)
    
    if sector:
        return sector
    
    sector_id = sector_manager.add_sector(name, description, relevance_reason)
    return sector_manager.get_sector_by_id(sector_id)


# Example usage
if __name__ == "__main__":
    with DatabaseManager() as db:
        sector_mgr = SectorManager(db)
        profile_mgr = CompanyProfileManager(db)
        lead_mgr = LeadManager(db)
        
        # Add example sector
        try:
            sector_mgr.add_sector(
                name="Property Management",
                description="Companies that manage properties",
                relevance_reason="High lead generation potential"
            )
            print("Added sector: Property Management")
        except sqlite3.IntegrityError:
            print("Sector already exists")
        
        # Add example company profile
        example_profile = {
            "company_name": "AutoAI Solutions",
            "location": "Zurich, Switzerland",
            "description": "Tailored software solutions including AI integration.",
            "team_size": 5,
            "core_services": ["process automation", "AI integration"],
            "languages": ["English", "German"]
        }
        
        try:
            profile_id = profile_mgr.add_company_profile(example_profile)
            print(f"Added company profile with ID: {profile_id}")
        except Exception as e:
            print(f"Error adding profile: {e}")
        
        # Add example lead
        example_lead = {
            "company_name": "Example Company",
            "website_url": "https://example.com",
            "address": "123 Main St, Zurich",
            "contact_email": "contact@example.com",
            "phone_number": "+41 123 456 789",
            "description": "An example company for testing",
            "automation_proposal": "This company could benefit from process automation"
        }
        
        try:
            lead_id = lead_mgr.add_lead(example_lead, profile_id, ["Property Management"])
            print(f"Added lead with ID: {lead_id}")
        except Exception as e:
            print(f"Error adding lead: {e}")
        
        # Get all sectors
        sectors = sector_mgr.get_all_sectors()
        print(f"Total sectors: {len(sectors)}")
        for sector in sectors:
            print(f"- {sector['name']}: {sector['description']}")
        
        # Get all company profiles
        profiles = profile_mgr.get_all_company_profiles()
        print(f"Total company profiles: {len(profiles)}")
        for profile in profiles:
            print(f"- {profile['company_name']}: {profile['location']}")
        
        # Get all leads
        leads = lead_mgr.get_all_leads()
        print(f"Total leads: {len(leads)}")
        for lead in leads:
            print(f"- {lead['company_name']}: {lead['status']}")
        
        # Get lead statistics
        stats = lead_mgr.get_lead_stats()
        print(f"Lead statistics: {stats}")
