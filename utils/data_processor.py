import pandas as pd
import numpy as np
from typing import List, Dict, Any
import re
from datetime import datetime, timedelta
import streamlit as st

class DataProcessor:
    """Process and clean use case data for analysis"""
    
    def __init__(self):
        self.processed_data = {}
    
    def process_use_cases(self, raw_data: List[Dict]) -> Dict[str, Any]:
        """
        Process raw use case data into structured format
        
        Args:
            raw_data: List of raw use case dictionaries
            
        Returns:
            Dictionary containing processed data and metadata
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(raw_data)
            
            # Clean data - remove rows with missing essential fields
            if 'title' in df.columns:
                df = df.dropna(subset=['title'])  # Remove rows without titles
                df = df[df['title'].astype(str).str.strip() != '']  # Remove rows with empty titles
                df = df[df['title'].astype(str) != 'nan']  # Remove rows with 'nan' as title
                df = df[df['title'].notna()]  # Remove NaN titles
            
            # Simple data processing without complex operations
            df_processed = df.copy()
            
            # Derive business unit from teams_involved data
            def get_primary_business_unit(teams_involved):
                if isinstance(teams_involved, list) and teams_involved:
                    # Filter out empty/nan values from teams
                    valid_teams = [team for team in teams_involved if team and str(team).strip() != '' and str(team).lower() != 'nan']
                    if valid_teams:
                        return valid_teams[0]  # Use first valid team as primary business unit
                return 'General'
            
            # Use actual data from API fields
            df_processed['business_unit'] = df_processed['teams_involved'].apply(get_primary_business_unit)
            df_processed['status'] = 'Submitted'
            
            # Use actual priority from importance field
            def map_priority(importance):
                if isinstance(importance, str):
                    importance_lower = importance.lower()
                    if 'high' in importance_lower or 'critical' in importance_lower:
                        return 'High'
                    elif 'low' in importance_lower:
                        return 'Low'
                    else:
                        return 'Medium'
                return 'Medium'
            
            df_processed['priority'] = df_processed['importance'].apply(map_priority)
            
            # Keep ROI estimate data but don't calculate estimated values
            # ROI analysis will be done through the concrete ROI calculator
            df_processed['systems'] = df_processed['systems_involved']
            
            # Extract submitter name from submitter dict
            def extract_submitter_name(submitter):
                if isinstance(submitter, dict):
                    name = submitter.get('full_name', 'Unknown')
                    return name if name and str(name).strip() != '' and str(name).lower() != 'nan' else 'Unknown'
                if submitter and str(submitter).strip() != '' and str(submitter).lower() != 'nan':
                    return str(submitter)
                return 'Unknown'
            
            df_processed['submitter'] = df_processed['submitter'].apply(extract_submitter_name)
            df_processed['submission_date'] = df_processed['timestamp']
            df_processed['effort_estimate'] = 'Unknown'
            
            # Extract metadata
            metadata = self._extract_metadata(df_processed)
            
            return {
                'dataframe': df_processed,
                'business_units': metadata['business_units'],
                'priorities': metadata['priorities'],
                'systems': metadata['systems'],
                'summary': metadata['summary']
            }
            
        except Exception as e:
            st.error(f"Error processing data: {str(e)}")
            return {
                'dataframe': pd.DataFrame(),
                'business_units': [],
                'priorities': [],
                'systems': [],
                'summary': {}
            }
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize the dataframe"""
        df_clean = df.copy()
        
        # Standardize column names (handle various naming conventions)
        column_mapping = {
            # Title variations
            'use_case_title': 'title',
            'usecase_title': 'title',
            'name': 'title',
            'case_title': 'title',
            
            # Description variations
            'use_case_description': 'description',
            'desc': 'description',
            'details': 'description',
            
            # Submitter variations
            'submitted_by': 'submitter',
            'author': 'submitter',
            'requester': 'submitter',
            'user': 'submitter',
            
            # Business unit variations
            'bu': 'business_unit',
            'department': 'business_unit',
            'team': 'business_unit',
            'org': 'business_unit',
            
            # Status variations
            'current_status': 'status',
            'state': 'status',
            
            # Priority variations
            'priority_level': 'priority',
            'importance': 'priority',
            'criticality': 'priority',
            
            # ROI variations (keeping roi_estimate as raw data)
            # ROI analysis will be done through concrete ROI calculator
            
            # Systems variations
            'involved_systems': 'systems',
            'system_list': 'systems',
            'technologies': 'systems',
            'tools': 'systems',
            'systems_involved': 'systems',
            
            # Date variations
            'created_date': 'submission_date',
            'submitted_date': 'submission_date',
            'date_created': 'submission_date',
            'timestamp': 'submission_date',
            
            # Effort variations
            'estimated_effort': 'effort_estimate',
            'effort_hours': 'effort_estimate',
            'complexity': 'effort_estimate',
            'complexity_factors': 'effort_estimate'
        }
        
        # Apply column mapping
        df_clean = df_clean.rename(columns=column_mapping)
        
        # Handle submitter data extraction (do this after adding method)
        # Will be processed in _standardize_data_types
        
        # Handle business unit derivation from submitter or other data
        if 'business_unit' not in df_clean.columns:
            df_clean['business_unit'] = 'General'
        
        # Ensure required columns exist with defaults
        required_columns = {
            'title': 'Untitled Use Case',
            'description': 'No description provided',
            'submitter': 'Unknown',
            'business_unit': 'General',
            'status': 'Submitted',
            'priority': 'Medium',
            'systems': [],
            'submission_date': None,
            'effort_estimate': 'Unknown'
        }
        
        for col, default_value in required_columns.items():
            if col not in df_clean.columns:
                df_clean[col] = default_value
        
        # Clean and standardize data types
        df_clean = self._standardize_data_types(df_clean)
        
        return df_clean
    
    def _standardize_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize data types and clean values"""
        df_clean = df.copy()
        
        # Clean string columns with simple processing
        string_columns = ['title', 'description', 'submitter', 'business_unit', 'status', 'priority']
        for col in string_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].fillna('Unknown').astype(str)
        
        # Keep ROI estimate as raw data for concrete ROI calculator
        # No processing of estimated ROI values
        
        # Process systems from actual data
        if 'systems_involved' in df_clean.columns:
            for idx, row in df_clean.iterrows():
                systems_val = row.get('systems_involved', [])
                if isinstance(systems_val, list):
                    df_clean.at[idx, 'systems'] = systems_val
                else:
                    df_clean.at[idx, 'systems'] = []
        
        # Derive business units from title content
        if 'business_unit' in df_clean.columns:
            for idx, row in df_clean.iterrows():
                title = str(row.get('title', '')).lower()
                if 'timecard' in title or 'ps team' in title:
                    df_clean.at[idx, 'business_unit'] = 'Professional Services'
                elif 'support' in title or 'customer' in title:
                    df_clean.at[idx, 'business_unit'] = 'Support'
                elif 'contract' in title or 'revenue' in title:
                    df_clean.at[idx, 'business_unit'] = 'Finance'
                elif 'marketing' in title or 'marketo' in title:
                    df_clean.at[idx, 'business_unit'] = 'Marketing'
                else:
                    df_clean.at[idx, 'business_unit'] = 'General'
        
        # Keep business units as assigned (General for all)
        
        return df_clean
    
    def _standardize_business_unit(self, value: str) -> str:
        """Standardize business unit names"""
        if pd.isna(value) or value is None:
            return 'Unknown'
        
        value_str = str(value).lower().strip()
        if value_str in ['nan', 'none', '']:
            return 'Unknown'
        
        value = str(value).strip().title()
        
        # Common business unit mappings
        bu_mappings = {
            'It': 'IT',
            'Hr': 'HR',
            'R&D': 'R&D',
            'Rd': 'R&D',
            'Sales & Marketing': 'Sales',
            'Marketing': 'Sales',
            'Customer Service': 'Support',
            'Customer Support': 'Support',
            'Finance & Accounting': 'Finance',
            'Accounting': 'Finance',
            'Operations': 'Operations',
            'Engineering': 'Engineering',
            'Product': 'Product'
        }
        
        return bu_mappings.get(value, value)
    
    def _standardize_status(self, value: str) -> str:
        """Standardize status values"""
        if pd.isna(value) or value is None:
            return 'Submitted'
        
        value_str = str(value).lower().strip()
        
        if value_str in ['', 'nan', 'none']:
            return 'Submitted'
        
        status_mappings = {
            'new': 'Submitted',
            'pending': 'Under Review',
            'review': 'Under Review',
            'reviewing': 'Under Review',
            'in_review': 'Under Review',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'declined': 'Rejected',
            'in_progress': 'In Progress',
            'development': 'In Progress',
            'implementing': 'In Progress',
            'completed': 'Completed',
            'done': 'Completed',
            'closed': 'Completed',
            'cancelled': 'Cancelled',
            'canceled': 'Cancelled',
            'on_hold': 'On Hold',
            'paused': 'On Hold'
        }
        
        return status_mappings.get(value_str, 'Submitted')
    
    def _standardize_priority(self, value: str) -> str:
        """Standardize priority values"""
        if pd.isna(value) or value is None:
            return 'Medium'
        
        value_str = str(value).lower().strip()
        
        if value_str in ['', 'nan', 'none']:
            return 'Medium'
        
        if 'high' in value_str or 'urgent' in value_str or 'critical' in value_str:
            return 'High'
        elif 'low' in value_str or 'nice-to-have' in value_str or 'optional' in value_str:
            return 'Low'
        else:
            return 'Medium'
    
    def _clean_roi_value(self, value: Any) -> float:
        """Clean and convert ROI values to float"""
        if pd.isna(value) or value is None:
            return 0.0
        
        # Handle dictionary format from API (roi_estimate can be a dict)
        if isinstance(value, dict):
            # Look for common ROI keys in the dictionary
            for key in ['value', 'estimate', 'percentage', 'roi']:
                if key in value:
                    return self._clean_roi_value(value[key])
            # If no numeric value found, return 0
            return 0.0
        
        # Handle string descriptions (like "High", "Medium", "Low")
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if 'high' in value_lower:
                return 150.0  # Assign high ROI estimate
            elif 'medium' in value_lower:
                return 75.0   # Assign medium ROI estimate
            elif 'low' in value_lower:
                return 25.0   # Assign low ROI estimate
        
        # Convert to string and clean numeric values
        value_str = str(value).strip().replace('%', '').replace(',', '')
        
        # Extract numeric value
        numeric_match = re.search(r'(\d+\.?\d*)', value_str)
        if numeric_match:
            try:
                roi_value = float(numeric_match.group(1))
                # If value seems to be in decimal format (0.15 for 15%), convert to percentage
                if roi_value <= 1.0 and '.' in numeric_match.group(1):
                    roi_value *= 100
                return max(0, min(roi_value, 1000))  # Cap at 1000%
            except ValueError:
                return 0.0
        
        return 0.0
    
    def _clean_systems_list(self, value: Any) -> List[str]:
        """Clean and standardize systems list"""
        if pd.isna(value) or value is None:
            return []
        
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        
        if isinstance(value, str):
            # Handle comma-separated, semicolon-separated, or pipe-separated values
            separators = [',', ';', '|', '\n']
            systems = [value]
            
            for sep in separators:
                if sep in value:
                    systems = value.split(sep)
                    break
            
            return [system.strip() for system in systems if system.strip()]
        
        return []
    
    def _clean_date(self, value: Any) -> str:
        """Clean and standardize date values"""
        if pd.isna(value) or value is None:
            return 'Unknown'
        
        try:
            # Try to parse various date formats
            if isinstance(value, str):
                # Common date formats
                date_formats = [
                    '%Y-%m-%d',
                    '%m/%d/%Y',
                    '%d/%m/%Y',
                    '%Y-%m-%d %H:%M:%S',
                    '%m/%d/%Y %H:%M:%S'
                ]
                
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(value, fmt)
                        return parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
                
                return value  # Return original if no format matches
            
            return str(value)
        except Exception:
            return 'Unknown'
    
    def _extract_metadata(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract metadata from cleaned dataframe"""
        # Extract all unique teams from teams_involved for business unit filter
        all_teams = set()
        for teams_list in df['teams_involved']:
            if isinstance(teams_list, list):
                all_teams.update(teams_list)
        
        metadata = {
            'business_units': sorted(list(all_teams)) if all_teams else ['General'],
            'priorities': ['High', 'Medium', 'Low'],  # Standardized order
            'systems': [],
            'summary': {}
        }
        
        # Extract all unique systems
        all_systems = set()
        for systems_list in df['systems']:
            if isinstance(systems_list, list):
                all_systems.update(systems_list)
        metadata['systems'] = sorted(list(all_systems))
        
        # Generate summary statistics
        metadata['summary'] = {
            'total_use_cases': len(df),
            'total_systems': len(metadata['systems']),
            'business_units_count': len(metadata['business_units'])
        }
        
        return metadata
    
    def _extract_submitter_info(self, value: Any) -> str:
        """Extract submitter information from various formats"""
        if pd.isna(value) or value is None:
            return 'Unknown'
        
        if isinstance(value, dict):
            # Look for common submitter keys
            for key in ['name', 'email', 'user', 'slack_user_id', 'username']:
                if key in value and value[key]:
                    return str(value[key])
            return 'Unknown'
        
        return str(value).strip() if str(value).strip() else 'Unknown'
    
    def _derive_business_unit_from_content(self, row) -> str:
        """Derive business unit from available data"""
        # Look for business unit clues in title or description
        title = str(row.get('title', '')).lower()
        description = str(row.get('description', '')).lower()
        
        # Common business unit keywords
        if any(keyword in title + description for keyword in ['finance', 'accounting', 'revenue']):
            return 'Finance'
        elif any(keyword in title + description for keyword in ['support', 'customer', 'help']):
            return 'Support'
        elif any(keyword in title + description for keyword in ['sales', 'marketing', 'marketo']):
            return 'Sales & Marketing'
        elif any(keyword in title + description for keyword in ['hr', 'human resources']):
            return 'HR'
        elif any(keyword in title + description for keyword in ['engineering', 'development', 'technical']):
            return 'Engineering'
        elif any(keyword in title + description for keyword in ['operations', 'ops']):
            return 'Operations'
        elif any(keyword in title + description for keyword in ['professional services', 'ps team']):
            return 'Professional Services'
        else:
            return 'General'
