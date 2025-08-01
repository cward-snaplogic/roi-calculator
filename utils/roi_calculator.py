import pandas as pd
import numpy as np
from typing import Dict, Any, List

class ConcreteROICalculator:
    """Calculate ROI based on the Concrete ROI Option framework from Excel"""
    
    def __init__(self):
        # Default rates from Excel template
        self.blended_hourly_rate = 100.0  # From Excel: Blended Hourly
        
        # Excel framework structure - exact field mappings
        self.roi_structure = {
            'impact': {
                'cost_savings': {
                    'labor_impact': {'description': 'FTE hours saved/month', 'unit': 'Hours', 'value': None},
                    'labor_cost_saved': {'description': 'Avg loaded cost per FTE - role / dept ave', 'unit': '$/hour', 'value': 100.0},
                    'cost_avoidance': {'description': 'Hard costs saved - licenses, penalties, etc.', 'unit': '$/month', 'value': None}
                },
                'revenue_generated': {
                    'revenue_impact': {'description': 'Direct net new revenue generated', 'unit': '$/month', 'value': None}
                },
                'risk_avoided': {
                    'risk_mitigation': {'description': 'Reduces regulatory or compliance exposure', 'unit': '1-5 scale', 'value': None}
                },
                'referenceability': {
                    'customer_reach': {'description': 'Resonates with customers', 'unit': '1-5 scale', 'value': None}
                }
            },
            'effort': {
                'implementation_costs': {
                    'time_to_value': {'description': 'Time to develop and release', 'unit': 'Hours', 'value': None},
                    'cost_of_implementation': {'description': 'Avg loaded cost per FTE - role / dept ave', 'unit': '$/hour', 'value': 100.0}
                }
            },
            'confidence': {
                'confidence_level': {'description': 'Requirements understood; data sources defined; repeatable pattern', 'unit': '%', 'value': None}
            }
        }
    
    def extract_roi_inputs_from_api(self, use_case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract actual input values from API data without making assumptions"""
        
        # Initialize with blank values - only populate what's clearly available
        inputs = {
            'title': use_case_data.get('title', ''),
            'business_unit': use_case_data.get('business_unit', ''),
            
            # Impact - Cost Savings
            'labor_impact_hours': None,  # FTE hours saved/month - not directly in API
            'labor_cost_hourly': self.blended_hourly_rate,  # Default from Excel
            'cost_avoidance_annual': None,  # Hard costs saved annually - not directly in API
            
            # Impact - Revenue Generated  
            'revenue_impact_annual': None,  # Direct revenue annually - not directly in API
            
            # Impact - Risk Avoided
            'risk_mitigation_score': None,  # 1-5 scale - not directly in API
            
            # Impact - Referenceability
            'customer_reach_score': None,  # 1-5 scale - not directly in API
            
            # Effort - Implementation Costs
            'time_to_value_hours': None,  # Implementation time - not directly in API
            'implementation_cost_hourly': self.blended_hourly_rate,  # Default from Excel
            
            # Confidence
            'confidence_level': None,  # Requirements understanding (1-5 scale) - not directly in API
            
            # Available API fields for reference
            'api_systems_involved': use_case_data.get('systems_involved', []),
            'api_roi_estimate': use_case_data.get('roi_estimate', {}),
            'api_task_frequency': use_case_data.get('task_frequency', ''),
            'api_task_volume': use_case_data.get('task_volume', ''),
            'api_importance': use_case_data.get('importance', ''),
            'api_description': use_case_data.get('description', ''),
            'api_current_process': use_case_data.get('current_process', ''),
            'api_teams_involved': use_case_data.get('teams_involved', [])
        }
        
        return inputs
    
    def calculate_roi_with_inputs(self, inputs: Dict[str, Any]) -> Dict[str, float]:
        """Calculate ROI metrics using exact formulas specified"""
        
        # Get input values, defaulting to 0 if None
        fte_hours_saved = inputs.get('labor_impact_hours') or 0
        avg_hourly_rate = inputs.get('labor_cost_hourly') or self.blended_hourly_rate
        costs_saved_annual = inputs.get('cost_avoidance_annual') or 0  # Already annual
        revenue_generated_annual = inputs.get('revenue_impact_annual') or 0  # Already annual
        time_to_value_hours = inputs.get('time_to_value_hours') or 0
        
        # Monthly Benefit = (FTE hours saved × Avg hourly rate) + (Costs Saved / 12) + (Revenue Generated / 12)
        monthly_benefit = (fte_hours_saved * avg_hourly_rate) + (costs_saved_annual / 12) + (revenue_generated_annual / 12)
        
        # Implementation cost = Time to value * Avg hourly rate
        implementation_cost = time_to_value_hours * avg_hourly_rate
        
        # Payback Period = (Time to value * Avg hourly rate) / Monthly Benefit
        payback_months = implementation_cost / max(monthly_benefit, 0.01) if monthly_benefit > 0 else float('inf')
        
        # Annual ROI = ((12 × Monthly Benefit) – (Time to value * Avg hourly rate)) / (Time to value * Avg Hourly rate)
        annual_roi = ((12 * monthly_benefit) - implementation_cost) / max(implementation_cost, 0.01) * 100 if implementation_cost > 0 else 0
        
        # Get confidence and risk scores
        confidence = inputs.get('confidence_level') or 0
        risk_score = inputs.get('risk_mitigation_score') or 0
        customer_reach = inputs.get('customer_reach_score') or 0
        
        # Strategic Value = (Risk Mitigation Score + Customer reach + Confidence) / 3
        # All values are on 1-5 scale
        strategic_value = (risk_score + customer_reach + confidence) / 3
        
        return {
            'labor_savings_monthly': fte_hours_saved * avg_hourly_rate,
            'cost_avoidance_monthly': costs_saved_annual / 12,
            'revenue_monthly': revenue_generated_annual / 12,
            'monthly_benefit': monthly_benefit,
            'annual_benefit': monthly_benefit * 12,
            'implementation_cost': implementation_cost,
            'payback_period_months': payback_months,
            'annual_roi_percentage': annual_roi,
            'confidence_score': confidence,
            'risk_mitigation_score': risk_score,
            'customer_reach_score': customer_reach,
            'strategic_value': strategic_value,
            'time_to_value_hours': time_to_value_hours,
            'fte_hours_saved': fte_hours_saved,
            'costs_saved_annual': costs_saved_annual,
            'revenue_generated_annual': revenue_generated_annual
        }
    
    def _estimate_fte_hours_saved(self, frequency: str, volume: str, is_manual: bool, process_steps: List) -> float:
        """Estimate FTE hours saved per month based on task characteristics"""
        if not is_manual:
            return 0
        
        base_hours = 0
        frequency_lower = str(frequency).lower()
        
        # Extract hours from process complexity
        process_complexity = len(process_steps) if isinstance(process_steps, list) else 1
        hours_per_execution = max(0.5, process_complexity * 0.5)  # 30 min to multiple hours
        
        # Calculate frequency multiplier
        if 'daily' in frequency_lower:
            executions_per_month = 22  # Working days
        elif 'weekly' in frequency_lower:
            executions_per_month = 4
        elif 'monthly' in frequency_lower:
            executions_per_month = 1
        elif 'quarterly' in frequency_lower:
            executions_per_month = 0.33
        else:
            executions_per_month = 2  # Default assumption
        
        # Extract volume multiplier from task_volume
        volume_multiplier = 1
        if isinstance(volume, str):
            # Look for numbers in volume description
            import re
            numbers = re.findall(r'\d+', volume)
            if numbers:
                volume_multiplier = min(int(numbers[0]), 50)  # Cap at 50 people
        
        base_hours = hours_per_execution * executions_per_month * min(volume_multiplier, 10)
        return min(base_hours, 200)  # Cap at 200 hours/month
    
    def _estimate_cost_avoidance(self, systems: List, roi_data: Dict) -> float:
        """Estimate annual cost avoidance"""
        if isinstance(roi_data, dict):
            # Look for cost-related benefits
            benefits = roi_data.get('benefits', [])
            if isinstance(benefits, list):
                for benefit in benefits:
                    if any(word in str(benefit).lower() for word in ['cost', 'saving', 'efficiency']):
                        return self.cost_per_system * 2  # Higher estimate for cost-related benefits
        
        # Base on systems complexity using configurable cost per system
        system_count = len(systems) if isinstance(systems, list) else 0
        if system_count >= 3:
            return self.cost_per_system * 2  # High integration = high cost avoidance
        elif system_count >= 2:
            return self.cost_per_system
        
        return self.cost_per_system * 0.4  # Default minimal cost avoidance
    
    def _estimate_revenue_generated(self, roi_data: Dict, systems: List) -> float:
        """Estimate annual revenue generated"""
        if isinstance(roi_data, dict):
            # Look for revenue-related benefits
            benefits = roi_data.get('benefits', [])
            if isinstance(benefits, list):
                for benefit in benefits:
                    if any(word in str(benefit).lower() for word in ['revenue', 'sales', 'customer']):
                        return self.revenue_per_customer_system * 2  # Higher estimate for revenue-related benefits
        
        # Customer-facing systems might generate revenue using configurable rate
        if isinstance(systems, list):
            customer_systems = ['salesforce', 'marketo', 'hubspot', 'zendesk']
            if any(system.lower() in str(systems).lower() for system in customer_systems):
                return self.revenue_per_customer_system
        
        return 0  # Default no revenue generation
    
    def _estimate_time_to_value(self, complexity_factors: List, systems: List) -> float:
        """Estimate implementation hours"""
        base_hours = 40  # 1 week baseline
        
        # Add complexity
        if isinstance(complexity_factors, list):
            complexity_hours = len(complexity_factors) * 20
        else:
            complexity_hours = 20
        
        # Add system integration complexity
        if isinstance(systems, list):
            system_hours = len(systems) * 30
        else:
            system_hours = 30
        
        total_hours = base_hours + complexity_hours + system_hours
        return min(total_hours, 1000)  # Cap at 1000 hours (6 months)
    
    def _calculate_risk_score(self, use_case_data: Dict) -> float:
        """Calculate risk mitigation score (1-5 scale)"""
        # Base on data sensitivity and compliance factors
        data_sensitivity = str(use_case_data.get('data_sensitivity', '')).lower()
        challenges = use_case_data.get('challenges', [])
        
        if 'high' in data_sensitivity or 'sensitive' in data_sensitivity:
            return 5.0  # High regulatory risk avoided
        elif isinstance(challenges, list) and any('compliance' in str(c).lower() for c in challenges):
            return 4.0
        elif 'moderate' in data_sensitivity:
            return 3.0
        
        return 2.0  # Minimal risk impact
    
    def _calculate_confidence_score(self, use_case_data: Dict) -> float:
        """Calculate confidence score (1-5 scale)"""
        # Base on documentation completeness and process clarity
        long_description = use_case_data.get('long_description', '')
        current_process = use_case_data.get('current_process', [])
        systems_involved = use_case_data.get('systems_involved', [])
        
        score = 1.0
        
        # Add points for documentation quality
        if len(str(long_description)) > 200:
            score += 1.5
        elif len(str(long_description)) > 100:
            score += 1.0
        
        # Add points for process definition
        if isinstance(current_process, list) and len(current_process) > 3:
            score += 1.5
        elif isinstance(current_process, list) and len(current_process) > 1:
            score += 1.0
        
        # Add points for system clarity
        if isinstance(systems_involved, list) and len(systems_involved) > 0:
            score += 1.0
        
        return min(score, 5.0)
    
    def _calculate_customer_reach_score(self, use_case_data: Dict) -> float:
        """Calculate customer reach score (1-5 scale)"""
        teams_benefited = use_case_data.get('teams_benefited', [])
        use_case_category = str(use_case_data.get('use_case_category', '')).lower()
        
        # Customer-facing categories get higher scores
        if any(word in use_case_category for word in ['customer', 'sales', 'marketing', 'support']):
            return 5.0
        
        # Multiple teams = broader reach
        if isinstance(teams_benefited, list) and len(teams_benefited) > 2:
            return 4.0
        elif isinstance(teams_benefited, list) and len(teams_benefited) > 1:
            return 3.0
        
        return 2.0  # Internal use primarily