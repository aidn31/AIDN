// AIDN TypeScript Types
// Based on database schema from AIDN_SPECIFICATION.md

export interface Agent {
  id: string;
  agent_name: string;
  phone: string;
  email: string;
  physical_description: string;
  car_description: string;
  google_calendar_id?: string;
  earliest_appointment_time: string;
  latest_appointment_time: string;
  slot_gap_hours: number;
  is_active: boolean;
}

export interface Lead {
  id: string;
  first_name: string;
  last_name: string;
  phone: string;
  address: string;
  city: string;
  county: string;
  state: string;
  zip_code: string;
  lead_type: 'final_expense' | 'term_life' | 'whole_life' | 'mortgage_protection';
  lead_source: string;
  agent_id: string;
  created_at: string;
  uploaded_at: string;
  last_called_at?: string;
  next_call_at?: string;
  call_count: number;
  call_outcome: 'fresh' | 'no_answer' | 'not_interested' | 'booked' | 'callback' | 'disconnected' | 'wrong_number' | 'dnc';
  is_active: boolean;
}

export interface AppointmentSlot {
  id: string;
  agent_id: string;
  date: string;
  time: string;
  status: 'available' | 'booked' | 'completed' | 'no_show' | 'cancelled';
  lead_id?: string;
  booked_at?: string;
}

export interface CallLog {
  id: string;
  lead_id: string;
  agent_id: string;
  call_sid?: string;
  started_at: string;
  ended_at?: string;
  duration_seconds?: number;
  outcome: string;
  recording_url?: string;
  transcript?: string;
  notes?: string;
}

export interface AgentAvailability {
  id: string;
  agent_id: string;
  day_of_week: number; // 0-6
  is_available: boolean;
  calling_start_time: string;
  calling_end_time: string;
  max_appointments: number;
}

export interface AgentTerritory {
  id: string;
  agent_id: string;
  county?: string;
  state: string;
  zip_code?: string;
  lead_types: string[];
}

// Dashboard-specific types
export interface DashboardStats {
  totalLeads: number;
  freshLeads: number;
  appointmentsToday: number;
  callsInProgress: number;
  conversionRate: number;
  showRate: number;
}

export interface LeadFilter {
  status?: string;
  county?: string;
  leadType?: string;
  dateRange?: {
    start: string;
    end: string;
  };
  searchTerm?: string;
}

export interface CallSession {
  id: string;
  leadId: string;
  agentId: string;
  status: 'initiating' | 'ringing' | 'connected' | 'completed' | 'failed';
  startTime: string;
  transcript?: string;
}