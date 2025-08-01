import requests
import streamlit as st
import json
from typing import List, Dict, Optional

class SnapLogicAPIClient:
    """Client for interacting with SnapLogic API"""
    
    def __init__(self):
        self.base_url = "https://elastic.snaplogic.com/api/1/rest/slsched/feed/SLoS_Dev/AI_CoE_Operations/usecase_operations/get_submitted_usecases_task"
        self.bearer_token = "DjTsEOLU1tgZ0YW0lEFeseyuw56vrLdD"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def fetch_use_cases(_self) -> Optional[List[Dict]]:
        """
        Fetch use cases from SnapLogic API
        
        Returns:
            List of use case dictionaries or None if error
        """
        try:
            # Make API request with bearer token as query parameter
            url_with_token = f"{_self.base_url}?bearer_token={_self.bearer_token}"
            
            # Debug info removed for cleaner UI
            
            response = requests.get(
                url_with_token,
                headers=_self.headers,
                timeout=30,
                verify=True  # Ensure SSL verification
            )
            
            # Check response status
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    # Look for common keys that might contain the use cases array
                    for key in ['data', 'use_cases', 'results', 'items']:
                        if key in data and isinstance(data[key], list):
                            return data[key]
                    # If no array found, wrap single object in list
                    return [data]
                else:
                    st.error(f"Unexpected data format received: {type(data)}")
                    return None
                    
            elif response.status_code == 401:
                st.error("❌ Authentication failed. Please check the bearer token.")
                return None
            elif response.status_code == 404:
                st.error("❌ API endpoint not found. Please verify the URL.")
                return None
            elif response.status_code == 403:
                st.error("❌ Access forbidden. Please check permissions.")
                return None
            else:
                st.error(f"❌ API request failed with status {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            st.error("❌ Request timed out. Please try again.")
            return None
        except requests.exceptions.ConnectionError as e:
            st.error(f"❌ Connection error: {str(e)}")
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Request error: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON response: {str(e)}")
            return None
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            return None
    
    def validate_api_response(self, data: List[Dict]) -> bool:
        """
        Validate the structure of API response data
        
        Args:
            data: List of use case dictionaries
            
        Returns:
            Boolean indicating if data is valid
        """
        if not isinstance(data, list):
            return False
        
        if len(data) == 0:
            st.warning("⚠️ API returned empty dataset")
            return False
        
        # Check if each item has basic required fields
        required_fields = ['title', 'description', 'submitter']
        
        for i, item in enumerate(data[:5]):  # Check first 5 items
            if not isinstance(item, dict):
                st.warning(f"⚠️ Item {i} is not a dictionary")
                return False
            
            missing_fields = [field for field in required_fields if field not in item]
            if missing_fields:
                st.warning(f"⚠️ Item {i} missing fields: {missing_fields}")
                # Don't return False here as some fields might be optional
        
        return True
