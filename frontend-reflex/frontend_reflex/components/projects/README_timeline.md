# Project Timeline Component

## Overview

The project timeline component provides visual project schedule management for the iSwitch Roofs CRM system. It offers three distinct views for tracking project progress and resource allocation.

## Features

### View Modes

1. **Gantt Chart View** (Default)
   - Visual timeline bars showing project duration
   - Progress indicators within bars
   - Status color coding
   - Team member avatars
   - Click to view project details

2. **Calendar View**
   - Month-based calendar layout
   - Project markers on relevant dates
   - Navigation between months
   - Quick project overview

3. **Resource Allocation View**
   - Team member workload visualization
   - Capacity utilization metrics
   - Upcoming deadline tracking
   - Resource conflicts identification

### Timeline Controls

- **Date Range Selector**: Week, Month, Quarter views
- **Navigation**: Previous/Next period buttons
- **Quick Filters**: Overdue, This Week, High Priority, Unassigned
- **Export**: Timeline data export functionality

### Integration

- **Project Pipeline**: Seamless navigation between pipeline and timeline views
- **Project Details**: Click project bars to open detail modals
- **Real-time Updates**: Automatic refresh when project data changes

## Technical Implementation

### State Management

The component uses the following state variables:

```python
timeline_view_mode: str = "gantt"      # gantt, calendar, resource
timeline_date_range: str = "month"     # week, month, quarter
timeline_show_overdue: bool = False    # Filter toggles
timeline_show_this_week: bool = False
timeline_show_high_priority: bool = False
timeline_show_unassigned: bool = False
```

### Key Methods

- `set_timeline_view_mode(mode)`: Switch between view modes
- `set_timeline_date_range(range)`: Change date range scope
- `toggle_timeline_filter(filter)`: Toggle filter options
- `filtered_timeline_projects`: Computed filtered project list
- `timeline_stats`: Real-time statistics calculation

### Visual Design

- **Color Coding**: Projects colored by status (planning=blue, in_progress=orange, etc.)
- **Progress Bars**: Visual completion indicators
- **Hover Effects**: Enhanced interactivity
- **Responsive Layout**: Adapts to different screen sizes

## Usage

### Navigation

Access the timeline from:
- Dashboard: "Timeline" button in Project Management card
- Project Pipeline: "Timeline View" button in header
- Direct route: `/timeline`

### Interactions

1. **View Projects**: Click timeline bars to open project details
2. **Filter Data**: Use checkboxes in sidebar for quick filtering
3. **Change Views**: Use header buttons to switch between Gantt, Calendar, and Resource views
4. **Navigate Time**: Use date range selector and navigation arrows

### Data Sources

The timeline component uses:
- `AppState.projects`: All project data
- `AppState.team_members`: Team assignment information
- Backend project API for real-time updates

## Future Enhancements

- Drag-and-drop timeline editing
- Resource conflict alerts
- Milestone tracking
- Custom date range selection
- Timeline export to PDF/Excel
- Mobile-optimized touch interface

## Component Structure

```
project_timeline.py
├── project_timeline_header()      # Controls and navigation
├── gantt_chart_view()             # Main timeline visualization
├── calendar_view()                # Calendar-style layout
├── resource_allocation_view()      # Team workload view
├── timeline_legend()              # Status color legend
└── project_timeline_page()       # Main container
```

## Dependencies

- `reflex`: UI framework
- `datetime`: Date calculations
- `..modals.project_detail_modal`: Project details
- `..modals.new_project_modal`: New project creation
- `...state.AppState`: Application state management