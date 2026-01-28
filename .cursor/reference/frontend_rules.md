# Frontend Development Rules - AIDN

**Purpose:** Task-specific rules for working on AIDN Next.js dashboard. Load this when building UI components, integrating with API, or styling with Tailwind CSS.

---

## 🏗️ Frontend Architecture

**Framework:** Next.js 13+ with App Router
**Language:** TypeScript (strict mode)
**Styling:** Tailwind CSS
**Design System:** Linear/Vercel/Stripe aesthetic (Slate + Emerald colors)

```
Dashboard (localhost:3000)
        ↓
Next.js App Router (app/)
        ├── pages (page.tsx files)
        ├── components (reusable UI)
        └── lib (API client, utilities)
        ↓
FastAPI Backend (localhost:8000)
```

---

## 📦 Project Structure

```
web-dashboard/
├── app/
│   ├── page.tsx              # Home/Dashboard
│   ├── leads/page.tsx        # Leads list
│   ├── analytics/page.tsx    # Analytics
│   ├── call-history/page.tsx # Call logs
│   ├── campaigns/page.tsx    # Campaigns
│   ├── scripts/page.tsx      # Call scripts
│   ├── settings/page.tsx     # Agent configuration (TODO)
│   ├── components/           # Reusable components
│   │   ├── layout/
│   │   │   └── AppLayout.tsx # Main app layout
│   │   ├── ui/
│   │   │   └── Header.tsx    # Page header
│   │   ├── Navigation.tsx    # Sidebar navigation
│   │   └── UploadLeadsModal.tsx
│   ├── types/
│   │   └── index.ts          # TypeScript types
│   ├── lib/
│   │   └── api.ts            # API client
│   ├── globals.css           # Global styles
│   └── layout.tsx            # Root layout
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

---

## 🎨 Design System

### Color Palette

**Primary (Emerald):** Accent, CTAs, success states
```tsx
bg-emerald-600 hover:bg-emerald-700  // Primary buttons
text-emerald-600                      // Primary text
border-emerald-200                    // Primary borders
```

**Neutral (Slate):** Text, backgrounds, borders
```tsx
bg-slate-50                  // Light background
bg-slate-100                 // Hover states
text-slate-900               // Primary text
text-slate-600               // Secondary text
text-slate-500               // Tertiary text
border-slate-200             // Default borders
```

**Status Colors:**
```tsx
// Fresh leads
bg-emerald-50 text-emerald-700 border-emerald-200

// Callbacks
bg-amber-50 text-amber-700 border-amber-200

// No answer
bg-slate-50 text-slate-600 border-slate-200

// Booked
bg-blue-50 text-blue-700 border-blue-200
```

### Typography

```tsx
// Page title
text-2xl font-bold text-slate-900

// Section heading
text-lg font-semibold text-slate-900

// Subsection heading
text-sm font-medium text-slate-700

// Body text
text-sm text-slate-600

// Labels
text-xs font-medium text-slate-500 uppercase tracking-wider
```

### Spacing & Layout

```tsx
// Page container
p-8           // Page padding

// Card/Section
p-6           // Inner padding
mb-6          // Bottom margin
space-y-4     // Vertical spacing between children

// Component spacing
gap-3         // Flex/grid gap
mr-3          // Right margin for inline elements
```

### Border Radius

```tsx
rounded-lg     // Default (0.5rem / 8px)
rounded-xl     // Cards (0.75rem / 12px)
rounded-full   // Pills/badges (9999px)
```

---

## ⚛️ React Component Patterns

### 1. Client Components (Always)

**AIDN dashboard uses 'use client' for all pages:**
```tsx
'use client';

import React, { useState, useEffect } from 'react';

const LeadsPage = () => {
  // Component logic
};

export default LeadsPage;
```

**Why:** Interactive features (state, effects, event handlers) require client components.

### 2. State Management

**Use useState for local state:**
```tsx
const [leads, setLeads] = useState([]);
const [loading, setLoading] = useState(true);
const [selectedLead, setSelectedLead] = useState(null);
const [filters, setFilters] = useState({
  status: 'all',
  leadType: 'all',
  county: 'all'
});
```

**Update immutably:**
```tsx
// ✅ Good
setFilters({...filters, status: newStatus});

// ❌ Bad
filters.status = newStatus;  // Mutates state
setFilters(filters);
```

### 3. Data Fetching with useEffect

**Pattern:**
```tsx
useEffect(() => {
  const loadLeads = async () => {
    try {
      const leadsData = await apiClient.getLeads('1');
      setLeads(leadsData);
    } catch (error) {
      console.error('Error loading leads:', error);
    } finally {
      setLoading(false);
    }
  };

  loadLeads();
}, []); // Empty deps = run once on mount
```

**Critical:** Always set loading to false in `finally` block.

### 4. Loading States

**Always show loading UI:**
```tsx
if (loading) {
  return (
    <AppLayout>
      <div className="flex-1 flex items-center justify-center">
        <div className="text-slate-500">Loading leads...</div>
      </div>
    </AppLayout>
  );
}
```

### 5. Error Handling

**Show user-friendly errors:**
```tsx
try {
  const result = await apiClient.uploadLeads(file);
  alert(`Successfully imported ${result.imported} leads!`);
} catch (error) {
  console.error('Upload failed:', error);
  alert('Upload failed. Please try again.');
}
```

**TODO:** Replace `alert()` with toast notifications.

---

## 🔌 API Integration

### API Client Pattern

**Located in:** `app/lib/api.ts`

**Usage:**
```tsx
import { apiClient } from '../lib/api';

// In component
const leads = await apiClient.getLeads(agentId);
```

### Direct Fetch (Temporary Pattern)

**Current call initiation:**
```tsx
const handleCallLead = async (leadId: string) => {
  const response = await fetch('http://localhost:8000/calls/initiate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lead_id: leadId }),
  });
  const data = await response.json();
  alert(`Call dispatched! ID: ${data.call_id}`);
};
```

**TODO:** Move to apiClient for consistency.

### Environment Variables

**Use for API URL:**
```tsx
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

**Why NEXT_PUBLIC_ prefix:** Exposes variable to browser.

---

## 📝 TypeScript Types

### Type Definitions

**Located in:** `app/types/index.ts`

**Core Types:**
```tsx
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
  call_outcome: 'fresh' | 'no_answer' | 'not_interested' | 'booked' | 'callback' | 'disconnected' | 'wrong_number' | 'dnc';
  call_count: number;
  created_at: string;
  is_active: boolean;
}
```

### Type Usage

**Function parameters:**
```tsx
const getStatusStyle = (status: string) => {
  // Type-safe switch
};
```

**Component props:**
```tsx
interface HeaderProps {
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
}

const Header: React.FC<HeaderProps> = ({ title, subtitle, children }) => {
  // Typed props
};
```

**State typing:**
```tsx
const [leads, setLeads] = useState<Lead[]>([]);
const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
```

---

## 🎨 Tailwind CSS Conventions

### Component Structure

**Card pattern:**
```tsx
<div className="bg-white rounded-xl border border-slate-200 p-6">
  <h3 className="text-lg font-semibold text-slate-900 mb-4">
    Card Title
  </h3>
  <div className="space-y-4">
    {/* Card content */}
  </div>
</div>
```

**Table pattern:**
```tsx
<div className="bg-white rounded-xl border border-slate-200">
  <div className="px-6 py-4 border-b border-slate-200">
    <h2 className="text-lg font-semibold text-slate-900">Table Title</h2>
  </div>
  <div className="overflow-x-auto">
    <table className="w-full">
      <thead className="bg-slate-50">
        {/* Table headers */}
      </thead>
      <tbody className="divide-y divide-slate-100">
        {/* Table rows */}
      </tbody>
    </table>
  </div>
</div>
```

### Button Styles

**Primary button:**
```tsx
<button className="px-4 py-2 text-sm text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors">
  Primary Action
</button>
```

**Secondary button:**
```tsx
<button className="px-4 py-2 text-sm text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors">
  Secondary Action
</button>
```

**Danger button:**
```tsx
<button className="px-4 py-2 text-sm text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors">
  Delete
</button>
```

### Form Inputs

**Text input:**
```tsx
<input
  type="text"
  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
  placeholder="Enter value..."
/>
```

**Select:**
```tsx
<select
  value={value}
  onChange={(e) => setValue(e.target.value)}
  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-emerald-500 focus:border-emerald-500"
>
  <option value="all">All Options</option>
  <option value="option1">Option 1</option>
</select>
```

### Status Badges

**Pattern:**
```tsx
<span className="px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
  Fresh
</span>
```

### Responsive Design

**Grid layout:**
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {/* Grid items */}
</div>
```

**Conditional visibility:**
```tsx
<div className="hidden md:block">
  {/* Only visible on medium screens and up */}
</div>
```

---

## 🗂️ Layout Components

### AppLayout

**Usage:**
```tsx
import AppLayout from '../components/layout/AppLayout';

<AppLayout>
  <Header title="Page Title" subtitle="Page description" />
  <div className="flex-1 overflow-auto">
    {/* Page content */}
  </div>
</AppLayout>
```

**Structure:**
- Sidebar navigation (left)
- Main content area (right)
- Responsive layout

### Header Component

**Usage:**
```tsx
<Header
  title="Leads"
  subtitle={`${leads.length} leads total`}
>
  <button>Action Button</button>
</Header>
```

**Renders:**
- Title + subtitle on left
- Action buttons on right (children)

---

## 🔀 Filtering & Sorting

### Filter Pattern

**State:**
```tsx
const [filters, setFilters] = useState({
  status: 'all',
  leadType: 'all',
  county: 'all'
});
```

**Filter logic:**
```tsx
const filteredLeads = leads.filter(lead => {
  if (filters.status !== 'all' && lead.call_outcome !== filters.status) {
    return false;
  }
  if (filters.leadType !== 'all' && lead.lead_type !== filters.leadType) {
    return false;
  }
  return true;
});
```

**Dynamic filter options:**
```tsx
const leadTypes = [...new Set(leads.map(lead => lead.lead_type))];
const counties = [...new Set(leads.map(lead => lead.county))];
```

---

## 🎭 Modal Pattern

**Structure:**
```tsx
{showModal && (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">
        Modal Title
      </h3>
      {/* Modal content */}
      <div className="flex justify-end mt-6 gap-3">
        <button onClick={() => setShowModal(false)}>Cancel</button>
        <button>Confirm</button>
      </div>
    </div>
  </div>
)}
```

**Key classes:**
- `fixed inset-0` - Full screen overlay
- `bg-black bg-opacity-50` - Darkened backdrop
- `z-50` - Above other content
- `max-w-md w-full mx-4` - Responsive width with margins

---

## 📊 Table Patterns

### Hoverable Rows

```tsx
<tr className="hover:bg-slate-50/50 transition-colors">
  {/* Row cells */}
</tr>
```

### Avatar Initials

```tsx
<div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center">
  <span className="text-slate-700 text-sm font-medium">
    {firstName?.[0]}{lastName?.[0]}
  </span>
</div>
```

### Action Buttons

```tsx
<button className="text-emerald-600 hover:text-emerald-900 mr-3">
  View
</button>
<button className="text-blue-600 hover:text-blue-900">
  Call
</button>
```

---

## 🚫 Common Pitfalls

### ❌ Don't Do This

1. **Forget 'use client' directive**
   ```tsx
   // ❌ Missing 'use client'
   import { useState } from 'react';
   
   const Component = () => {
     const [state, setState] = useState(); // Error!
   };
   ```

2. **Mutate state directly**
   ```tsx
   // ❌ Bad
   filters.status = 'fresh';
   setFilters(filters);
   ```

3. **No loading state**
   ```tsx
   // ❌ Bad - no loading indicator
   const [data, setData] = useState([]);
   
   useEffect(() => {
     fetchData().then(setData);
   }, []);
   
   return <div>{data.map(...)}</div>; // Empty on first render
   ```

4. **Hardcode API URL**
   ```tsx
   // ❌ Bad
   fetch('http://localhost:8000/api/leads')
   ```

5. **Use `any` type**
   ```tsx
   // ❌ Bad
   const [data, setData] = useState<any>([]);
   ```

### ✅ Do This Instead

1. **Add 'use client'**
   ```tsx
   'use client';
   
   import { useState } from 'react';
   
   const Component = () => {
     const [state, setState] = useState();
   };
   ```

2. **Update immutably**
   ```tsx
   setFilters({...filters, status: 'fresh'});
   ```

3. **Show loading state**
   ```tsx
   const [data, setData] = useState([]);
   const [loading, setLoading] = useState(true);
   
   if (loading) return <div>Loading...</div>;
   ```

4. **Use environment variable**
   ```tsx
   const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
   fetch(`${API_URL}/api/leads`)
   ```

5. **Use proper types**
   ```tsx
   const [data, setData] = useState<Lead[]>([]);
   ```

---

## 🧪 Testing Strategy

### 3 Levels of Frontend Testing

1. **Manual Testing** - Visual inspection in browser (fastest)
2. **Component Tests** - Jest/React Testing Library (unit tests)
3. **E2E Tests** - Cypress/Playwright (optional for MVP)

### Manual Testing (Primary for MVP)

**Testing Checklist:**

- [ ] Component uses `'use client'` directive
- [ ] All state properly typed (no `any`)
- [ ] Loading state implemented
- [ ] Error handling implemented
- [ ] Responsive design (works on mobile)
- [ ] Follows design system (Slate + Emerald colors)
- [ ] Uses Tailwind classes (no inline styles)
- [ ] API calls use apiClient or env variables
- [ ] Modal has close button and backdrop click
- [ ] Forms validate input before submission
- [ ] Buttons have hover states
- [ ] Links use Next.js `<Link>` component

**Test in Multiple Screen Sizes:**
```bash
# In browser DevTools (F12)
# Test these sizes:
- Mobile: 375px width
- Tablet: 768px width
- Desktop: 1440px width
```

### Component Tests (Jest + React Testing Library)

**Setup:**
```bash
npm install --save-dev jest @testing-library/react @testing-library/jest-dom
```

**jest.config.js:**
```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
};
```

**Test Component Rendering:**

**Location:** `web-dashboard/__tests__/components/Header.test.tsx`

```tsx
import { render, screen } from '@testing-library/react';
import Header from '@/app/components/ui/Header';

describe('Header Component', () => {
  it('renders title and subtitle', () => {
    render(
      <Header title="Leads" subtitle="100 total leads" />
    );
    
    expect(screen.getByText('Leads')).toBeInTheDocument();
    expect(screen.getByText('100 total leads')).toBeInTheDocument();
  });
  
  it('renders children (action buttons)', () => {
    render(
      <Header title="Leads">
        <button>Add Lead</button>
      </Header>
    );
    
    expect(screen.getByText('Add Lead')).toBeInTheDocument();
  });
});
```

**Test User Interactions:**

```tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LeadsPage from '@/app/leads/page';

describe('Leads Page', () => {
  it('loads and displays leads', async () => {
    // Mock API response
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve([
          {
            id: '1',
            first_name: 'John',
            last_name: 'Smith',
            phone: '+15551234567',
            call_outcome: 'fresh',
          }
        ]),
      })
    );
    
    render(<LeadsPage />);
    
    // Should show loading state initially
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('John')).toBeInTheDocument();
      expect(screen.getByText('Smith')).toBeInTheDocument();
    });
  });
  
  it('filters leads by status', async () => {
    render(<LeadsPage />);
    
    // Wait for leads to load
    await waitFor(() => screen.getByText('John'));
    
    // Click filter dropdown
    const statusFilter = screen.getByLabelText(/status/i);
    fireEvent.change(statusFilter, { target: { value: 'fresh' } });
    
    // Should only show fresh leads
    // (Implementation would filter the displayed leads)
  });
  
  it('initiates call when button clicked', async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({ call_id: 'test-123', status: 'dispatched' }),
      })
    );
    
    render(<LeadsPage />);
    
    await waitFor(() => screen.getByText('John'));
    
    // Click "Call" button
    const callButton = screen.getByRole('button', { name: /call/i });
    fireEvent.click(callButton);
    
    // Should have called API
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/calls/initiate'),
      expect.objectContaining({
        method: 'POST',
      })
    );
  });
});
```

**Test Form Validation:**

```tsx
describe('Upload Leads Modal', () => {
  it('shows error when no file selected', () => {
    render(<UploadLeadsModal />);
    
    const uploadButton = screen.getByRole('button', { name: /upload/i });
    fireEvent.click(uploadButton);
    
    expect(screen.getByText(/select a file/i)).toBeInTheDocument();
  });
  
  it('accepts CSV files', () => {
    render(<UploadLeadsModal />);
    
    const fileInput = screen.getByLabelText(/choose file/i);
    const file = new File(['lead data'], 'leads.csv', { type: 'text/csv' });
    
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    expect(fileInput.files[0]).toBe(file);
    expect(fileInput.files).toHaveLength(1);
  });
});
```

**Test State Management:**

```tsx
describe('Leads Filtering', () => {
  it('updates filter state when dropdown changes', () => {
    const { rerender } = render(<LeadsPage />);
    
    const statusFilter = screen.getByLabelText(/status/i);
    
    // Initially 'all'
    expect(statusFilter.value).toBe('all');
    
    // Change to 'fresh'
    fireEvent.change(statusFilter, { target: { value: 'fresh' } });
    expect(statusFilter.value).toBe('fresh');
  });
});
```

### API Mocking

**Mock fetch globally:**
```tsx
// In test file
beforeEach(() => {
  global.fetch = jest.fn();
});

afterEach(() => {
  jest.restoreAllMocks();
});
```

**Mock specific API call:**
```tsx
const mockLeads = [
  { id: '1', first_name: 'John', last_name: 'Smith' },
  { id: '2', first_name: 'Jane', last_name: 'Doe' },
];

global.fetch = jest.fn((url) => {
  if (url.includes('/leads')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockLeads),
    });
  }
  if (url.includes('/calls/initiate')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ call_id: 'test-123' }),
    });
  }
});
```

### Snapshot Testing

**Test component structure doesn't change unexpectedly:**
```tsx
import { render } from '@testing-library/react';

it('matches snapshot', () => {
  const { container } = render(
    <Header title="Leads" subtitle="100 leads" />
  );
  
  expect(container).toMatchSnapshot();
});

// First run creates snapshot file
// Subsequent runs compare against snapshot
// If structure changes, test fails (update snapshot if intentional)
```

### Run Tests

```bash
# All tests
npm test

# Watch mode (re-runs on file change)
npm test -- --watch

# Coverage report
npm test -- --coverage

# Single test file
npm test Header.test.tsx
```

### E2E Tests (Cypress - Optional for MVP)

**Install:**
```bash
npm install --save-dev cypress
```

**Test full user flow:**
```typescript
// cypress/e2e/leads-flow.cy.ts
describe('Leads Management Flow', () => {
  it('loads leads and initiates call', () => {
    // Visit page
    cy.visit('http://localhost:3000/leads');
    
    // Wait for leads to load
    cy.contains('John Smith').should('be.visible');
    
    // Click "Call" button
    cy.contains('Call').first().click();
    
    // Should show success message
    cy.contains('Call dispatched').should('be.visible');
  });
  
  it('filters leads by county', () => {
    cy.visit('http://localhost:3000/leads');
    
    // Select county filter
    cy.get('select[name="county"]').select('Cook');
    
    // Should only show Cook County leads
    cy.contains('Cook').should('be.visible');
    cy.contains('Lake').should('not.exist');
  });
});
```

### Accessibility Testing

**Check for a11y issues:**
```tsx
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

it('has no accessibility violations', async () => {
  const { container } = render(<LeadsPage />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### Visual Regression Testing (Future)

**Chromatic (for Storybook):**
- Takes screenshots of components
- Detects unintended visual changes
- Great for design system consistency

---

## ⚙️ Agent Settings Page (TODO - High Priority)

### Purpose
Allow human agents to configure their calling schedule, appointment goals, and territory preferences.

### Page Location
`app/settings/page.tsx`

### Required Configuration Sections

#### 1. Calling Schedule
**What agent configures:**
- Which days to work (Monday-Sunday checkboxes)
- What times to call leads each day (e.g., "9am-12pm, 2pm-5pm")
- Multiple time slots per day allowed

**Example UI:**
```tsx
<div className="space-y-4">
  <h3>Calling Schedule</h3>
  {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map(day => (
    <div key={day} className="flex items-center gap-4">
      <input type="checkbox" checked={schedule[day].enabled} />
      <span className="w-24">{day}</span>
      <input type="time" value={schedule[day].startTime1} placeholder="Start" />
      <input type="time" value={schedule[day].endTime1} placeholder="End" />
      <button>+ Add Time Slot</button>
    </div>
  ))}
</div>
```

**Data Structure:**
```tsx
interface DaySchedule {
  enabled: boolean;
  timeSlots: Array<{
    startTime: string; // "09:00"
    endTime: string;   // "12:00"
  }>;
}
```

#### 2. Appointment Goals
**What agent configures:**
- How many appointments per day (e.g., 4 on Monday, 5 on Thursday)
- What times appointments can be scheduled (earliest/latest)
- Time gap between appointments (e.g., 2 hours)

**Example UI:**
```tsx
<div className="space-y-4">
  <h3>Appointment Settings</h3>
  
  {/* Max appointments per day */}
  {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map(day => (
    <div key={day} className="flex items-center gap-4">
      <span className="w-24">{day}</span>
      <input 
        type="number" 
        min="0" 
        max="10"
        value={appointmentGoals[day]} 
        placeholder="Max appointments"
      />
    </div>
  ))}
  
  {/* Appointment time window */}
  <div>
    <label>Earliest appointment time</label>
    <input type="time" value={earliestAppointment} /> {/* e.g., 09:00 */}
  </div>
  
  <div>
    <label>Latest appointment time</label>
    <input type="time" value={latestAppointment} /> {/* e.g., 18:00 */}
  </div>
  
  {/* Gap between appointments */}
  <div>
    <label>Time between appointments</label>
    <select value={appointmentGapHours}>
      <option value="1">1 hour</option>
      <option value="1.5">1.5 hours</option>
      <option value="2">2 hours</option>
      <option value="2.5">2.5 hours</option>
      <option value="3">3 hours</option>
    </select>
  </div>
</div>
```

**Data Structure:**
```tsx
interface AppointmentSettings {
  maxAppointmentsPerDay: {
    [day: string]: number; // "monday": 4
  };
  earliestAppointmentTime: string; // "09:00"
  latestAppointmentTime: string;   // "18:00"
  gapBetweenAppointmentsHours: number; // 2
}
```

#### 3. Territory & Lead Preferences
**What agent configures:**
- Which counties to call (multi-select)
- Which lead types to call (checkboxes: final_expense, mortgage_protection, term_life, whole_life)

**Example UI:**
```tsx
<div className="space-y-4">
  <h3>Territory Preferences</h3>
  
  {/* County filter */}
  <div>
    <label>Counties to call</label>
    <select multiple value={selectedCounties}>
      <option value="Cook">Cook County</option>
      <option value="Lake">Lake County</option>
      <option value="DuPage">DuPage County</option>
      <option value="Will">Will County</option>
      {/* Populated from database */}
    </select>
    <p className="text-xs text-slate-500">Hold Ctrl/Cmd to select multiple</p>
  </div>
  
  {/* Lead type filter */}
  <div>
    <label>Lead types to call</label>
    <div className="space-y-2">
      <label className="flex items-center gap-2">
        <input type="checkbox" checked={leadTypes.includes('final_expense')} />
        <span>Final Expense</span>
      </label>
      <label className="flex items-center gap-2">
        <input type="checkbox" checked={leadTypes.includes('mortgage_protection')} />
        <span>Mortgage Protection</span>
      </label>
      <label className="flex items-center gap-2">
        <input type="checkbox" checked={leadTypes.includes('term_life')} />
        <span>Term Life</span>
      </label>
      <label className="flex items-center gap-2">
        <input type="checkbox" checked={leadTypes.includes('whole_life')} />
        <span>Whole Life</span>
      </label>
    </div>
  </div>
</div>
```

**Data Structure:**
```tsx
interface TerritoryPreferences {
  counties: string[]; // ["Cook", "Lake"]
  leadTypes: Array<'final_expense' | 'mortgage_protection' | 'term_life' | 'whole_life'>;
}
```

### API Integration (TODO)

**Required API Endpoints:**

1. **GET /agent/settings**
   - Fetch current agent settings
   - Response: Combined object with schedule, appointments, territory

2. **PUT /agent/settings**
   - Update agent settings
   - Request: Full settings object
   - Response: Updated settings

**Example API Call:**
```tsx
const saveSettings = async () => {
  const settings = {
    schedule: {
      monday: { enabled: true, timeSlots: [{ startTime: "09:00", endTime: "12:00" }] },
      // ... other days
    },
    appointments: {
      maxAppointmentsPerDay: { monday: 4, tuesday: 5 },
      earliestAppointmentTime: "09:00",
      latestAppointmentTime: "18:00",
      gapBetweenAppointmentsHours: 2,
    },
    territory: {
      counties: ["Cook", "Lake"],
      leadTypes: ["final_expense", "mortgage_protection"],
    },
  };
  
  const response = await fetch('http://localhost:8000/agent/settings', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });
  
  if (response.ok) {
    alert('Settings saved!');
  }
};
```

### Validation Rules

**Before saving:**
- [ ] At least one day enabled in calling schedule
- [ ] Time slots don't overlap within same day
- [ ] Appointment max per day not greater than available time slots
- [ ] At least one county selected
- [ ] At least one lead type selected
- [ ] Earliest appointment < Latest appointment
- [ ] Gap between appointments is reasonable (0.5-4 hours)

### TypeScript Types (Add to `app/types/index.ts`)

```tsx
export interface AgentSettings {
  schedule: WeeklySchedule;
  appointments: AppointmentSettings;
  territory: TerritoryPreferences;
}

export interface WeeklySchedule {
  [day: string]: DaySchedule; // "monday", "tuesday", etc.
}

export interface DaySchedule {
  enabled: boolean;
  timeSlots: TimeSlot[];
}

export interface TimeSlot {
  startTime: string; // "09:00"
  endTime: string;   // "12:00"
}

export interface AppointmentSettings {
  maxAppointmentsPerDay: {
    [day: string]: number; // "monday": 4
  };
  earliestAppointmentTime: string;
  latestAppointmentTime: string;
  gapBetweenAppointmentsHours: number;
}

export interface TerritoryPreferences {
  counties: string[];
  leadTypes: LeadType[];
}

export type LeadType = 'final_expense' | 'mortgage_protection' | 'term_life' | 'whole_life';
```

### How Calling Works After Settings Are Configured

**Example Scenario:**
```
Agent configures:
- Monday: Call 9am-12pm, max 4 appointments
- Territory: Cook County only
- Lead types: Final Expense only

AIDN behavior:
1. On Monday at 9am, starts calling leads that match:
   - county = 'Cook'
   - lead_type = 'final_expense'
   - call_outcome IN ('fresh', 'no_answer', 'callback')

2. When appointment is booked → counts toward daily goal (4 max)

3. When 4 appointments booked → stops calling for the day

4. Calls continue between 9am-12pm until goal reached or time window ends
```

### Design Notes
- Use tabs for each section (Schedule, Appointments, Territory)
- Show preview of what the calling behavior will be based on settings
- Warn if settings result in no leads to call (e.g., county has no leads)

---

## 🎯 Development Workflow

1. **Create page:** Add `page.tsx` in `app/[route]/`
2. **Add types:** Define interfaces in `app/types/index.ts`
3. **Build components:** Use Tailwind classes, no custom CSS
4. **Integrate API:** Use `apiClient` from `lib/api.ts`
5. **Handle states:** Loading, error, empty states
6. **Test locally:** Check responsive design, interactions
7. **Update AppLayout:** Add route to navigation if needed

---

## 📚 Reference Resources

- **Next.js Docs:** https://nextjs.org/docs
- **Tailwind CSS:** https://tailwindcss.com/docs
- **TypeScript:** https://www.typescriptlang.org/docs
- **Linear Design:** https://linear.app (for design inspiration)

---

*Reference Doc | Frontend | Last Updated: January 27, 2026*
