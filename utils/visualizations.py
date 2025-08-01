import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from itertools import combinations
import streamlit as st
from typing import List, Dict, Any

def create_overlap_charts(df: pd.DataFrame, st_instance):
    """Create overlap analysis charts"""
    
    # Systems co-occurrence matrix
    systems_cooccurrence = create_systems_cooccurrence_matrix(df)
    
    if not systems_cooccurrence.empty:
        # Create heatmap for systems co-occurrence
        fig_cooccurrence = px.imshow(
            systems_cooccurrence.values,
            x=systems_cooccurrence.columns,
            y=systems_cooccurrence.index,
            title="Systems Co-occurrence Matrix",
            labels=dict(color="Co-occurrence Count"),
            aspect="auto"
        )
        fig_cooccurrence.update_layout(height=500)
        st_instance.plotly_chart(fig_cooccurrence, use_container_width=True, key="systems_cooccurrence")
        
        # Network diagram for system relationships
        create_systems_network_chart(df, st_instance)
    
    # Business unit overlap analysis
    create_business_unit_overlap_chart(df, st_instance)

def create_systems_cooccurrence_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Create a co-occurrence matrix for systems"""
    
    # Get all unique systems
    all_systems = set()
    for systems_list in df['systems']:
        if isinstance(systems_list, list):
            all_systems.update(systems_list)
    
    all_systems = sorted(list(all_systems))
    
    if not all_systems:
        return pd.DataFrame()
    
    # Create co-occurrence matrix
    cooccurrence_matrix = pd.DataFrame(0, index=all_systems, columns=all_systems)
    
    for systems_list in df['systems']:
        if isinstance(systems_list, list) and len(systems_list) > 1:
            # Count co-occurrences
            for system1, system2 in combinations(systems_list, 2):
                if system1 in all_systems and system2 in all_systems:
                    cooccurrence_matrix.loc[system1, system2] += 1
                    cooccurrence_matrix.loc[system2, system1] += 1
    
    return cooccurrence_matrix

def create_systems_network_chart(df: pd.DataFrame, st_instance):
    """Create a network chart showing system relationships"""
    
    # Prepare data for network chart
    edges = []
    node_sizes = {}
    
    # Count system usage
    for systems_list in df['systems']:
        if isinstance(systems_list, list):
            for system in systems_list:
                node_sizes[system] = node_sizes.get(system, 0) + 1
    
    # Find system pairs
    for systems_list in df['systems']:
        if isinstance(systems_list, list) and len(systems_list) > 1:
            for system1, system2 in combinations(systems_list, 2):
                edges.append((system1, system2))
    
    if not edges:
        st_instance.info("No system relationships found for network visualization")
        return
    
    # Count edge weights
    edge_weights = {}
    for edge in edges:
        edge_key = tuple(sorted(edge))
        edge_weights[edge_key] = edge_weights.get(edge_key, 0) + 1
    
    # Create network visualization (simplified as scatter plot with connections)
    # Note: For a full network graph, you'd typically use networkx + plotly, 
    # but keeping it simple for this implementation
    
    systems = list(node_sizes.keys())
    if len(systems) <= 20:  # Only show network for manageable number of systems
        # Create a simple force-directed layout
        positions = _calculate_simple_layout(systems, edge_weights)
        
        # Create scatter plot for nodes
        fig_network = go.Figure()
        
        # Add edges
        for (sys1, sys2), weight in edge_weights.items():
            if sys1 in positions and sys2 in positions:
                x1, y1 = positions[sys1]
                x2, y2 = positions[sys2]
                
                fig_network.add_trace(go.Scatter(
                    x=[x1, x2, None],
                    y=[y1, y2, None],
                    mode='lines',
                    line=dict(width=min(weight * 2, 10), color='lightgray'),
                    showlegend=False,
                    hoverinfo='none'
                ))
        
        # Add nodes
        x_coords = [positions[sys][0] for sys in systems if sys in positions]
        y_coords = [positions[sys][1] for sys in systems if sys in positions]
        sizes = [node_sizes[sys] * 10 for sys in systems if sys in positions]
        
        fig_network.add_trace(go.Scatter(
            x=x_coords,
            y=y_coords,
            mode='markers+text',
            marker=dict(size=sizes, color='lightblue', line=dict(width=2, color='darkblue')),
            text=[sys for sys in systems if sys in positions],
            textposition='middle center',
            hovertemplate='%{text}<br>Usage Count: %{marker.size}<extra></extra>',
            showlegend=False
        ))
        
        fig_network.update_layout(
            title="Systems Relationship Network",
            showlegend=False,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            height=500
        )
        
        st_instance.plotly_chart(fig_network, use_container_width=True, key="systems_network")

def _calculate_simple_layout(systems: List[str], edge_weights: Dict) -> Dict[str, tuple]:
    """Calculate simple circular layout for systems"""
    positions = {}
    n = len(systems)
    
    for i, system in enumerate(systems):
        angle = 2 * np.pi * i / n
        x = np.cos(angle)
        y = np.sin(angle)
        positions[system] = (x, y)
    
    return positions

def create_business_unit_overlap_chart(df: pd.DataFrame, st_instance):
    """Create business unit overlap analysis"""
    
    # Create business unit vs systems analysis
    bu_systems = []
    for _, row in df.iterrows():
        bu = row['business_unit']
        systems = row['systems'] if isinstance(row['systems'], list) else []
        for system in systems:
            bu_systems.append({'business_unit': bu, 'system': system})
    
    if not bu_systems:
        st_instance.info("No business unit system data available for overlap analysis")
        return
    
    bu_systems_df = pd.DataFrame(bu_systems)
    
    # Create business unit collaboration matrix
    collaboration_opportunities = []
    business_units = df['business_unit'].unique()
    
    for bu1 in business_units:
        for bu2 in business_units:
            if bu1 != bu2:
                systems1 = set()
                systems2 = set()
                
                for _, row in df[df['business_unit'] == bu1].iterrows():
                    if isinstance(row['systems'], list):
                        systems1.update(row['systems'])
                
                for _, row in df[df['business_unit'] == bu2].iterrows():
                    if isinstance(row['systems'], list):
                        systems2.update(row['systems'])
                
                common_systems = systems1.intersection(systems2)
                if common_systems:
                    collaboration_opportunities.append({
                        'bu1': bu1,
                        'bu2': bu2,
                        'common_systems_count': len(common_systems),
                        'common_systems': list(common_systems)
                    })
    
    if collaboration_opportunities:
        # Create collaboration matrix visualization
        collab_df = pd.DataFrame(collaboration_opportunities)
        
        # Create matrix for heatmap
        bu_list = sorted(business_units)
        collab_matrix = pd.DataFrame(0, index=bu_list, columns=bu_list)
        
        for _, row in collab_df.iterrows():
            collab_matrix.loc[row['bu1'], row['bu2']] = row['common_systems_count']
        
        fig_collab = px.imshow(
            collab_matrix.values,
            x=collab_matrix.columns,
            y=collab_matrix.index,
            title="Business Unit Collaboration Opportunities (Common Systems)",
            labels=dict(color="Shared Systems Count"),
            aspect="auto"
        )
        fig_collab.update_layout(height=400)
        st_instance.plotly_chart(fig_collab, use_container_width=True)

def create_roi_charts(df: pd.DataFrame, st_instance):
    """Create analysis visualizations focused on systems and business units"""
    
    # Systems and priority analysis
    col1, col2 = st_instance.columns(2)
    
    with col1:
        # Priority vs System Count
        system_counts = df['systems'].apply(lambda x: len(x) if isinstance(x, list) else 0)
        df_priority_systems = pd.DataFrame({
            'system_count': system_counts,
            'priority': df['priority'],
            'title': df['title'],
            'business_unit': df['business_unit']
        })
        
        fig_priority_systems = px.scatter(
            df_priority_systems,
            x='system_count',
            y='priority',
            color='business_unit',
            hover_data=['title'],
            title="Priority vs Number of Systems Involved",
            labels={'system_count': 'Number of Systems', 'priority': 'Priority Level'}
        )
        st_instance.plotly_chart(fig_priority_systems, use_container_width=True, key="priority_systems_scatter")
    
    with col2:
        # Systems complexity distribution
        fig_systems_complexity = px.histogram(
            df_priority_systems,
            x='system_count',
            color='priority',
            title="Systems Complexity Distribution by Priority",
            labels={'system_count': 'Number of Systems', 'count': 'Number of Use Cases'},
            nbins=10
        )
        fig_systems_complexity.update_layout(height=400)
        st_instance.plotly_chart(fig_systems_complexity, use_container_width=True, key="systems_complexity_hist")
    
    # Portfolio optimization chart
    create_portfolio_optimization_chart(df, st_instance)

def create_portfolio_optimization_chart(df: pd.DataFrame, st_instance):
    """Create portfolio optimization visualization"""
    
    st_instance.write("### Portfolio Optimization Matrix")
    
    # Create impact vs effort matrix (assuming we have or can derive effort estimates)
    # For now, we'll use system count as a proxy for complexity/effort
    system_counts = df['systems'].apply(lambda x: len(x) if isinstance(x, list) else 0)
    
    # Normalize priority and effort for better visualization
    # Create priority numeric mapping for visualization
    priority_map = {'High': 3, 'Medium': 2, 'Low': 1}
    priority_numeric = df['priority'].map(priority_map).fillna(2)
    
    normalized_priority = (priority_numeric - priority_numeric.min()) / (priority_numeric.max() - priority_numeric.min()) if priority_numeric.max() > priority_numeric.min() else priority_numeric * 0
    normalized_effort = (system_counts - system_counts.min()) / (system_counts.max() - system_counts.min()) if system_counts.max() > system_counts.min() else system_counts * 0
    
    # Create quadrant chart
    fig_portfolio = go.Figure()
    
    # Add quadrant background
    fig_portfolio.add_shape(
        type="rect",
        x0=0, y0=0.5, x1=0.5, y1=1,
        fillcolor="lightgreen", opacity=0.2,
        layer="below", line_width=0,
    )
    fig_portfolio.add_shape(
        type="rect",
        x0=0.5, y0=0.5, x1=1, y1=1,
        fillcolor="yellow", opacity=0.2,
        layer="below", line_width=0,
    )
    fig_portfolio.add_shape(
        type="rect",
        x0=0, y0=0, x1=0.5, y1=0.5,
        fillcolor="orange", opacity=0.2,
        layer="below", line_width=0,
    )
    fig_portfolio.add_shape(
        type="rect",
        x0=0.5, y0=0, x1=1, y1=0.5,
        fillcolor="lightcoral", opacity=0.2,
        layer="below", line_width=0,
    )
    
    # Add data points
    fig_portfolio.add_trace(go.Scatter(
        x=normalized_effort,
        y=normalized_priority,
        mode='markers+text',
        marker=dict(
            size=priority_numeric * 5,  # Size based on priority
            color=priority_numeric,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Priority Level")
        ),
        text=df['title'].str[:20] + '...',  # Truncated titles
        textposition='top center',
        hovertemplate='<b>%{text}</b><br>ROI: %{marker.color}%<br>Complexity: %{x:.2f}<extra></extra>',
        showlegend=False
    ))
    
    # Add quadrant lines
    fig_portfolio.add_hline(y=0.5, line_dash="dash", line_color="black")
    fig_portfolio.add_vline(x=0.5, line_dash="dash", line_color="black")
    
    # Add quadrant labels
    fig_portfolio.add_annotation(x=0.25, y=0.75, text="Quick Wins<br>(High ROI, Low Effort)", showarrow=False, font=dict(size=12, color="green"))
    fig_portfolio.add_annotation(x=0.75, y=0.75, text="Major Projects<br>(High ROI, High Effort)", showarrow=False, font=dict(size=12, color="orange"))
    fig_portfolio.add_annotation(x=0.25, y=0.25, text="Fill-ins<br>(Low ROI, Low Effort)", showarrow=False, font=dict(size=12, color="blue"))
    fig_portfolio.add_annotation(x=0.75, y=0.25, text="Questionable<br>(Low ROI, High Effort)", showarrow=False, font=dict(size=12, color="red"))
    
    fig_portfolio.update_layout(
        title="Use Case Portfolio Optimization Matrix",
        xaxis_title="Complexity/Effort (Normalized)",
        yaxis_title="Expected ROI (Normalized)",
        height=600,
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1])
    )
    
    st_instance.plotly_chart(fig_portfolio, use_container_width=True, key="portfolio_optimization")
    
    # Recommendations based on quadrants
    st_instance.write("### Portfolio Recommendations")
    
    quick_wins = df[(normalized_priority >= 0.5) & (normalized_effort <= 0.5)]
    major_projects = df[(normalized_priority >= 0.5) & (normalized_effort > 0.5)]
    questionable = df[(normalized_priority < 0.5) & (normalized_effort > 0.5)]
    
    if not quick_wins.empty:
        st_instance.success(f"Quick Wins: {len(quick_wins)} use cases with high priority and low complexity")
        for _, case in quick_wins.head(3).iterrows():
            st_instance.write(f"• {case['title']} (Priority: {case['priority']})")
    
    if not major_projects.empty:
        st_instance.info(f"Major Projects: {len(major_projects)} use cases requiring significant investment")
    
    if not questionable.empty:
        st_instance.warning(f"Questionable: {len(questionable)} use cases may need re-evaluation")
