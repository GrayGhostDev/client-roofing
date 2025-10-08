"""Lead components for dashboard and management - Static components with JavaScript functionality."""

import reflex as rx
# from .modals.new_lead_wizard import new_lead_wizard  # Temporarily disabled


def lead_status_badge(status) -> rx.Component:
    """Status badge with appropriate styling."""
    return rx.match(
        status,
        ("new", rx.badge("New", color_scheme="blue", size="1")),
        ("contacted", rx.badge("Contacted", color_scheme="purple", size="1")),
        ("qualified", rx.badge("Qualified", color_scheme="green", size="1")),
        ("appointment_scheduled", rx.badge("Appointment Scheduled", color_scheme="orange", size="1")),
        ("inspection_completed", rx.badge("Inspection Completed", color_scheme="yellow", size="1")),
        ("quote_sent", rx.badge("Quote Sent", color_scheme="cyan", size="1")),
        ("negotiation", rx.badge("Negotiation", color_scheme="pink", size="1")),
        ("won", rx.badge("Won", color_scheme="green", size="1")),
        ("lost", rx.badge("Lost", color_scheme="red", size="1")),
        ("nurture", rx.badge("Nurture", color_scheme="gray", size="1")),
        rx.badge(status, color_scheme="gray", size="1")
    )


def lead_temperature_indicator(temperature, score) -> rx.Component:
    """Temperature indicator with score."""
    return rx.match(
        temperature,
        ("hot", rx.hstack(
            rx.icon("flame", size=16, color="red"),
            rx.text(score, size="2", weight="bold"),
            spacing="1",
            align_items="center"
        )),
        ("warm", rx.hstack(
            rx.icon("sun", size=16, color="orange"),
            rx.text(score, size="2", weight="bold"),
            spacing="1",
            align_items="center"
        )),
        ("cool", rx.hstack(
            rx.icon("cloud", size=16, color="blue"),
            rx.text(score, size="2", weight="bold"),
            spacing="1",
            align_items="center"
        )),
        ("cold", rx.hstack(
            rx.icon("snowflake", size=16, color="gray"),
            rx.text(score, size="2", weight="bold"),
            spacing="1",
            align_items="center"
        )),
        rx.hstack(
            rx.icon("thermometer", size=16, color="gray"),
            rx.text(score, size="2", weight="bold"),
            spacing="1",
            align_items="center"
        )
    )


def leads_table_static() -> rx.Component:
    """Static leads table structure - data loaded via JavaScript."""
    return rx.vstack(
        # Header with static filters
        rx.hstack(
            rx.heading("Lead Management", size="5"),
            rx.spacer(),
            rx.hstack(
                rx.select(
                    ["all", "new", "contacted", "qualified", "appointment_scheduled", "quote_sent", "negotiation", "won", "lost"],
                    value="all",
                    placeholder="Filter by status",
                    size="2",
                    id="status-filter"
                ),
                rx.select(
                    ["all", "hot", "warm", "cool", "cold"],
                    value="all",
                    placeholder="Filter by temperature",
                    size="2",
                    id="temperature-filter"
                ),
                rx.input(
                    placeholder="Search leads...",
                    size="2",
                    id="search-input"
                ),
                # new_lead_wizard(),  # TODO: Temporarily disabled due to Reflex Var compatibility issues
                rx.button(
                    "➕ Add Lead",
                    size="3",
                    color_scheme="blue",
                    on_click=lambda: rx.window_alert("Wizard temporarily disabled - under refactoring for Reflex 0.8.13 compatibility")
                ),
                spacing="2"
            ),
            justify="between",
            align_items="center",
            width="100%",
            margin_bottom="4"
        ),

        # Loading message
        rx.card(
            rx.vstack(
                rx.spinner(size="3"),
                rx.text("Loading leads...", id="leads-loading-message", size="3", color="gray"),
                spacing="3",
                align_items="center",
                padding="8"
            ),
            id="leads-loading-card",
            size="2",
            width="100%"
        ),

        # Error message (hidden by default)
        rx.callout(
            "Failed to load leads",
            id="leads-error-message",
            icon="circle_alert",
            color_scheme="red",
            size="2",
            margin_bottom="4",
            style={"display": "none"}
        ),

        # Main table (hidden until data loads)
        rx.card(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Name"),
                        rx.table.column_header_cell("Contact"),
                        rx.table.column_header_cell("Status"),
                        rx.table.column_header_cell("Score"),
                        rx.table.column_header_cell("Source"),
                        rx.table.column_header_cell("Created"),
                        rx.table.column_header_cell("Actions"),
                    )
                ),
                rx.table.body(
                    id="leads-table-body"
                    # Table rows will be populated by JavaScript
                ),
                id="leads-table",
                size="2",
                width="100%"
            ),
            id="leads-table-card",
            size="2",
            width="100%",
            style={"display": "none"}
        ),

        # Pagination (hidden until data loads)
        rx.hstack(
            rx.text("Showing 0-0 of 0 leads", id="leads-pagination-info", size="2", color="gray"),
            rx.spacer(),
            rx.hstack(
                rx.select(
                    ["10", "25", "50", "100"],
                    value="25",
                    size="2",
                    id="page-size-select"
                ),
                rx.button(
                    rx.icon("chevron_left", size=16),
                    size="2",
                    variant="outline",
                    id="prev-page-btn",
                    disabled=True
                ),
                rx.text("Page 1 of 1", id="page-info", size="2"),
                rx.button(
                    rx.icon("chevron_right", size=16),
                    size="2",
                    variant="outline",
                    id="next-page-btn",
                    disabled=True
                ),
                spacing="2"
            ),
            justify="between",
            align_items="center",
            width="100%",
            margin_top="4",
            id="leads-pagination",
            style={"display": "none"}
        ),

        spacing="4",
        width="100%"
    )


def hot_leads_widget_static() -> rx.Component:
    """Static hot leads widget for dashboard."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("flame", size=20, color="red"),
                rx.heading("Hot Leads", size="3"),
                rx.badge(
                    rx.text("0", id="hot-leads-count"),
                    color_scheme="red"
                ),
                spacing="2",
                align_items="center"
            ),
            rx.divider(),
            rx.vstack(
                rx.text("Loading hot leads...", id="hot-leads-loading", size="2", color="gray"),
                rx.vstack(
                    id="hot-leads-list",
                    spacing="1",
                    width="100%",
                    style={"display": "none"}
                ),
                rx.text("No hot leads", id="hot-leads-empty", size="2", color="gray", style={"display": "none"}),
                spacing="2",
                width="100%"
            ),
            spacing="2",
            width="100%"
        ),
        size="2",
        height="300px"
    )


def follow_up_reminders_widget_static() -> rx.Component:
    """Static follow-up reminders widget."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("clock", size=20, color="orange"),
                rx.heading("Follow-up Reminders", size="3"),
                rx.badge(
                    rx.text("0", id="reminders-count"),
                    color_scheme="orange"
                ),
                spacing="2",
                align_items="center"
            ),
            rx.divider(),
            rx.vstack(
                rx.text("Loading reminders...", id="reminders-loading", size="2", color="gray"),
                rx.vstack(
                    id="reminders-list",
                    spacing="1",
                    width="100%",
                    style={"display": "none"}
                ),
                rx.text("No upcoming reminders", id="reminders-empty", size="2", color="gray", style={"display": "none"}),
                spacing="2",
                width="100%"
            ),
            spacing="2",
            width="100%"
        ),
        size="2",
        height="300px"
    )


def leads_list_page() -> rx.Component:
    """Complete leads list page with navigation and table."""
    return rx.container(
        rx.color_mode.button(position="top-right"),

        # Navigation breadcrumb
        rx.hstack(
            rx.link(
                rx.button(
                    rx.icon("arrow_left", size=16),
                    "Back to Dashboard",
                    variant="ghost",
                    size="2"
                ),
                href="/"
            ),
            rx.text("/", color="gray"),
            rx.text("Lead Management", weight="bold"),
            spacing="2",
            align_items="center",
            margin_bottom="4"
        ),

        # Main leads table
        leads_table_static(),

        # JavaScript for leads functionality
        rx.script("""
            // Leads management JavaScript
            let currentPage = 1;
            let pageSize = 25;
            let totalLeads = 0;
            let filteredLeads = [];
            let allLeads = [];

            // DOM elements
            const loadingCard = document.getElementById('leads-loading-card');
            const errorMessage = document.getElementById('leads-error-message');
            const tableCard = document.getElementById('leads-table-card');
            const tableBody = document.getElementById('leads-table-body');
            const pagination = document.getElementById('leads-pagination');
            const statusFilter = document.getElementById('status-filter');
            const temperatureFilter = document.getElementById('temperature-filter');
            const searchInput = document.getElementById('search-input');
            const newLeadBtn = document.getElementById('new-lead-btn');

            // Initialize page
            document.addEventListener('DOMContentLoaded', function() {
                loadLeadsData();
                setupEventListeners();
            });

            // Setup event listeners
            function setupEventListeners() {
                if (statusFilter) {
                    statusFilter.addEventListener('change', function() {
                        filterLeads();
                    });
                }

                if (temperatureFilter) {
                    temperatureFilter.addEventListener('change', function() {
                        filterLeads();
                    });
                }

                if (searchInput) {
                    searchInput.addEventListener('input', debounce(function() {
                        filterLeads();
                    }, 300));
                }

                if (newLeadBtn) {
                    newLeadBtn.addEventListener('click', function() {
                        // Trigger new lead wizard if available
                        const trigger = document.getElementById('new-lead-trigger');
                        if (trigger) trigger.click();
                    });
                }
            }

            // Load leads data
            async function loadLeadsData() {
                try {
                    showLoading();

                    // Simulate API call - replace with actual endpoint
                    await new Promise(resolve => setTimeout(resolve, 1000));

                    // Mock data for demonstration
                    allLeads = [
                        {
                            id: '1',
                            first_name: 'John',
                            last_name: 'Doe',
                            phone: '(555) 123-4567',
                            email: 'john.doe@email.com',
                            status: 'new',
                            temperature: 'hot',
                            lead_score: 85,
                            source: 'Google Ads',
                            created_at: '2024-01-15',
                            address: '123 Main St'
                        },
                        {
                            id: '2',
                            first_name: 'Jane',
                            last_name: 'Smith',
                            phone: '(555) 987-6543',
                            email: 'jane.smith@email.com',
                            status: 'contacted',
                            temperature: 'warm',
                            lead_score: 72,
                            source: 'Referral',
                            created_at: '2024-01-16',
                            address: '456 Oak Ave'
                        },
                        {
                            id: '3',
                            first_name: 'Bob',
                            last_name: 'Johnson',
                            phone: '(555) 456-7890',
                            email: '',
                            status: 'qualified',
                            temperature: 'cool',
                            lead_score: 65,
                            source: 'Website',
                            created_at: '2024-01-17',
                            address: '789 Pine Rd'
                        }
                    ];

                    filterLeads();
                    hideLoading();
                    showTable();
                } catch (error) {
                    console.error('Failed to load leads:', error);
                    showError('Failed to load leads. Please try again.');
                }
            }

            // Filter leads based on current filters
            function filterLeads() {
                const statusValue = statusFilter?.value || 'all';
                const tempValue = temperatureFilter?.value || 'all';
                const searchValue = searchInput?.value?.toLowerCase() || '';

                filteredLeads = allLeads.filter(lead => {
                    const matchesStatus = statusValue === 'all' || lead.status === statusValue;
                    const matchesTemp = tempValue === 'all' || lead.temperature === tempValue;
                    const matchesSearch = !searchValue ||
                        lead.first_name.toLowerCase().includes(searchValue) ||
                        lead.last_name.toLowerCase().includes(searchValue) ||
                        lead.phone.includes(searchValue) ||
                        lead.email.toLowerCase().includes(searchValue);

                    return matchesStatus && matchesTemp && matchesSearch;
                });

                currentPage = 1; // Reset to first page
                updateTable();
                updatePagination();
            }

            // Update table with current page data
            function updateTable() {
                if (!tableBody) return;

                const startIndex = (currentPage - 1) * pageSize;
                const endIndex = startIndex + pageSize;
                const pageLeads = filteredLeads.slice(startIndex, endIndex);

                tableBody.innerHTML = '';

                pageLeads.forEach(lead => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td style="padding: 12px;">
                            <div>
                                <div style="font-weight: bold;">${lead.first_name} ${lead.last_name}</div>
                                <div style="color: #666; font-size: 14px;">${lead.address}</div>
                            </div>
                        </td>
                        <td style="padding: 12px;">
                            <div>
                                <div>${lead.phone}</div>
                                <div style="color: #666; font-size: 14px;">${lead.email || '-'}</div>
                            </div>
                        </td>
                        <td style="padding: 12px;">
                            <span class="badge ${getStatusBadgeClass(lead.status)}">${lead.status}</span>
                        </td>
                        <td style="padding: 12px;">
                            <div style="display: flex; align-items: center; gap: 4px;">
                                ${getTemperatureIcon(lead.temperature)}
                                <span style="font-weight: bold;">${lead.lead_score}</span>
                            </div>
                        </td>
                        <td style="padding: 12px;">${lead.source}</td>
                        <td style="padding: 12px; color: #666;">${formatDate(lead.created_at)}</td>
                        <td style="padding: 12px;">
                            <div style="display: flex; gap: 4px;">
                                <button onclick="callLead('${lead.phone}')" style="padding: 4px 8px; border: none; background: #e8f5e8; color: #2d7f2d; border-radius: 4px; cursor: pointer;">📞</button>
                                <button onclick="emailLead('${lead.email}')" style="padding: 4px 8px; border: none; background: #e8f0ff; color: #2d5aa0; border-radius: 4px; cursor: pointer;">✉️</button>
                                <button onclick="editLead('${lead.id}')" style="padding: 4px 8px; border: none; background: #f0f0f0; color: #333; border-radius: 4px; cursor: pointer;">✏️</button>
                            </div>
                        </td>
                    `;
                    tableBody.appendChild(row);
                });
            }

            // Update pagination
            function updatePagination() {
                const totalPages = Math.ceil(filteredLeads.length / pageSize);

                const paginationInfo = document.getElementById('leads-pagination-info');
                const pageInfo = document.getElementById('page-info');
                const prevBtn = document.getElementById('prev-page-btn');
                const nextBtn = document.getElementById('next-page-btn');

                if (paginationInfo) {
                    const startItem = filteredLeads.length === 0 ? 0 : ((currentPage - 1) * pageSize) + 1;
                    const endItem = Math.min(currentPage * pageSize, filteredLeads.length);
                    paginationInfo.textContent = `Showing ${startItem}-${endItem} of ${filteredLeads.length} leads`;
                }

                if (pageInfo) {
                    pageInfo.textContent = `Page ${currentPage} of ${totalPages || 1}`;
                }

                if (prevBtn) {
                    prevBtn.disabled = currentPage <= 1;
                    prevBtn.onclick = () => {
                        if (currentPage > 1) {
                            currentPage--;
                            updateTable();
                            updatePagination();
                        }
                    };
                }

                if (nextBtn) {
                    nextBtn.disabled = currentPage >= totalPages;
                    nextBtn.onclick = () => {
                        if (currentPage < totalPages) {
                            currentPage++;
                            updateTable();
                            updatePagination();
                        }
                    };
                }
            }

            // Helper functions
            function getStatusBadgeClass(status) {
                const classes = {
                    'new': 'badge-blue',
                    'contacted': 'badge-purple',
                    'qualified': 'badge-green',
                    'appointment_scheduled': 'badge-orange',
                    'won': 'badge-green',
                    'lost': 'badge-red'
                };
                return classes[status] || 'badge-gray';
            }

            function getTemperatureIcon(temperature) {
                const icons = {
                    'hot': '🔥',
                    'warm': '☀️',
                    'cool': '☁️',
                    'cold': '❄️'
                };
                return icons[temperature] || '🌡️';
            }

            function formatDate(dateString) {
                const date = new Date(dateString);
                return date.toLocaleDateString();
            }

            function debounce(func, wait) {
                let timeout;
                return function executedFunction(...args) {
                    const later = () => {
                        clearTimeout(timeout);
                        func(...args);
                    };
                    clearTimeout(timeout);
                    timeout = setTimeout(later, wait);
                };
            }

            // Show/hide functions
            function showLoading() {
                if (loadingCard) loadingCard.style.display = 'block';
                if (tableCard) tableCard.style.display = 'none';
                if (pagination) pagination.style.display = 'none';
                if (errorMessage) errorMessage.style.display = 'none';
            }

            function hideLoading() {
                if (loadingCard) loadingCard.style.display = 'none';
            }

            function showTable() {
                if (tableCard) tableCard.style.display = 'block';
                if (pagination) pagination.style.display = 'flex';
            }

            function showError(message) {
                hideLoading();
                if (errorMessage) {
                    errorMessage.style.display = 'block';
                    errorMessage.textContent = message;
                }
            }

            // Action functions
            function callLead(phone) {
                window.open(`tel:${phone}`);
            }

            function emailLead(email) {
                if (email) {
                    window.open(`mailto:${email}`);
                }
            }

            function editLead(leadId) {
                console.log('Edit lead:', leadId);
                // Future: Open lead detail modal
            }

            // Add CSS for badges
            const style = document.createElement('style');
            style.textContent = `
                .badge {
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: bold;
                    text-transform: capitalize;
                }
                .badge-blue { background: #dbeafe; color: #1e40af; }
                .badge-purple { background: #ede9fe; color: #7c3aed; }
                .badge-green { background: #dcfce7; color: #166534; }
                .badge-orange { background: #fed7aa; color: #ea580c; }
                .badge-red { background: #fecaca; color: #dc2626; }
                .badge-gray { background: #f3f4f6; color: #374151; }
            `;
            document.head.appendChild(style);
        """),

        size="4",
        padding="4"
    )


# Aliases for backward compatibility
leads_page = leads_list_page
lead_management_page = leads_list_page  # Alternative alias