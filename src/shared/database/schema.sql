-- AIDN Database Schema
-- Based on AIDN_SPECIFICATION.md

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Leads table
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    county VARCHAR(100),
    state VARCHAR(10),
    zip_code VARCHAR(10),
    lead_type VARCHAR(50) CHECK (lead_type IN ('final_expense', 'term_life', 'whole_life', 'mortgage_protection')),
    lead_source VARCHAR(100),
    agent_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    uploaded_at TIMESTAMP DEFAULT NOW(),
    last_called_at TIMESTAMP,
    next_call_at TIMESTAMP,
    call_count INTEGER DEFAULT 0,
    call_outcome VARCHAR(50) CHECK (call_outcome IN (
        'fresh', 'no_answer', 'not_interested', 'booked', 'callback',
        'disconnected', 'wrong_number', 'dnc'
    )) DEFAULT 'fresh',
    is_active BOOLEAN DEFAULT true,

    FOREIGN KEY (agent_id) REFERENCES agent_profiles(id)
);

-- Agent profiles table
CREATE TABLE agent_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    physical_description TEXT,
    car_description TEXT,
    google_calendar_id VARCHAR(255),
    earliest_appointment_time TIME DEFAULT '09:00:00',
    latest_appointment_time TIME DEFAULT '18:00:00',
    slot_gap_hours INTEGER DEFAULT 2,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Agent availability table
CREATE TABLE agent_availability (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL,
    day_of_week INTEGER CHECK (day_of_week >= 0 AND day_of_week <= 6), -- 0 = Sunday
    is_available BOOLEAN DEFAULT false,
    calling_start_time TIME,
    calling_end_time TIME,
    max_appointments INTEGER DEFAULT 0,
    first_appointment_time TIME,

    FOREIGN KEY (agent_id) REFERENCES agent_profiles(id),
    UNIQUE(agent_id, day_of_week)
);

-- Agent territories table
CREATE TABLE agent_territories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL,
    county VARCHAR(100),
    state VARCHAR(10) NOT NULL,
    zip_code VARCHAR(10),
    lead_types VARCHAR(50)[] DEFAULT '{}', -- Array of lead types

    FOREIGN KEY (agent_id) REFERENCES agent_profiles(id)
);

-- Appointment slots table
CREATE TABLE appointment_slots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    status VARCHAR(50) CHECK (status IN ('available', 'booked', 'completed', 'no_show', 'cancelled')) DEFAULT 'available',
    lead_id UUID,
    booked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (agent_id) REFERENCES agent_profiles(id),
    FOREIGN KEY (lead_id) REFERENCES leads(id),
    UNIQUE(agent_id, date, time)
);

-- Call logs table
CREATE TABLE call_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    call_sid VARCHAR(255), -- Twilio Call SID
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP,
    duration_seconds INTEGER,
    outcome VARCHAR(50),
    recording_url TEXT,
    transcript TEXT,
    notes TEXT,

    FOREIGN KEY (lead_id) REFERENCES leads(id),
    FOREIGN KEY (agent_id) REFERENCES agent_profiles(id)
);

-- Indexes for performance
CREATE INDEX idx_leads_agent_id ON leads(agent_id);
CREATE INDEX idx_leads_call_outcome ON leads(call_outcome);
CREATE INDEX idx_leads_next_call_at ON leads(next_call_at);
CREATE INDEX idx_leads_county_state ON leads(county, state);
CREATE INDEX idx_appointment_slots_agent_date ON appointment_slots(agent_id, date);
CREATE INDEX idx_appointment_slots_status ON appointment_slots(status);
CREATE INDEX idx_call_logs_lead_id ON call_logs(lead_id);
CREATE INDEX idx_call_logs_started_at ON call_logs(started_at);

-- Functions for appointment booking
CREATE OR REPLACE FUNCTION book_appointment(
    p_slot_id UUID,
    p_lead_id UUID
) RETURNS TABLE(success BOOLEAN, slot_id UUID) AS $$
BEGIN
    -- Atomic booking to prevent double-booking
    UPDATE appointment_slots
    SET status = 'booked',
        lead_id = p_lead_id,
        booked_at = NOW()
    WHERE id = p_slot_id
      AND status = 'available';

    IF FOUND THEN
        RETURN QUERY SELECT true, p_slot_id;
    ELSE
        RETURN QUERY SELECT false, p_slot_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to generate appointment slots for an agent
CREATE OR REPLACE FUNCTION generate_appointment_slots(
    p_agent_id UUID,
    p_start_date DATE,
    p_end_date DATE
) RETURNS INTEGER AS $$
DECLARE
    current_date DATE := p_start_date;
    availability_record RECORD;
    slot_time TIME;
    slots_created INTEGER := 0;
BEGIN
    WHILE current_date <= p_end_date LOOP
        -- Get availability for this day of week
        SELECT * INTO availability_record
        FROM agent_availability
        WHERE agent_id = p_agent_id
          AND day_of_week = EXTRACT(DOW FROM current_date)
          AND is_available = true;

        IF FOUND THEN
            -- Generate slots based on availability
            slot_time := availability_record.first_appointment_time;

            FOR i IN 1..availability_record.max_appointments LOOP
                -- Insert slot if it doesn't exist
                INSERT INTO appointment_slots (agent_id, date, time, status)
                VALUES (p_agent_id, current_date, slot_time, 'available')
                ON CONFLICT (agent_id, date, time) DO NOTHING;

                IF FOUND THEN
                    slots_created := slots_created + 1;
                END IF;

                -- Move to next slot time
                SELECT slot_time + INTERVAL '1 hour' * (
                    SELECT slot_gap_hours FROM agent_profiles WHERE id = p_agent_id
                ) INTO slot_time;
            END LOOP;
        END IF;

        current_date := current_date + INTERVAL '1 day';
    END LOOP;

    RETURN slots_created;
END;
$$ LANGUAGE plpgsql;