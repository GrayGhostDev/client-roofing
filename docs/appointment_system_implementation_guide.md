# Appointment Management System - Technical Implementation Guide

## Overview

This guide provides specific code implementations for enhancing the existing appointment management system in the iSwitch Roofs CRM. All recommendations build upon the existing solid foundation.

## 1. Enhanced Data Models

### A. Weather-Aware Appointment Model Extension

```python
# Add to existing appointment.py model
from typing import Dict, Any
import requests
from datetime import datetime, timedelta

class WeatherDependentAppointment(BaseModel):
    """Extension for weather-dependent appointment features"""

    weather_dependent: bool = Field(default=True, description="Affected by weather conditions")
    weather_check_required: bool = Field(default=False, description="Check weather 24h before")
    backup_date: Optional[datetime] = Field(None, description="Backup date for weather delays")
    weather_conditions_required: Optional[str] = Field(None, description="Required weather conditions")
    temperature_range: Optional[Dict[str, int]] = Field(None, description="Min/max temperature")
    wind_speed_limit: Optional[int] = Field(None, description="Maximum wind speed in mph")
    precipitation_limit: Optional[float] = Field(None, description="Maximum precipitation in inches")

class RoofingAppointmentType(str, Enum):
    """Enhanced appointment types for roofing business"""

    # Emergency Response (Priority Level 1)
    EMERGENCY_INSPECTION = "emergency_inspection"
    STORM_DAMAGE_ASSESSMENT = "storm_damage_assessment"
    LEAK_EMERGENCY = "leak_emergency"

    # Sales Process (Priority Level 2)
    INITIAL_CONSULTATION = "initial_consultation"
    DETAILED_ROOF_INSPECTION = "detailed_roof_inspection"
    DRONE_INSPECTION = "drone_inspection"
    INSURANCE_ADJUSTER_MEETING = "insurance_adjuster_meeting"
    QUOTE_PRESENTATION = "quote_presentation"
    CONTRACT_SIGNING = "contract_signing"

    # Project Execution (Priority Level 3)
    PROJECT_KICKOFF = "project_kickoff"
    MATERIAL_DELIVERY = "material_delivery"
    WORK_START = "work_start"
    DAILY_PROGRESS_CHECK = "daily_progress_check"
    QUALITY_INSPECTION = "quality_inspection"
    FINAL_WALKTHROUGH = "final_walkthrough"
    CLEANUP_INSPECTION = "cleanup_inspection"

    # Post-Project (Priority Level 4)
    WARRANTY_FOLLOW_UP = "warranty_follow_up"
    ANNUAL_MAINTENANCE = "annual_maintenance"
    CUSTOMER_SATISFACTION_SURVEY = "customer_satisfaction_survey"

# Enhanced appointment model with roofing-specific fields
class EnhancedAppointment(Appointment):
    """Enhanced appointment model with roofing-specific features"""

    # Roofing-specific fields
    appointment_type: RoofingAppointmentType
    weather_info: Optional[WeatherDependentAppointment] = None

    # Equipment and materials
    equipment_required: Optional[List[str]] = Field(None, description="Required equipment list")
    material_samples: Optional[List[str]] = Field(None, description="Material samples to bring")
    inspection_scope: Optional[str] = Field(None, description="Scope of inspection")
    access_requirements: Optional[str] = Field(None, description="Special access needs")

    # Customer experience
    customer_special_instructions: Optional[str] = Field(None, description="Gate codes, pets, etc.")
    preferred_communication: Optional[str] = Field(None, description="Preferred contact method")

    # Business intelligence
    estimated_project_value: Optional[int] = Field(None, description="Estimated project value USD")
    lead_temperature: Optional[str] = Field(None, description="Hot/Warm/Cool/Cold")
    priority_level: int = Field(default=3, ge=1, le=5, description="1=Emergency, 5=Low priority")

    @property
    def requires_weather_check(self) -> bool:
        """Check if appointment requires weather monitoring"""
        outdoor_types = [
            RoofingAppointmentType.DETAILED_ROOF_INSPECTION,
            RoofingAppointmentType.DRONE_INSPECTION,
            RoofingAppointmentType.STORM_DAMAGE_ASSESSMENT,
            RoofingAppointmentType.WORK_START,
            RoofingAppointmentType.QUALITY_INSPECTION
        ]
        return self.appointment_type in outdoor_types

    @property
    def travel_buffer_minutes(self) -> int:
        """Calculate travel buffer based on appointment type and location"""
        if self.appointment_type in [RoofingAppointmentType.EMERGENCY_INSPECTION, RoofingAppointmentType.LEAK_EMERGENCY]:
            return 15  # Minimal buffer for emergencies
        elif self.appointment_type in [RoofingAppointmentType.DETAILED_ROOF_INSPECTION, RoofingAppointmentType.DRONE_INSPECTION]:
            return 30  # More time for equipment setup
        else:
            return 20  # Standard buffer
```

### B. Team Availability and Coordination

```python
class TeamAvailabilitySlot(BaseDBModel):
    """Detailed availability tracking for team members"""

    team_member_id: UUID
    date: date
    start_time: time
    end_time: time
    availability_type: str  # "available", "busy", "tentative", "out_of_office"

    # Location and travel
    starting_location: Optional[str] = Field(None, description="Starting location for day")
    travel_radius_miles: int = Field(default=25, description="Willing to travel distance")

    # Capacity management
    max_appointments: int = Field(default=6, description="Maximum appointments per slot")
    current_appointments: int = Field(default=0, description="Current scheduled appointments")

    # Break and buffer times
    lunch_break_start: Optional[time] = None
    lunch_break_duration: int = Field(default=60, description="Lunch break in minutes")
    buffer_between_appointments: int = Field(default=15, description="Buffer time in minutes")

    # Special considerations
    equipment_available: Optional[List[str]] = Field(None, description="Available equipment/tools")
    certifications: Optional[List[str]] = Field(None, description="Active certifications")
    notes: Optional[str] = Field(None, description="Special notes for the day")

class MultiTeamAppointment(BaseDBModel):
    """Coordination for appointments requiring multiple team members"""

    primary_appointment_id: UUID
    appointment_type: RoofingAppointmentType

    # Team coordination
    lead_team_member: UUID
    required_team_members: List[UUID]
    optional_team_members: List[UUID] = []
    minimum_team_size: int = Field(ge=1, description="Minimum required team members")

    # Scheduling constraints
    all_members_required: bool = Field(default=True, description="All members must attend")
    coordination_window: int = Field(default=30, description="Coordination window in minutes")

    # Logistics
    meeting_point: Optional[str] = Field(None, description="Team meeting location")
    equipment_assignments: Optional[Dict[str, List[str]]] = Field(None, description="Equipment per member")
    role_assignments: Optional[Dict[str, str]] = Field(None, description="Role per team member")
```

## 2. Smart Scheduling Service

```python
class WeatherService:
    """Service for weather-related appointment management"""

    def __init__(self):
        self.api_key = os.getenv('WEATHER_API_KEY')
        self.base_url = "https://api.openweathermap.org/data/2.5"

    async def check_weather_suitability(self,
                                       appointment: EnhancedAppointment,
                                       location: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if weather conditions are suitable for appointment

        Returns:
            Tuple of (is_suitable, weather_data)
        """
        try:
            if not appointment.requires_weather_check:
                return True, {}

            # Get weather forecast
            weather_data = await self._get_weather_forecast(location, appointment.scheduled_date)

            # Check against requirements
            is_suitable = self._evaluate_weather_conditions(
                weather_data,
                appointment.weather_info
            )

            return is_suitable, weather_data

        except Exception as e:
            logger.error(f"Weather check failed: {str(e)}")
            return True, {}  # Default to suitable if check fails

    async def _get_weather_forecast(self, location: str, date: datetime) -> Dict[str, Any]:
        """Get weather forecast for specific location and date"""
        url = f"{self.base_url}/forecast"
        params = {
            'q': location,
            'appid': self.api_key,
            'units': 'imperial',
            'cnt': 40  # 5-day forecast
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()

                # Find forecast closest to appointment time
                target_time = date.timestamp()
                closest_forecast = min(
                    data['list'],
                    key=lambda x: abs(x['dt'] - target_time)
                )

                return closest_forecast

    def _evaluate_weather_conditions(self,
                                   weather_data: Dict[str, Any],
                                   weather_requirements: Optional[WeatherDependentAppointment]) -> bool:
        """Evaluate if weather meets appointment requirements"""
        if not weather_requirements:
            # Default weather requirements for roofing
            weather_requirements = WeatherDependentAppointment(
                temperature_range={"min": 40, "max": 95},
                wind_speed_limit=25,
                precipitation_limit=0.1
            )

        # Check temperature
        temp = weather_data['main']['temp']
        if weather_requirements.temperature_range:
            min_temp = weather_requirements.temperature_range.get('min', -100)
            max_temp = weather_requirements.temperature_range.get('max', 200)
            if not (min_temp <= temp <= max_temp):
                return False

        # Check wind speed
        wind_speed = weather_data['wind']['speed']
        if weather_requirements.wind_speed_limit and wind_speed > weather_requirements.wind_speed_limit:
            return False

        # Check precipitation
        precipitation = weather_data.get('rain', {}).get('3h', 0) + weather_data.get('snow', {}).get('3h', 0)
        if weather_requirements.precipitation_limit and precipitation > weather_requirements.precipitation_limit:
            return False

        return True

class SmartSchedulingService:
    """Advanced scheduling service with AI-powered optimization"""

    def __init__(self):
        self.weather_service = WeatherService()
        self.travel_time_service = TravelTimeService()

    async def find_optimal_appointment_slots(self,
                                           request: SmartSchedulingRequest) -> List[Dict[str, Any]]:
        """
        Find optimal appointment slots using multiple factors:
        - Team member availability
        - Travel optimization
        - Weather conditions
        - Customer preferences
        - Business priorities
        """
        try:
            # Get available team members
            available_members = await self._get_available_team_members(
                request.appointment_type,
                request.priority,
                request.preferred_time_slots
            )

            optimal_slots = []

            for member in available_members:
                # Get member's available slots
                slots = await self._get_member_available_slots(
                    member['id'],
                    request.preferred_time_slots,
                    request.appointment_type
                )

                for slot in slots:
                    # Calculate travel time
                    travel_time = await self.travel_time_service.calculate_travel_time(
                        member['current_location'],
                        request.location,
                        slot['start_time']
                    )

                    # Check weather if required
                    weather_suitable = True
                    if request.weather_dependent:
                        weather_suitable, weather_data = await self.weather_service.check_weather_suitability(
                            request.to_appointment(),
                            request.location
                        )

                    # Calculate score
                    score = self._calculate_slot_score(
                        slot,
                        member,
                        request,
                        travel_time,
                        weather_suitable
                    )

                    optimal_slots.append({
                        'team_member_id': member['id'],
                        'team_member_name': member['name'],
                        'start_time': slot['start_time'],
                        'end_time': slot['end_time'],
                        'travel_time_minutes': travel_time,
                        'weather_suitable': weather_suitable,
                        'score': score,
                        'reasons': self._get_score_reasons(score, travel_time, weather_suitable)
                    })

            # Sort by score and return top options
            optimal_slots.sort(key=lambda x: x['score'], reverse=True)
            return optimal_slots[:10]  # Top 10 options

        except Exception as e:
            logger.error(f"Error finding optimal slots: {str(e)}")
            return []

    def _calculate_slot_score(self,
                            slot: Dict,
                            member: Dict,
                            request: SmartSchedulingRequest,
                            travel_time: int,
                            weather_suitable: bool) -> float:
        """Calculate score for appointment slot based on multiple factors"""
        score = 100.0  # Base score

        # Priority adjustments
        if request.priority == SchedulingPriority.EMERGENCY:
            score += 50
        elif request.priority == SchedulingPriority.URGENT:
            score += 30
        elif request.priority == SchedulingPriority.HIGH:
            score += 15

        # Travel time penalty
        score -= (travel_time * 0.5)  # 0.5 points per minute of travel

        # Weather bonus/penalty
        if weather_suitable:
            score += 10
        else:
            score -= 30

        # Team member specialization bonus
        if self._is_specialized_for_appointment(member, request.appointment_type):
            score += 20

        # Time preference matching
        if self._matches_customer_preferences(slot, request.preferred_time_slots):
            score += 15

        # Workload balancing
        daily_appointments = member.get('daily_appointments', 0)
        if daily_appointments < 4:
            score += 5
        elif daily_appointments > 6:
            score -= 10

        return max(0, score)  # Ensure score doesn't go negative

    def _is_specialized_for_appointment(self, member: Dict, appointment_type: RoofingAppointmentType) -> bool:
        """Check if team member is specialized for appointment type"""
        specializations = {
            RoofingAppointmentType.DRONE_INSPECTION: ['drone_certified', 'inspection_specialist'],
            RoofingAppointmentType.INSURANCE_ADJUSTER_MEETING: ['insurance_specialist', 'senior_sales'],
            RoofingAppointmentType.EMERGENCY_INSPECTION: ['emergency_response', 'senior_technician'],
            RoofingAppointmentType.CONTRACT_SIGNING: ['sales_rep', 'manager', 'owner']
        }

        required_skills = specializations.get(appointment_type, [])
        member_skills = member.get('skills', [])

        return any(skill in member_skills for skill in required_skills)

class TravelTimeService:
    """Service for calculating travel times and optimizing routes"""

    def __init__(self):
        self.google_maps_key = os.getenv('GOOGLE_MAPS_API_KEY')

    async def calculate_travel_time(self,
                                  origin: str,
                                  destination: str,
                                  departure_time: datetime) -> int:
        """Calculate travel time between two locations"""
        try:
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                'origins': origin,
                'destinations': destination,
                'departure_time': int(departure_time.timestamp()),
                'traffic_model': 'best_guess',
                'key': self.google_maps_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()

                    if data['status'] == 'OK':
                        duration = data['rows'][0]['elements'][0]['duration_in_traffic']['value']
                        return duration // 60  # Convert to minutes
                    else:
                        return 30  # Default 30 minutes if API fails

        except Exception as e:
            logger.error(f"Travel time calculation failed: {str(e)}")
            return 30  # Default fallback

    async def optimize_daily_route(self, appointments: List[EnhancedAppointment]) -> Dict[str, Any]:
        """Optimize route for daily appointments"""
        # Implementation for route optimization
        # Using Google Maps Directions API with waypoint optimization
        pass
```

## 3. Advanced Notification System

```python
class NotificationTemplateEngine:
    """Advanced notification template system with personalization"""

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Dict]:
        """Load notification templates"""
        return {
            "appointment_confirmation": {
                "email": {
                    "subject": "Your {appointment_type} is Confirmed - {formatted_date}",
                    "body": """
Hi {customer_name},

Your {appointment_type} with {team_member_name} is confirmed for {formatted_date}.

📍 Location: {location}
⏰ Duration: {duration} minutes
🌤️ Weather: {weather_status}

What to expect:
{preparation_notes}

{weather_dependent_note}

Need to reschedule? Reply to this email or call us at {company_phone}.

Best regards,
{team_member_name}
iSwitch Roofs Team
                    """
                },
                "sms": {
                    "body": "✅ Confirmed: {appointment_type} on {short_date} at {time} with {team_member_name}. {location}. {weather_note} Need to reschedule? Call {company_phone}"
                }
            },
            "weather_alert": {
                "email": {
                    "subject": "Weather Alert: Your {appointment_type} on {formatted_date}",
                    "body": """
Hi {customer_name},

We're monitoring weather conditions for your {appointment_type} scheduled for {formatted_date}.

Current forecast: {weather_forecast}

{weather_action_required}

We'll update you 24 hours before if any changes are needed.

Stay safe,
{team_member_name}
                    """
                },
                "sms": {
                    "body": "🌤️ Weather alert for your {appointment_type} on {short_date}. {weather_summary} We'll update you if changes needed. -iSwitch Roofs"
                }
            },
            "emergency_response": {
                "sms": {
                    "body": "🚨 Emergency response team dispatched! {team_member_name} will arrive at {location} within {eta_minutes} minutes. Emergency contact: {emergency_phone}"
                }
            }
        }

    def generate_notification(self,
                            template_type: str,
                            channel: str,
                            appointment: EnhancedAppointment,
                            custom_variables: Dict[str, Any] = None) -> Dict[str, str]:
        """Generate personalized notification content"""
        try:
            template = self.templates[template_type][channel]
            variables = self._prepare_variables(appointment, custom_variables)

            result = {}
            for key, template_str in template.items():
                result[key] = template_str.format(**variables)

            return result

        except Exception as e:
            logger.error(f"Notification generation failed: {str(e)}")
            return {"subject": "Appointment Update", "body": "Please contact us for details."}

    def _prepare_variables(self,
                          appointment: EnhancedAppointment,
                          custom_variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare variables for template substitution"""
        variables = {
            'customer_name': appointment.customer_name,
            'team_member_name': appointment.team_member_name,
            'appointment_type': appointment.appointment_type.replace('_', ' ').title(),
            'formatted_date': appointment.scheduled_date.strftime('%B %d, %Y at %I:%M %p'),
            'short_date': appointment.scheduled_date.strftime('%m/%d'),
            'time': appointment.scheduled_date.strftime('%I:%M %p'),
            'location': appointment.location or 'Address provided separately',
            'duration': appointment.duration_minutes,
            'company_phone': os.getenv('COMPANY_PHONE', '(555) 123-4567'),
            'preparation_notes': appointment.preparation_notes or 'No special preparation required.',
        }

        # Add weather-related variables
        if appointment.requires_weather_check:
            variables.update({
                'weather_status': 'Weather conditions being monitored',
                'weather_dependent_note': 'Note: This appointment may be rescheduled due to weather conditions.',
                'weather_note': 'Weather dependent'
            })
        else:
            variables.update({
                'weather_status': 'Indoor appointment - weather independent',
                'weather_dependent_note': '',
                'weather_note': ''
            })

        # Add custom variables
        if custom_variables:
            variables.update(custom_variables)

        return variables

class EnhancedNotificationService:
    """Enhanced notification service with intelligent routing"""

    def __init__(self):
        self.template_engine = NotificationTemplateEngine()
        self.delivery_tracker = DeliveryTracker()

    async def send_appointment_notification(self,
                                          appointment: EnhancedAppointment,
                                          notification_type: str,
                                          urgency: str = "normal") -> bool:
        """Send intelligent multi-channel notification"""
        try:
            # Get customer notification preferences
            preferences = await self._get_customer_preferences(appointment.customer_id)

            # Determine optimal notification strategy
            strategy = self._determine_notification_strategy(
                notification_type,
                urgency,
                preferences,
                appointment.scheduled_date
            )

            success = True
            for channel in strategy['channels']:
                try:
                    # Generate notification content
                    content = self.template_engine.generate_notification(
                        notification_type,
                        channel,
                        appointment,
                        strategy.get('custom_variables', {})
                    )

                    # Send notification
                    delivery_id = await self._send_via_channel(
                        channel,
                        appointment.customer_contact_info[channel],
                        content
                    )

                    # Track delivery
                    await self.delivery_tracker.track_sent(
                        appointment.id,
                        channel,
                        delivery_id,
                        content
                    )

                except Exception as e:
                    logger.error(f"Failed to send via {channel}: {str(e)}")
                    success = False

            return success

        except Exception as e:
            logger.error(f"Notification sending failed: {str(e)}")
            return False

    def _determine_notification_strategy(self,
                                       notification_type: str,
                                       urgency: str,
                                       preferences: Dict,
                                       appointment_time: datetime) -> Dict[str, Any]:
        """Determine optimal notification strategy"""

        # Emergency notifications
        if urgency == "emergency":
            return {
                'channels': ['sms', 'phone'],
                'retry_attempts': 3,
                'retry_interval': 5  # minutes
            }

        # Time-sensitive notifications
        time_until = appointment_time - datetime.utcnow()
        if time_until.total_seconds() < 3600:  # Less than 1 hour
            return {
                'channels': ['sms'],
                'custom_variables': {'urgency_note': 'Urgent - appointment within 1 hour'}
            }

        # Standard notifications based on preferences
        preferred_channels = preferences.get('notification_channels', ['email', 'sms'])

        return {
            'channels': preferred_channels,
            'retry_attempts': 1,
            'custom_variables': {}
        }

class DeliveryTracker:
    """Track notification delivery and engagement"""

    async def track_sent(self,
                        appointment_id: UUID,
                        channel: str,
                        delivery_id: str,
                        content: Dict[str, str]):
        """Track when notification is sent"""
        from app.config import get_supabase_client
        supabase = get_supabase_client()

        tracking_data = {
            'appointment_id': str(appointment_id),
            'channel': channel,
            'delivery_id': delivery_id,
            'content': content,
            'sent_at': datetime.utcnow().isoformat(),
            'status': 'sent'
        }

        supabase.table('notification_tracking').insert(tracking_data).execute()

    async def track_delivery(self, delivery_id: str, status: str):
        """Track delivery confirmation"""
        from app.config import get_supabase_client
        supabase = get_supabase_client()

        supabase.table('notification_tracking').update({
            'status': status,
            'delivered_at': datetime.utcnow().isoformat()
        }).eq('delivery_id', delivery_id).execute()

    async def track_engagement(self, delivery_id: str, engagement_type: str):
        """Track customer engagement (opened, clicked, replied)"""
        from app.config import get_supabase_client
        supabase = get_supabase_client()

        supabase.table('notification_tracking').update({
            'engagement_type': engagement_type,
            'engaged_at': datetime.utcnow().isoformat()
        }).eq('delivery_id', delivery_id).execute()
```

## 4. Calendar Component Architecture

```typescript
// Frontend calendar components (React/TypeScript)

interface AppointmentCalendarProps {
  viewType: 'day' | 'week' | 'month' | 'team';
  teamMemberId?: string;
  filters: AppointmentFilters;
  onAppointmentSelect: (appointment: Appointment) => void;
  onSlotSelect: (slot: TimeSlot) => void;
  onAppointmentDrop: (appointmentId: string, newSlot: TimeSlot) => void;
  readOnly?: boolean;
  showWeatherAlerts?: boolean;
  showTravelTimes?: boolean;
}

interface AppointmentFilters {
  status?: AppointmentStatus[];
  appointmentTypes?: RoofingAppointmentType[];
  dateRange?: { start: Date; end: Date };
  teamMembers?: string[];
  weatherDependent?: boolean;
  priority?: SchedulingPriority[];
}

interface TimeSlot {
  start: Date;
  end: Date;
  teamMemberId: string;
  available: boolean;
  conflicts?: ConflictInfo[];
  weatherSuitable?: boolean;
  travelTime?: number;
}

interface ConflictInfo {
  type: 'time_overlap' | 'travel_time' | 'weather' | 'team_unavailable';
  severity: 'hard' | 'soft' | 'warning';
  description: string;
  suggestions?: string[];
}

// Main calendar component
class AppointmentCalendar extends React.Component<AppointmentCalendarProps, AppointmentCalendarState> {

  constructor(props: AppointmentCalendarProps) {
    super(props);
    this.state = {
      appointments: [],
      availability: [],
      selectedDate: new Date(),
      draggedAppointment: null,
      conflictHighlights: [],
      weatherAlerts: [],
      loading: false
    };
  }

  async componentDidMount() {
    await this.loadAppointments();
    await this.loadAvailability();

    if (this.props.showWeatherAlerts) {
      await this.loadWeatherAlerts();
    }

    // Set up real-time updates
    this.setupWebSocketConnection();
  }

  async loadAppointments() {
    this.setState({ loading: true });

    try {
      const response = await appointmentAPI.getAppointments({
        ...this.props.filters,
        team_member_id: this.props.teamMemberId,
        start_date: this.getViewStartDate(),
        end_date: this.getViewEndDate()
      });

      this.setState({
        appointments: response.data,
        loading: false
      });
    } catch (error) {
      console.error('Failed to load appointments:', error);
      this.setState({ loading: false });
    }
  }

  async loadAvailability() {
    if (!this.props.teamMemberId) return;

    try {
      const response = await teamAPI.getAvailability(
        this.props.teamMemberId,
        this.getViewStartDate(),
        this.getViewEndDate()
      );

      this.setState({ availability: response.data });
    } catch (error) {
      console.error('Failed to load availability:', error);
    }
  }

  async loadWeatherAlerts() {
    try {
      const response = await weatherAPI.getWeatherAlerts(
        this.getViewStartDate(),
        this.getViewEndDate()
      );

      this.setState({ weatherAlerts: response.data });
    } catch (error) {
      console.error('Failed to load weather alerts:', error);
    }
  }

  setupWebSocketConnection() {
    const socket = new WebSocket(`ws://localhost:5000/ws/appointments`);

    socket.onmessage = (event) => {
      const update = JSON.parse(event.data);
      this.handleRealTimeUpdate(update);
    };
  }

  handleRealTimeUpdate(update: any) {
    switch (update.type) {
      case 'appointment_created':
      case 'appointment_updated':
      case 'appointment_cancelled':
        this.loadAppointments();
        break;
      case 'availability_changed':
        this.loadAvailability();
        break;
      case 'weather_alert':
        this.loadWeatherAlerts();
        break;
    }
  }

  async handleAppointmentDrop(appointmentId: string, newSlot: TimeSlot) {
    try {
      // Optimistic update
      this.updateAppointmentOptimistically(appointmentId, newSlot);

      // Check for conflicts
      const conflicts = await this.checkConflicts(appointmentId, newSlot);

      if (conflicts.length > 0) {
        // Show conflict resolution dialog
        this.showConflictResolution(appointmentId, newSlot, conflicts);
        return;
      }

      // Perform the update
      await appointmentAPI.rescheduleAppointment(appointmentId, {
        new_scheduled_date: newSlot.start,
        duration: newSlot.end.getTime() - newSlot.start.getTime()
      });

      // Reload data
      await this.loadAppointments();

    } catch (error) {
      console.error('Failed to reschedule appointment:', error);
      // Revert optimistic update
      this.loadAppointments();
    }
  }

  async checkConflicts(appointmentId: string, newSlot: TimeSlot): Promise<ConflictInfo[]> {
    try {
      const response = await appointmentAPI.checkConflicts(appointmentId, newSlot);
      return response.conflicts || [];
    } catch (error) {
      console.error('Failed to check conflicts:', error);
      return [];
    }
  }

  render() {
    const { viewType, readOnly, showWeatherAlerts, showTravelTimes } = this.props;
    const { appointments, availability, weatherAlerts, loading } = this.state;

    if (loading) {
      return <LoadingSpinner />;
    }

    return (
      <div className="appointment-calendar">
        <CalendarHeader
          viewType={viewType}
          selectedDate={this.state.selectedDate}
          onDateChange={(date) => this.setState({ selectedDate: date })}
          onViewTypeChange={this.handleViewTypeChange}
        />

        {showWeatherAlerts && weatherAlerts.length > 0 && (
          <WeatherAlertsBar alerts={weatherAlerts} />
        )}

        <CalendarGrid
          viewType={viewType}
          appointments={appointments}
          availability={availability}
          selectedDate={this.state.selectedDate}
          onAppointmentSelect={this.props.onAppointmentSelect}
          onSlotSelect={this.props.onSlotSelect}
          onAppointmentDrop={readOnly ? undefined : this.handleAppointmentDrop}
          showTravelTimes={showTravelTimes}
          conflictHighlights={this.state.conflictHighlights}
        />

        {this.state.draggedAppointment && (
          <DragPreview appointment={this.state.draggedAppointment} />
        )}

        <ConflictResolutionDialog
          isOpen={this.state.showConflictDialog}
          conflicts={this.state.pendingConflicts}
          onResolve={this.handleConflictResolution}
          onCancel={this.handleConflictCancel}
        />
      </div>
    );
  }
}

// Weather alerts component
const WeatherAlertsBar: React.FC<{ alerts: WeatherAlert[] }> = ({ alerts }) => {
  return (
    <div className="weather-alerts-bar">
      {alerts.map(alert => (
        <div key={alert.id} className={`weather-alert ${alert.severity}`}>
          <WeatherIcon type={alert.weatherType} />
          <span>{alert.message}</span>
          <Button size="sm" onClick={() => alert.onViewDetails?.()}>
            Details
          </Button>
        </div>
      ))}
    </div>
  );
};

// Conflict resolution dialog
const ConflictResolutionDialog: React.FC<ConflictResolutionProps> = ({
  isOpen,
  conflicts,
  onResolve,
  onCancel
}) => {
  const [selectedResolution, setSelectedResolution] = useState<string>('');

  return (
    <Modal isOpen={isOpen} onClose={onCancel}>
      <div className="conflict-resolution-dialog">
        <h3>Scheduling Conflicts Detected</h3>

        {conflicts.map(conflict => (
          <div key={conflict.id} className={`conflict-item ${conflict.severity}`}>
            <div className="conflict-description">
              <strong>{conflict.type.replace('_', ' ').toUpperCase()}</strong>
              <p>{conflict.description}</p>
            </div>

            {conflict.suggestions && (
              <div className="conflict-suggestions">
                <h4>Suggested Solutions:</h4>
                {conflict.suggestions.map((suggestion, index) => (
                  <label key={index} className="suggestion-option">
                    <input
                      type="radio"
                      name="resolution"
                      value={suggestion}
                      onChange={(e) => setSelectedResolution(e.target.value)}
                    />
                    {suggestion}
                  </label>
                ))}
              </div>
            )}
          </div>
        ))}

        <div className="dialog-actions">
          <Button variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={() => onResolve(selectedResolution)}
            disabled={!selectedResolution}
          >
            Apply Resolution
          </Button>
        </div>
      </div>
    </Modal>
  );
};
```

## 5. API Extensions

```python
# Enhanced appointment routes with new features

@bp.route('/availability/smart-suggestions', methods=['POST'])
@require_auth
def get_smart_scheduling_suggestions():
    """
    Get AI-powered scheduling suggestions

    Body:
    {
        "customer_id": "uuid",
        "appointment_type": "detailed_roof_inspection",
        "priority": "high",
        "preferred_time_slots": [
            {"start": "2025-01-15T09:00:00", "end": "2025-01-15T17:00:00"}
        ],
        "location": "123 Main St, Detroit, MI",
        "weather_dependent": true,
        "max_travel_distance": 25
    }

    Returns:
        200: List of optimal appointment slots with scores
        400: Invalid request
        500: Server error
    """
    try:
        data = request.get_json()

        # Validate request
        scheduling_request = SmartSchedulingRequest(**data)

        # Get smart suggestions
        smart_scheduler = SmartSchedulingService()
        suggestions = await smart_scheduler.find_optimal_appointment_slots(scheduling_request)

        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'total': len(suggestions)
        })

    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Smart scheduling failed: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@bp.route('/<appointment_id>/weather-check', methods=['GET'])
@require_auth
def check_appointment_weather(appointment_id: str):
    """
    Check weather conditions for a specific appointment

    Returns:
        200: Weather check results
        404: Appointment not found
        500: Server error
    """
    try:
        # Get appointment
        appointment = get_appointment_by_id(appointment_id)
        if not appointment:
            return jsonify({'success': False, 'error': 'Appointment not found'}), 404

        # Check weather
        weather_service = WeatherService()
        is_suitable, weather_data = await weather_service.check_weather_suitability(
            appointment,
            appointment.location
        )

        return jsonify({
            'success': True,
            'weather_suitable': is_suitable,
            'weather_data': weather_data,
            'recommendations': _get_weather_recommendations(is_suitable, weather_data)
        })

    except Exception as e:
        logger.error(f"Weather check failed: {str(e)}")
        return jsonify({'success': False, 'error': 'Weather check failed'}), 500

@bp.route('/team-coordination', methods=['POST'])
@require_auth
@require_role(['manager', 'admin'])
def coordinate_team_appointment():
    """
    Create appointment requiring multiple team members

    Body:
    {
        "appointment_type": "large_project_inspection",
        "customer_id": "uuid",
        "scheduled_date": "2025-01-15T10:00:00",
        "duration": 120,
        "required_team_members": ["uuid1", "uuid2"],
        "optional_team_members": ["uuid3"],
        "minimum_team_size": 2,
        "location": "123 Main St, Detroit, MI"
    }

    Returns:
        200: Team appointment created
        400: Scheduling conflicts
        500: Server error
    """
    try:
        data = request.get_json()

        # Check availability for all required team members
        conflicts = []
        for member_id in data['required_team_members']:
            is_available, conflict = appointments_service.check_availability(
                member_id,
                datetime.fromisoformat(data['scheduled_date']),
                data['duration']
            )

            if not is_available:
                conflicts.append({
                    'team_member_id': member_id,
                    'conflict': conflict
                })

        if conflicts:
            return jsonify({
                'success': False,
                'error': 'Team members not available',
                'conflicts': conflicts
            }), 400

        # Create primary appointment
        primary_appointment_data = {
            'customer_id': data['customer_id'],
            'appointment_type': data['appointment_type'],
            'scheduled_time': datetime.fromisoformat(data['scheduled_date']),
            'team_member_id': data['required_team_members'][0],  # Lead member
            'duration': data['duration'],
            'location': data['location'],
            'notes': f"Team appointment - {len(data['required_team_members'])} members required"
        }

        success, appointment, error = appointments_service.create_appointment(**primary_appointment_data)

        if not success:
            return jsonify({'success': False, 'error': error}), 500

        # Create team coordination record
        team_coordination = MultiTeamAppointment(
            primary_appointment_id=appointment['id'],
            appointment_type=data['appointment_type'],
            lead_team_member=data['required_team_members'][0],
            required_team_members=data['required_team_members'],
            optional_team_members=data.get('optional_team_members', []),
            minimum_team_size=data.get('minimum_team_size', len(data['required_team_members']))
        )

        # Save team coordination
        supabase = get_supabase_client()
        supabase.table('team_appointments').insert(team_coordination.dict()).execute()

        # Create individual appointments for other team members
        for member_id in data['required_team_members'][1:]:
            member_appointment_data = primary_appointment_data.copy()
            member_appointment_data['team_member_id'] = member_id
            member_appointment_data['notes'] = f"Team appointment - coordinated with {appointment['id']}"

            appointments_service.create_appointment(**member_appointment_data)

        return jsonify({
            'success': True,
            'appointment': appointment,
            'team_coordination_id': team_coordination.id
        })

    except Exception as e:
        logger.error(f"Team coordination failed: {str(e)}")
        return jsonify({'success': False, 'error': 'Team coordination failed'}), 500

@bp.route('/analytics/efficiency', methods=['GET'])
@require_auth
@require_role(['manager', 'admin'])
def get_scheduling_efficiency():
    """
    Get scheduling efficiency analytics

    Query Parameters:
        - start_date: Analysis start date
        - end_date: Analysis end date
        - team_member_id: Optional team member filter

    Returns:
        200: Efficiency metrics
        500: Server error
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        team_member_id = request.args.get('team_member_id')

        analytics = SchedulingAnalytics()
        efficiency_data = analytics.calculate_efficiency_metrics(
            start_date=datetime.fromisoformat(start_date) if start_date else None,
            end_date=datetime.fromisoformat(end_date) if end_date else None,
            team_member_id=team_member_id
        )

        return jsonify({
            'success': True,
            'data': efficiency_data
        })

    except Exception as e:
        logger.error(f"Analytics calculation failed: {str(e)}")
        return jsonify({'success': False, 'error': 'Analytics failed'}), 500
```

This implementation guide provides the foundation for a world-class appointment management system specifically designed for roofing businesses. The key differentiators include weather integration, intelligent scheduling, team coordination, and customer experience optimization.

The system builds upon the existing solid foundation while adding roofing-industry specific features that will significantly improve operational efficiency and customer satisfaction.