import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import json

from utils.api_client import SnapLogicAPIClient
from utils.data_processor import DataProcessor
from utils.visualizations import create_overlap_charts, create_roi_charts
from utils.roi_calculator import ConcreteROICalculator
from utils.database_storage import ROIStorage

# Page configuration
st.set_page_config(
    page_title="SnapLogic AI Center of Excellence Dashboard",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'use_cases_data' not in st.session_state:
    st.session_state.use_cases_data = None
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'auto_load_attempted' not in st.session_state:
    st.session_state.auto_load_attempted = False

def load_data():
    """Load data from SnapLogic API"""
    try:
        with st.spinner("Loading use cases from SnapLogic API..."):
            api_client = SnapLogicAPIClient()
            data = api_client.fetch_use_cases()
            
            if data:
                processor = DataProcessor()
                processed_data = processor.process_use_cases(data)
                
                st.session_state.use_cases_data = data
                st.session_state.processed_data = processed_data
                st.session_state.data_loaded = True
                st.success(f"Successfully loaded {len(data)} use cases!")
                return True
            else:
                st.error("No data received from API")
                return False
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return False

def main():
    # Custom CSS styling to match SnapLogic branding
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    
    .snaplogic-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #4285F4 100%);
        padding: 2rem 3rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
        text-align: left;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .snaplogic-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: white;
        letter-spacing: -0.02em;
    }
    
    .snaplogic-subtitle {
        font-size: 1.2rem;
        font-weight: 400;
        color: #e0e7ff;
        margin-bottom: 0;
    }
    
    .agentcreator-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.2);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        margin-top: 1rem;
        backdrop-filter: blur(10px);
    }
    
    div[data-testid="metric-container"] {
        background-color: white;
        border: 1px solid #e5e7eb;
        padding: 1.2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 4px solid #4285F4;
    }
    
    .sidebar .sidebar-content {
        background-color: #f8fafc;
    }
    
    .stSelectbox > div > div {
        background-color: white;
        border-radius: 8px;
    }
    
    .stMultiSelect > div > div {
        background-color: white;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        margin-bottom: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9;
        border-radius: 8px;
        color: #475569;
        font-weight: 500;
        padding: 0.75rem 1.5rem !important;
        min-width: 120px;
        height: auto !important;
        white-space: nowrap;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4285F4 !important;
        color: white !important;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 1rem;
    }
    
    .stExpander {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Auto-load data on first visit
    if not st.session_state.data_loaded and not st.session_state.auto_load_attempted:
        st.session_state.auto_load_attempted = True
        load_data()
    
    # Main content - check data loading status first
    if not st.session_state.data_loaded:
        # SnapLogic branded header for loading state
        st.markdown("""
        <div class="snaplogic-header">
            <h1 class="snaplogic-title">SnapLogic AI Center of Excellence</h1>
            <p class="snaplogic-subtitle">Interactive dashboard for analyzing submitted AgentCreator use cases</p>
            <div class="agentcreator-badge">✨ AgentCreator Analytics</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("Loading use cases automatically... Please wait.")
        with col2:
            if st.button("🔄 Refresh Data"):
                st.session_state.data_loaded = False
                st.session_state.use_cases_data = None
                st.session_state.processed_data = None
                st.session_state.auto_load_attempted = False
                st.rerun()
        return
    
    # Get cleaned data for navigation
    df = st.session_state.processed_data['dataframe'].copy()
    
    # Additional data cleaning for display
    df = df[df['title'].notna()]  # Remove any remaining NaN titles
    df = df[df['title'].str.strip() != '']  # Remove empty titles
    df = df[~df['title'].str.lower().isin(['nan', 'unknown', 'null'])]  # Remove problematic values
    
    # Create tabs for navigation
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview", 
        "💰 ROI Analysis",
        "📋 Use Cases List", 
        "🔄 Overlap Analysis", 
        "📤 Export",
        "⚙️ Settings"
    ])
    
    with tab1:
        # SnapLogic branded header in Overview tab
        st.markdown("""
        <div class="snaplogic-header">
            <h1 class="snaplogic-title">SnapLogic AI Center of Excellence</h1>
            <p class="snaplogic-subtitle">Interactive dashboard for analyzing submitted AgentCreator use cases</p>
            <div class="agentcreator-badge">✨ AgentCreator Analytics</div>
        </div>
        """, unsafe_allow_html=True)
        
        display_overview(df)
    
    with tab2:
        display_roi_analysis(df)
    
    with tab3:
        display_use_cases_list(df)
    
    with tab4:
        display_overlap_analysis(df)
    
    with tab5:
        display_export_options(df)
    
    with tab6:
        st.subheader("⚙️ Dashboard Settings")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**Data Management**")
            
            # Data loading controls
            if st.button("🔄 Refresh Data", type="primary"):
                st.session_state.data_loaded = False
                st.session_state.use_cases_data = None
                st.session_state.processed_data = None
                st.session_state.auto_load_attempted = False
                st.success("Data will be refreshed on next page load")
                st.rerun()
            
            if st.button("📥 Force Reload Data"):
                load_data()
                st.success("Data reloaded successfully")
                st.rerun()
        
        with col2:
            st.write("**System Status**")
            
            if st.session_state.data_loaded:
                st.success("✅ Data loaded")
                total_cases = len(df)
                st.metric("Total Use Cases", total_cases)
            else:
                st.error("❌ No data loaded")
            
            # Database status
            try:
                from utils.database_storage import ROIStorage
                test_storage = ROIStorage()
                st.success("✅ Database connected")
                test_storage.close()
            except:
                st.error("❌ Database offline")

def display_overview(df):
    """Display overview metrics and charts"""
    if df.empty:
        st.warning("No data matches the current filters")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Use Cases", len(df))
    
    with col2:
        unique_business_units = df['business_unit'].nunique()
        st.metric("Business Units", unique_business_units)
    
    with col3:
        high_priority = len(df[df['priority'] == 'High'])
        st.metric("High Priority Cases", high_priority)
    
    with col4:
        unique_systems = df['systems'].apply(lambda x: len(x) if isinstance(x, list) else 0).sum()
        st.metric("Total Systems Involved", unique_systems)
    
    st.divider()
    
    # Charts row 1
    col1, col2 = st.columns(2)
    
    with col1:
        # Business unit distribution
        bu_counts = df['business_unit'].value_counts()
        fig_bu = px.bar(
            x=bu_counts.index, 
            y=bu_counts.values,
            title="Use Cases by Business Unit"
        )
        fig_bu.update_layout(xaxis_title="Business Unit", yaxis_title="Count")
        st.plotly_chart(fig_bu, use_container_width=True, key="overview_bu_chart")
    
    with col2:
        # Status distribution
        status_counts = df['status'].value_counts()
        fig_status = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Use Cases by Status"
        )
        st.plotly_chart(fig_status, use_container_width=True, key="overview_status_chart")
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        # Priority distribution
        priority_counts = df['priority'].value_counts()
        fig_priority = px.bar(
            x=priority_counts.index, 
            y=priority_counts.values,
            title="Use Cases by Priority",
            color=priority_counts.index,
            color_discrete_map={'High': 'red', 'Medium': 'orange', 'Low': 'green'}
        )
        fig_priority.update_layout(xaxis_title="Priority", yaxis_title="Count")
        st.plotly_chart(fig_priority, use_container_width=True, key="overview_priority_chart")
    
    with col2:
        # Systems complexity analysis
        system_counts = df['systems'].apply(lambda x: len(x) if isinstance(x, list) else 0)
        fig_systems = px.histogram(
            x=system_counts,
            title="Systems Integration Complexity",
            nbins=10
        )
        fig_systems.update_layout(xaxis_title="Number of Systems", yaxis_title="Count")
        st.plotly_chart(fig_systems, use_container_width=True, key="overview_systems_complexity")

def display_use_cases_list(df):
    """Display searchable and filterable list of use cases"""
    if df.empty:
        st.warning("No data matches the current filters")
        return
    
    st.subheader("Use Cases Details")
    
    # Search functionality
    search_term = st.text_input("🔍 Search use cases (title, description, submitter)")
    
    if search_term:
        mask = (
            df['title'].str.contains(search_term, case=False, na=False) |
            df['description'].str.contains(search_term, case=False, na=False) |
            df['submitter'].str.contains(search_term, case=False, na=False)
        )
        df_filtered = df[mask]
    else:
        df_filtered = df
    
    st.write(f"Showing {len(df_filtered)} of {len(df)} use cases")
    
    # Display use cases as expandable cards
    for idx, row in df_filtered.iterrows():
        with st.expander(f"🎯 {row['title']} - {row['business_unit']} ({row['priority']} Priority)"):
            
            # Basic Information Section
            st.markdown("### 📋 Basic Information")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Title:** {row['title']}")
                st.write(f"**Business Unit:** {row['business_unit']}")
                st.write(f"**Priority:** {row['priority']}")
            with col2:
                st.write(f"**Data Sensitivity:** {row.get('data_sensitivity', 'Not specified')}")
                st.write(f"**Submitted:** {row.get('timestamp', 'Unknown')}")
                st.write(f"**Use Case Submitted:** {row.get('use_case_submitted', 'Unknown')}")
                st.write(f"**Submitter:** {row.get('submitter', 'Unknown')}")
            
            st.divider()
            
            # Description Section
            st.markdown("### 📝 Description & Problem")
            st.write("**Description:**")
            st.write(row.get('description', 'No description provided'))
            
            if row.get('long_description') and str(row.get('long_description')).strip() and str(row.get('long_description')) != 'nan':
                st.write("**Long Description:**")
                st.write(row['long_description'])
            
            if row.get('business_problem') and str(row.get('business_problem')).strip() and str(row.get('business_problem')) != 'nan':
                st.write("**Business Problem:**")
                st.write(row['business_problem'])
            
            if row.get('proposed_solution') and str(row.get('proposed_solution')).strip() and str(row.get('proposed_solution')) != 'nan':
                st.write("**Proposed Solution:**")
                st.write(row['proposed_solution'])
            
            st.divider()
            
            # Process & Requirements Section
            st.markdown("### ⚙️ Process & Requirements")
            if row.get('current_process') and str(row.get('current_process')).strip() and str(row.get('current_process')) != 'nan':
                st.write("**Current Process:**")
                if isinstance(row['current_process'], list):
                    for step in row['current_process']:
                        st.write(f"• {step}")
                else:
                    st.write(row['current_process'])
            
            if row.get('challenges') and isinstance(row['challenges'], list) and len(row['challenges']) > 0:
                st.write("**Challenges:**")
                for challenge in row['challenges']:
                    st.write(f"• {challenge}")
            
            if row.get('pain_points') and isinstance(row['pain_points'], list) and len(row['pain_points']) > 0:
                st.write("**Pain Points:**")
                for pain in row['pain_points']:
                    st.write(f"• {pain}")
            
            st.divider()
            
            # Systems & Teams Section
            st.markdown("### 🔧 Systems & Teams")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Systems Involved:**")
                if isinstance(row.get('systems'), list) and row['systems']:
                    for system in row['systems']:
                        st.write(f"• {system}")
                elif isinstance(row.get('systems_involved'), list) and row['systems_involved']:
                    for system in row['systems_involved']:
                        st.write(f"• {system}")
                else:
                    st.write("No systems specified")
            
            with col2:
                if row.get('teams_involved') and isinstance(row['teams_involved'], list) and len(row['teams_involved']) > 0:
                    st.write("**Teams Involved:**")
                    for team in row['teams_involved']:
                        st.write(f"• {team}")
                
                if row.get('teams_benefited') and isinstance(row['teams_benefited'], list) and len(row['teams_benefited']) > 0:
                    st.write("**Teams Benefited:**")
                    for team in row['teams_benefited']:
                        st.write(f"• {team}")
            
            st.divider()
            
            # Benefits & ROI Section
            st.markdown("### 💰 Benefits & ROI")
            if row.get('potential_benefits') and isinstance(row['potential_benefits'], list) and len(row['potential_benefits']) > 0:
                st.write("**Potential Benefits:**")
                for benefit in row['potential_benefits']:
                    st.write(f"• {benefit}")
            
            if row.get('roi_estimate') and str(row.get('roi_estimate')).strip() and str(row.get('roi_estimate')) != 'nan':
                st.write("**ROI Estimate:**")
                roi_estimate = row['roi_estimate']
                if isinstance(roi_estimate, dict):
                    for key, value in roi_estimate.items():
                        if isinstance(value, list):
                            st.write(f"**{key.replace('_', ' ').title()}:**")
                            for item in value:
                                st.write(f"• {item}")
                        else:
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                else:
                    st.write(roi_estimate)
            
            st.divider()
            
            # Task Details Section
            st.markdown("### 📊 Task Details")
            col1, col2 = st.columns(2)
            
            with col1:
                if row.get('task_frequency') and str(row.get('task_frequency')).strip() and str(row.get('task_frequency')) != 'nan':
                    st.write(f"**Task Frequency:** {row['task_frequency']}")
                
                if row.get('task_volume') and str(row.get('task_volume')).strip() and str(row.get('task_volume')) != 'nan':
                    st.write(f"**Task Volume:** {row['task_volume']}")
                
                if row.get('is_manual_today') is not None:
                    st.write(f"**Currently Manual:** {'Yes' if row['is_manual_today'] else 'No'}")
            
            with col2:
                if row.get('criticality') and str(row.get('criticality')).strip() and str(row.get('criticality')) != 'nan':
                    st.write(f"**Criticality:** {row['criticality']}")
                
                if row.get('importance') and str(row.get('importance')).strip() and str(row.get('importance')) != 'nan':
                    st.write(f"**Importance:** {row['importance']}")
                
                if row.get('use_case_category') and str(row.get('use_case_category')).strip() and str(row.get('use_case_category')) != 'nan':
                    st.write(f"**Category:** {row['use_case_category']}")
            
            # Additional Information
            if row.get('complexity_factors') and isinstance(row['complexity_factors'], list) and len(row['complexity_factors']) > 0:
                st.write("**Complexity Factors:**")
                for factor in row['complexity_factors']:
                    st.write(f"• {factor}")
            
            if row.get('process_recording') and str(row.get('process_recording')).strip() and str(row.get('process_recording')) != 'nan':
                st.write(f"**Process Recording:** {row['process_recording']}")
            
            if row.get('recording_shared') is not None:
                st.write(f"**Recording Shared:** {'Yes' if row['recording_shared'] else 'No'}")
            
            if row.get('does_problem_exist_outside_of_snaplogic') is not None:
                st.write(f"**Problem Exists Outside SnapLogic:** {'Yes' if row['does_problem_exist_outside_of_snaplogic'] else 'No'}")

def display_overlap_analysis(df):
    """Display overlap analysis based on systems and business units"""
    if df.empty:
        st.warning("No data matches the current filters")
        return
    
    st.subheader("Overlap Analysis")
    
    # Systems overlap analysis
    st.write("### Systems Overlap Analysis")
    
    # Extract all systems and count occurrences
    all_systems = []
    for systems_list in df['systems']:
        if isinstance(systems_list, list):
            all_systems.extend(systems_list)
    
    if all_systems:
        systems_df = pd.DataFrame({'system': all_systems})
        system_counts = systems_df['system'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top systems chart
            fig_systems = px.bar(
                x=system_counts.head(10).values,
                y=system_counts.head(10).index,
                orientation='h',
                title="Top 10 Most Common Systems"
            )
            fig_systems.update_layout(xaxis_title="Number of Use Cases", yaxis_title="System")
            st.plotly_chart(fig_systems, use_container_width=True)
        
        with col2:
            # Systems overlap heatmap
            create_overlap_charts(df, st)
    else:
        st.info("No systems data available for overlap analysis")
    
    st.divider()
    
    # Business unit collaboration matrix
    st.write("### Business Unit Collaboration Opportunities")
    
    # Create business unit vs systems matrix
    bu_systems_matrix = []
    for _, row in df.iterrows():
        bu = row['business_unit']
        systems = row['systems'] if isinstance(row['systems'], list) else []
        for system in systems:
            bu_systems_matrix.append({'business_unit': bu, 'system': system})
    
    if bu_systems_matrix:
        bu_systems_df = pd.DataFrame(bu_systems_matrix)
        pivot_table = bu_systems_df.groupby(['business_unit', 'system']).size().to_frame('count').reset_index()
        
        # Create heatmap
        fig_heatmap = px.density_heatmap(
            pivot_table,
            x='system',
            y='business_unit',
            z='count',
            title="Business Unit - System Usage Heatmap"
        )
        fig_heatmap.update_layout(height=400)
        st.plotly_chart(fig_heatmap, use_container_width=True, key="overlap_heatmap")
    
    # Potential collaboration recommendations
    st.write("### Collaboration Recommendations")
    
    # Find use cases with similar systems
    system_similarities = []
    use_cases_list = df.to_dict('records')
    
    for i, case1 in enumerate(use_cases_list):
        for j, case2 in enumerate(use_cases_list[i+1:], i+1):
            systems1 = set(case1['systems']) if isinstance(case1['systems'], list) else set()
            systems2 = set(case2['systems']) if isinstance(case2['systems'], list) else set()
            
            if systems1 and systems2:
                overlap = len(systems1.intersection(systems2))
                if overlap > 0:
                    system_similarities.append({
                        'case1': case1['title'],
                        'case2': case2['title'],
                        'bu1': case1['business_unit'],
                        'bu2': case2['business_unit'],
                        'overlap_count': overlap,
                        'common_systems': list(systems1.intersection(systems2))
                    })
    
    if system_similarities:
        # Sort by overlap count and display top recommendations
        system_similarities.sort(key=lambda x: x['overlap_count'], reverse=True)
        
        st.write("**Top Collaboration Opportunities:**")
        for sim in system_similarities[:5]:
            if sim['bu1'] != sim['bu2']:  # Only show cross-BU opportunities
                st.write(f"• **{sim['case1']}** ({sim['bu1']}) ↔ **{sim['case2']}** ({sim['bu2']})")
                st.write(f"  Common systems: {', '.join(sim['common_systems'])}")
    else:
        st.info("No significant overlap found between use cases")



def display_roi_analysis(df):
    """Display concrete ROI analysis for use cases"""
    if df.empty:
        st.warning("No data matches the current filters")
        return
    
    st.subheader("💰 ROI Analysis")
    
    # Initialize ROI calculator and database storage
    roi_calculator = ConcreteROICalculator()
    
    # Initialize database storage
    try:
        roi_storage = ROIStorage()
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        st.info("ROI inputs will only be stored for this session.")
        roi_storage = None
    
    # Load saved ROI inputs from database for consolidated summary
    consolidated_roi_data = {}
    if roi_storage:
        try:
            consolidated_roi_data = roi_storage.load_all_roi_inputs()
        except Exception as e:
            st.warning(f"Could not load ROI data for consolidated summary: {e}")
    
    # Also include session state ROI data for real-time updates
    session_roi_data = st.session_state.get('roi_inputs', {})
    
    # Combine database and session data (session takes precedence)
    all_roi_data = consolidated_roi_data.copy()
    all_roi_data.update(session_roi_data)
    
    # Display Consolidated ROI Summary at the top
    if all_roi_data:
        with st.expander("📊 Consolidated ROI Summary", expanded=True):
            col_header1, col_header2 = st.columns([3, 1])
            with col_header1:
                st.markdown("**Summary of all use cases with completed ROI analysis**")
            with col_header2:
                if st.button("🔄 Refresh Summary", help="Update summary with latest ROI calculations"):
                    st.rerun()
            
            total_annual_benefits = 0
            total_implementation_costs = 0
            roi_summary_data = []
            
            for case_title, inputs in all_roi_data.items():
                # Skip cases with no meaningful data (all None/0 values for key fields)
                key_fields = ['labor_impact_hours', 'cost_avoidance_annual', 'revenue_impact_annual']
                has_data = any(inputs.get(field) not in [None, 0, ''] for field in key_fields)
                
                # Also check if time_to_value_hours is provided for implementation cost calculation
                has_implementation_data = inputs.get('time_to_value_hours') not in [None, 0, '']
                
                if has_data:
                    # Calculate ROI for each case
                    results = roi_calculator.calculate_roi_with_inputs(inputs)
                    if results:
                        annual_benefit = results.get('annual_benefit', 0)
                        impl_cost = results.get('implementation_cost', 0)
                        net_benefit = annual_benefit - impl_cost
                        roi_percentage = results.get('annual_roi_percentage', 0)
                        
                        total_annual_benefits += annual_benefit
                        total_implementation_costs += impl_cost
                        
                        monthly_benefit = results.get('monthly_benefit', 0)
                        strategic_value = results.get('strategic_value', 0)
                        
                        # Handle cases where implementation cost is 0
                        impl_cost_display = f"${impl_cost:,.0f}" if impl_cost > 0 else "Not Set"
                        roi_display = f"{roi_percentage:.1f}%" if impl_cost > 0 and roi_percentage != float('inf') else "N/A"
                        
                        roi_summary_data.append({
                            'Use Case': case_title,
                            'Monthly Benefit': f"${monthly_benefit:,.0f}",
                            'Annual Benefit': f"${annual_benefit:,.0f}",
                            'Implementation Cost': impl_cost_display,
                            'Net Annual Benefit': f"${net_benefit:,.0f}",
                            'ROI %': roi_display,
                            'Strategic Value': f"{strategic_value:.1f}/5"
                        })
            
            if roi_summary_data:
                # Overall metrics
                total_net_benefit = total_annual_benefits - total_implementation_costs
                overall_roi = (total_net_benefit / total_implementation_costs * 100) if total_implementation_costs > 0 else 0
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Annual Benefits", f"${total_annual_benefits:,.0f}")
                with col2:
                    st.metric("Total Implementation Cost", f"${total_implementation_costs:,.0f}")
                with col3:
                    st.metric("Total Net Annual Benefit", f"${total_net_benefit:,.0f}")
                with col4:
                    st.metric("Portfolio ROI", f"{overall_roi:.1f}%")
                
                st.divider()
                
                # Summary table with sorting capability
                summary_df = pd.DataFrame(roi_summary_data)
                
                # Add sorting options
                col1, col2 = st.columns([3, 1])
                with col2:
                    sort_by = st.selectbox(
                        "Sort by:",
                        options=['Use Case', 'Monthly Benefit', 'Annual Benefit', 'Net Annual Benefit', 'ROI %', 'Strategic Value'],
                        index=2,  # Default to Annual Benefit
                        key="roi_summary_sort"
                    )
                    
                    sort_ascending = st.checkbox("Ascending", value=False, key="roi_summary_ascending")
                
                # Sort the dataframe
                if sort_by in ['Monthly Benefit', 'Annual Benefit', 'Net Annual Benefit']:
                    # Remove $ and , for numeric sorting
                    summary_df[f'{sort_by}_numeric'] = summary_df[sort_by].str.replace('[$,]', '', regex=True).astype(float)
                    summary_df_sorted = summary_df.sort_values(f'{sort_by}_numeric', ascending=sort_ascending)
                    summary_df_sorted = summary_df_sorted.drop(columns=[f'{sort_by}_numeric'])
                elif sort_by == 'ROI %':
                    # Handle ROI % with N/A values
                    summary_df['ROI_numeric'] = summary_df['ROI %'].replace('N/A', '0').str.replace('%', '').astype(float)
                    summary_df_sorted = summary_df.sort_values('ROI_numeric', ascending=sort_ascending)
                    summary_df_sorted = summary_df_sorted.drop(columns=['ROI_numeric'])
                elif sort_by == 'Strategic Value':
                    # Handle Strategic Value format (X.X/5)
                    summary_df['Strategic_numeric'] = summary_df['Strategic Value'].str.split('/').str[0].astype(float)
                    summary_df_sorted = summary_df.sort_values('Strategic_numeric', ascending=sort_ascending)
                    summary_df_sorted = summary_df_sorted.drop(columns=['Strategic_numeric'])
                else:
                    # Text sorting
                    summary_df_sorted = summary_df.sort_values(sort_by, ascending=sort_ascending)
                
                st.dataframe(summary_df_sorted, use_container_width=True, hide_index=True)
            else:
                st.info("No completed ROI analyses found")
    else:
        st.info("📊 **Consolidated ROI Summary**\n\nComplete ROI analysis for individual use cases to see consolidated portfolio summary here.")
    
    st.divider()
    
    # Store all use case inputs in session state
    if 'roi_inputs' not in st.session_state:
        st.session_state.roi_inputs = {}
        
        # Load existing ROI inputs from database if available
        if roi_storage:
            try:
                saved_inputs = roi_storage.load_all_roi_inputs()
                st.session_state.roi_inputs.update(saved_inputs)
                if saved_inputs:
                    st.success(f"Loaded saved ROI inputs for {len(saved_inputs)} use cases from database")
            except Exception as e:
                st.warning(f"Could not load saved ROI inputs: {e}")
    
    # Make use case selection more prominent
    st.markdown("---")
    st.markdown("### 🎯 Select Use Case for Analysis")
    st.markdown("**Choose a use case below to perform detailed ROI calculations:**")
    
    # ROI Management Controls
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if roi_storage:
            # Show saved ROI inputs management
            if st.button("🗂️ Manage Saved Data", help="View and manage saved ROI inputs"):
                st.session_state.show_roi_management = not st.session_state.get('show_roi_management', False)
    
    # ROI Management Panel
    if roi_storage and st.session_state.get('show_roi_management', False):
        with st.expander("📊 Saved ROI Inputs Management", expanded=True):
            saved_cases = roi_storage.get_saved_use_cases()
            
            if saved_cases:
                st.write(f"**{len(saved_cases)} use cases with saved ROI inputs:**")
                
                # Display saved cases with delete option
                for case_title in saved_cases:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"• {case_title}")
                    with col2:
                        if st.button("🗑️", key=f"delete_{case_title}", help="Delete saved ROI inputs"):
                            if roi_storage.delete_roi_inputs(case_title):
                                # Remove from session state too
                                if case_title in st.session_state.roi_inputs:
                                    del st.session_state.roi_inputs[case_title]
                                st.success(f"Deleted ROI inputs for {case_title}")
                                st.rerun()
                
                # Bulk operations
                st.divider()
                if st.button("🔄 Reload All from Database"):
                    try:
                        saved_inputs = roi_storage.load_all_roi_inputs()
                        st.session_state.roi_inputs.update(saved_inputs)
                        st.success(f"Reloaded {len(saved_inputs)} saved ROI inputs")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to reload: {e}")
            else:
                st.info("No saved ROI inputs found in database")
        
        st.divider()
    
    # Create a selectbox for choosing which use case to analyze
    use_case_options = []
    for idx, row in df.iterrows():
        use_case_options.append(f"{row['title']} ({row['business_unit']})")
    
    if not use_case_options:
        st.warning("No use cases available for ROI analysis")
        return
    
    selected_option = st.selectbox(
        "📋 **Select Use Case:**",
        use_case_options,
        key="roi_use_case_selector",
        help="Choose which use case you want to analyze for ROI calculations"
    )
    
    st.info("💡 **Tip:** After selecting a use case, scroll down to enter ROI inputs in the calculator section below.")
    
    # Get the selected use case data
    selected_idx = use_case_options.index(selected_option)
    selected_row = df.iloc[selected_idx]
    use_case_title = selected_row['title']
    use_case_data = selected_row.to_dict()
    
    # Extract initial inputs from API
    initial_inputs = roi_calculator.extract_roi_inputs_from_api(use_case_data)
    
    # Initialize session state for this use case if not exists
    if use_case_title not in st.session_state.roi_inputs:
        st.session_state.roi_inputs[use_case_title] = initial_inputs
    
    st.divider()
    
    # Side panel layout: Use case details on left, calculator on right
    left_panel, right_panel = st.columns([1, 1])
    
    with left_panel:
        st.write("### 📋 Use Case Details")
        
        # Basic Information Section
        st.markdown("#### 📋 Basic Information")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Title:** {selected_row['title']}")
            st.write(f"**Business Unit:** {selected_row['business_unit']}")
            st.write(f"**Priority:** {selected_row['priority']}")
        with col2:
            st.write(f"**Data Sensitivity:** {selected_row.get('data_sensitivity', 'Not specified')}")
            st.write(f"**Submitted:** {selected_row.get('timestamp', 'Unknown')}")
            st.write(f"**Submitter:** {selected_row.get('submitter', 'Unknown')}")
        
        st.divider()
        
        # Description Section
        st.markdown("#### 📝 Description & Problem")
        st.write("**Description:**")
        st.write(selected_row.get('description', 'No description provided'))
        
        if selected_row.get('long_description') and str(selected_row.get('long_description')).strip() and str(selected_row.get('long_description')) != 'nan':
            st.write("**Long Description:**")
            st.write(selected_row['long_description'])
        
        if selected_row.get('business_problem') and str(selected_row.get('business_problem')).strip() and str(selected_row.get('business_problem')) != 'nan':
            st.write("**Business Problem:**")
            st.write(selected_row['business_problem'])
        
        if selected_row.get('proposed_solution') and str(selected_row.get('proposed_solution')).strip() and str(selected_row.get('proposed_solution')) != 'nan':
            st.write("**Proposed Solution:**")
            st.write(selected_row['proposed_solution'])
        
        st.divider()
        
        # Process & Requirements Section
        st.markdown("#### ⚙️ Process & Requirements")
        if selected_row.get('current_process') and str(selected_row.get('current_process')).strip() and str(selected_row.get('current_process')) != 'nan':
            st.write("**Current Process:**")
            if isinstance(selected_row['current_process'], list):
                for step in selected_row['current_process']:
                    st.write(f"• {step}")
            else:
                st.write(selected_row['current_process'])
        
        if selected_row.get('challenges') and isinstance(selected_row['challenges'], list) and len(selected_row['challenges']) > 0:
            st.write("**Challenges:**")
            for challenge in selected_row['challenges']:
                st.write(f"• {challenge}")
        
        if selected_row.get('pain_points') and isinstance(selected_row['pain_points'], list) and len(selected_row['pain_points']) > 0:
            st.write("**Pain Points:**")
            for pain in selected_row['pain_points']:
                st.write(f"• {pain}")
        
        st.divider()
        
        # Systems & Teams Section
        st.markdown("#### 🔧 Systems & Teams")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Systems Involved:**")
            if isinstance(selected_row.get('systems'), list) and selected_row['systems']:
                for system in selected_row['systems']:
                    st.write(f"• {system}")
            elif isinstance(selected_row.get('systems_involved'), list) and selected_row['systems_involved']:
                for system in selected_row['systems_involved']:
                    st.write(f"• {system}")
            else:
                st.write("No systems specified")
        
        with col2:
            if selected_row.get('teams_involved') and isinstance(selected_row['teams_involved'], list) and len(selected_row['teams_involved']) > 0:
                st.write("**Teams Involved:**")
                for team in selected_row['teams_involved']:
                    st.write(f"• {team}")
            
            if selected_row.get('teams_benefited') and isinstance(selected_row['teams_benefited'], list) and len(selected_row['teams_benefited']) > 0:
                st.write("**Teams Benefited:**")
                for team in selected_row['teams_benefited']:
                    st.write(f"• {team}")
        
        st.divider()
        
        # Benefits & ROI Section
        st.markdown("#### 💰 Benefits & ROI")
        if selected_row.get('potential_benefits') and isinstance(selected_row['potential_benefits'], list) and len(selected_row['potential_benefits']) > 0:
            st.write("**Potential Benefits:**")
            for benefit in selected_row['potential_benefits']:
                st.write(f"• {benefit}")
        
        if selected_row.get('roi_estimate') and str(selected_row.get('roi_estimate')).strip() and str(selected_row.get('roi_estimate')) != 'nan':
            st.write("**ROI Estimate:**")
            roi_estimate = selected_row['roi_estimate']
            if isinstance(roi_estimate, dict):
                for key, value in roi_estimate.items():
                    if isinstance(value, list):
                        st.write(f"**{key.replace('_', ' ').title()}:**")
                        for item in value:
                            st.write(f"• {item}")
                    else:
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")
            else:
                st.write(roi_estimate)
        
        st.divider()
        
        # Task Details Section
        st.markdown("#### 📊 Task Details")
        col1, col2 = st.columns(2)
        
        with col1:
            if selected_row.get('task_frequency') and str(selected_row.get('task_frequency')).strip() and str(selected_row.get('task_frequency')) != 'nan':
                st.write(f"**Task Frequency:** {selected_row['task_frequency']}")
            
            if selected_row.get('task_volume') and str(selected_row.get('task_volume')).strip() and str(selected_row.get('task_volume')) != 'nan':
                st.write(f"**Task Volume:** {selected_row['task_volume']}")
            
            if selected_row.get('is_manual_today') is not None:
                st.write(f"**Currently Manual:** {'Yes' if selected_row['is_manual_today'] else 'No'}")
        
        with col2:
            if selected_row.get('criticality') and str(selected_row.get('criticality')).strip() and str(selected_row.get('criticality')) != 'nan':
                st.write(f"**Criticality:** {selected_row['criticality']}")
            
            if selected_row.get('importance') and str(selected_row.get('importance')).strip() and str(selected_row.get('importance')) != 'nan':
                st.write(f"**Importance:** {selected_row['importance']}")
            
            if selected_row.get('use_case_category') and str(selected_row.get('use_case_category')).strip() and str(selected_row.get('use_case_category')) != 'nan':
                st.write(f"**Category:** {selected_row['use_case_category']}")
        
        # Additional Information
        if selected_row.get('complexity_factors') and isinstance(selected_row['complexity_factors'], list) and len(selected_row['complexity_factors']) > 0:
            st.write("**Complexity Factors:**")
            for factor in selected_row['complexity_factors']:
                st.write(f"• {factor}")
        
        if selected_row.get('process_recording') and str(selected_row.get('process_recording')).strip() and str(selected_row.get('process_recording')) != 'nan':
            st.write(f"**Process Recording:** {selected_row['process_recording']}")
        
        if selected_row.get('recording_shared') is not None:
            st.write(f"**Recording Shared:** {'Yes' if selected_row['recording_shared'] else 'No'}")
        
        if selected_row.get('does_problem_exist_outside_of_snaplogic') is not None:
            st.write(f"**Problem Exists Outside SnapLogic:** {'Yes' if selected_row['does_problem_exist_outside_of_snaplogic'] else 'No'}")
    
    with right_panel:
        st.write("### 🔧 ROI Calculator")
        
        # Create unique keys for inputs
        key_prefix = f"roi_calc_{selected_idx}"
        
        # Impact - Cost Savings
        st.write("**Impact - Cost Savings**")
        labor_hours = st.number_input(
            "FTE hours saved/month",
            value=float(st.session_state.roi_inputs[use_case_title].get('labor_impact_hours') or 0),
            min_value=0.0,
            help="Hours saved per month from automation",
            key=f"{key_prefix}_labor_hours"
        )
        
        labor_rate = st.number_input(
            "Labor cost ($/hour)",
            value=float(st.session_state.roi_inputs[use_case_title].get('labor_cost_hourly') or 100),
            min_value=0.0,
            help="Blended hourly rate for affected roles",
            key=f"{key_prefix}_labor_rate"
        )
        
        cost_avoidance = st.number_input(
            "Hard cost avoidance ($/year)",
            value=float(st.session_state.roi_inputs[use_case_title].get('cost_avoidance_annual') or 0),
            min_value=0.0,
            help="Annual licenses, penalties, etc. saved",
            key=f"{key_prefix}_cost_avoidance"
        )
        
        # Impact - Revenue Generated
        st.write("**Impact - Revenue Generated**")
        revenue_annual = st.number_input(
            "Direct revenue generated ($/year)",
            value=float(st.session_state.roi_inputs[use_case_title].get('revenue_impact_annual') or 0),
            min_value=0.0,
            help="Annual new revenue directly attributable to this solution",
            key=f"{key_prefix}_revenue"
        )
        
        # Impact - Risk & Referenceability
        st.write("**Impact - Risk & Referenceability**")
        risk_score = st.slider(
            "Risk mitigation (1-5 scale)",
            min_value=1,
            max_value=5,
            value=int(st.session_state.roi_inputs[use_case_title].get('risk_mitigation_score') or 3),
            help="1=no impact, 3=moderate risk avoided, 5=major regulatory/risk avoided",
            key=f"{key_prefix}_risk"
        )
        
        customer_reach = st.slider(
            "Customer reach (1-5 scale)",
            min_value=1,
            max_value=5,
            value=int(st.session_state.roi_inputs[use_case_title].get('customer_reach_score') or 3),
            help="1=internal only, 3=moderate reach, 5=highly applicable and visible to customers",
            key=f"{key_prefix}_customer"
        )
        
        # Effort - Implementation
        st.write("**Effort - Implementation**")
        time_to_value = st.number_input(
            "Time to develop and release (hours)",
            value=float(st.session_state.roi_inputs[use_case_title].get('time_to_value_hours') or 0),
            min_value=0.0,
            help="Total person hours from discovery to enablement",
            key=f"{key_prefix}_time"
        )
        
        impl_rate = st.number_input(
            "Implementation cost ($/hour)",
            value=float(st.session_state.roi_inputs[use_case_title].get('implementation_cost_hourly') or 100),
            min_value=0.0,
            help="Blended hourly rate for implementation team",
            key=f"{key_prefix}_impl_rate"
        )
        
        confidence = st.slider(
            "Confidence level (1-5 scale)",
            min_value=1,
            max_value=5,
            value=int(st.session_state.roi_inputs[use_case_title].get('confidence_level') or 3),
            help="Requirements understood; data sources defined; repeatable pattern",
            key=f"{key_prefix}_confidence"
        )
    
    # Update session state with current values
    updated_inputs = {
        'labor_impact_hours': labor_hours,
        'labor_cost_hourly': labor_rate,
        'cost_avoidance_annual': cost_avoidance,
        'revenue_impact_annual': revenue_annual,
        'risk_mitigation_score': risk_score,
        'customer_reach_score': customer_reach,
        'time_to_value_hours': time_to_value,
        'implementation_cost_hourly': impl_rate,
        'confidence_level': confidence
    }
    
    st.session_state.roi_inputs[use_case_title].update(updated_inputs)
    
    # Auto-save to database if available
    if roi_storage:
        try:
            roi_storage.save_roi_inputs(
                use_case_title, 
                updated_inputs, 
                selected_row['business_unit']
            )
        except Exception as e:
            st.error(f"Failed to save ROI inputs to database: {e}")
    
    # Calculate and display ROI results
    roi_metrics = roi_calculator.calculate_roi_with_inputs(st.session_state.roi_inputs[use_case_title])
    
    st.divider()
    
    # ROI Results Summary - full width below the side panels
    st.write("### 📊 ROI Results for Selected Use Case")
    
    result_col1, result_col2, result_col3, result_col4 = st.columns(4)
    
    with result_col1:
        st.metric("Monthly Benefit", f"${roi_metrics['monthly_benefit']:,.0f}")
    
    with result_col2:
        payback = roi_metrics['payback_period_months']
        payback_text = f"{payback:.1f} months" if payback != float('inf') else "∞"
        st.metric("Payback Period", payback_text)
    
    with result_col3:
        st.metric("Annual ROI", f"{roi_metrics['annual_roi_percentage']:.1f}%")
    
    with result_col4:
        st.metric("Strategic Value", f"{roi_metrics['strategic_value']:.1f}/5")
    
    # Detailed breakdown
    with st.expander("Show detailed breakdown"):
        detail_col1, detail_col2 = st.columns(2)
        with detail_col1:
            st.write(f"**Labor Savings:** ${roi_metrics['labor_savings_monthly']:,.0f}/month")
            st.write(f"**Cost Avoidance:** ${roi_metrics['cost_avoidance_monthly']:,.0f}/month")
        with detail_col2:
            st.write(f"**Revenue Generated:** ${roi_metrics['revenue_monthly']:,.0f}/month")
            st.write(f"**Implementation Cost:** ${roi_metrics['implementation_cost']:,.0f}")
    
    # ROI Framework Information - moved under card interface
    st.write("### ROI Framework Structure")
    
    with st.expander("View ROI Framework Details"):
        st.write("**Impact Categories:**")
        st.write("• **Cost Savings:** Labor Impact (FTE hours/month) + Labor Cost ($/hour) + Cost Avoidance ($/month)")
        st.write("• **Revenue Generated:** Direct net new revenue generated ($/month)")
        st.write("• **Risk Avoided:** Regulatory/compliance exposure reduction (1-5 scale)")
        st.write("• **Referenceability:** Customer resonance and visibility (1-5 scale)")
        
        st.write("**Effort Categories:**")
        st.write("• **Implementation Costs:** Time to Value (hours) + Cost of Implementation ($/hour)")
        
        st.write("**Confidence:**")
        st.write("• Requirements understanding, data source definition, repeatability (1-5 scale)")
        
        st.write("**Exact Formulas Used:**")
        st.code("Monthly Benefit = (FTE hours saved × Avg hourly rate) + (Costs Saved / 12) + (Revenue Generated / 12)")
        st.code("Payback Period = (Time to value * Avg hourly rate) / Monthly Benefit") 
        st.code("Annual ROI = ((12 × Monthly Benefit) – (Time to value * Avg hourly rate)) / (Time to value * Avg Hourly rate)")
        st.code("Strategic Value = (Risk Mitigation Score + Customer reach + Confidence) / 3")
    



def display_export_options(df):
    """Display data export options"""
    if df.empty:
        st.warning("No data matches the current filters")
        return
    
    st.subheader("Export Filtered Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Export Options")
        
        # CSV export
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📄 Download as CSV",
            data=csv_data,
            file_name=f"snaplogic_use_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # JSON export
        json_data = df.to_json(orient='records', indent=2)
        st.download_button(
            label="📋 Download as JSON",
            data=json_data,
            file_name=f"snaplogic_use_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col2:
        st.write("### Export Summary")
        st.write(f"**Filtered Records**: {len(df)}")
        st.write(f"**Total Columns**: {len(df.columns)}")
        st.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Column information
        st.write("**Available Columns**:")
        for col in df.columns:
            st.write(f"• {col}")

if __name__ == "__main__":
    main()
