# RSS Feed Generator - Design Guidelines

## Design Approach
**Selected Approach:** Design System - Linear/Notion-inspired productivity interface
**Rationale:** This is a utility-focused tool for content aggregation and feed management. Users need efficiency, clarity, and robust functionality over visual flair. The interface should feel professional, fast, and purpose-built.

## Core Design Principles
1. **Content-First Hierarchy** - Feed data, URLs, and article previews are the heroes
2. **Efficient Workflows** - Minimize clicks from URL input to RSS feed generation
3. **Information Density** - Display maximum relevant data without overwhelming users
4. **Professional Polish** - Clean, modern aesthetic that builds trust for handling web content

---

## Typography
- **Primary Font:** Inter (Google Fonts)
- **Monospace:** JetBrains Mono (for URLs, RSS XML)
- **Hierarchy:**
  - Page Titles: text-2xl/text-3xl, font-semibold
  - Section Headers: text-lg/text-xl, font-medium
  - Body Text: text-sm/text-base, font-normal
  - Labels/Metadata: text-xs/text-sm, font-medium, uppercase tracking
  - Code/URLs: JetBrains Mono, text-sm

## Layout System
**Spacing Units:** Consistently use Tailwind units of **2, 4, 6, 8, 12, 16**
- Component padding: p-4, p-6
- Section spacing: space-y-6, space-y-8
- Card gaps: gap-4, gap-6
- Page margins: mx-4 (mobile), mx-8 (desktop)

**Container Strategy:**
- Main content: max-w-7xl mx-auto
- Forms/Input areas: max-w-2xl
- Feed preview cards: max-w-4xl

---

## Application Structure

### Header (Persistent)
- Logo/brand on left
- Primary navigation: "Create Feed" | "My Feeds" | "Documentation"
- User account menu on right
- Sticky positioning with subtle shadow on scroll
- Height: h-16

### Main Dashboard Layout
**Two-Column Split (Desktop):**
- Left sidebar (w-64): Feed list navigation, category filters
- Right content area (flex-1): Dynamic content based on selection

**Mobile:** Stack vertically, collapsible sidebar

---

## Component Library

### 1. URL Input Form (Primary Interface)
**Layout:**
- Large text input field with placeholder: "Enter any website URL..."
- Input styling: Prominent border, focus ring, monospace font for typed URLs
- Submit button: "Generate RSS Feed" - large, primary action
- Optional settings below input: Category tags (Sports, Tech, Blockchain, etc.), feed refresh frequency selector
- All contained in elevated card (rounded-lg, border, shadow-sm)

### 2. Feed Preview Component
**Structure:**
- Header: Feed title, source URL, article count
- Article list: 5-10 preview items showing:
  - Article title (text-base, font-medium)
  - Publication date/time
  - Excerpt (text-sm, line-clamp-2)
  - Thumbnail image (if available, w-16 h-16, rounded)
- Footer actions: "Generate RSS" | "Edit Settings" buttons

### 3. Feed Management Dashboard
**Grid Layout:**
- Feed cards in responsive grid (grid-cols-1 md:grid-cols-2 lg:grid-cols-3)
- Each card displays:
  - Feed icon/favicon
  - Feed title and source domain
  - Category badges
  - Last updated timestamp
  - Quick actions: Copy RSS URL, Edit, Delete (icon buttons)
  - Active/Inactive status indicator

### 4. Feed Detail View
**Split Layout:**
- Left: Feed metadata panel (narrow, w-80)
  - RSS feed URL with copy button
  - Category tags
  - Creation date, last updated
  - Article count stats
  - Settings controls
- Right: Live feed preview (flex-1)
  - Scrollable article list
  - Pagination controls

### 5. Category Filter Sidebar
- Checkbox list with counts: "Sports (12)" | "Tech (8)" | "Blockchain (5)"
- "All Feeds" option at top
- Visual indicators for active filters

### 6. RSS XML Preview Modal
- Full-screen overlay with code syntax highlighting
- XML formatted with proper indentation
- Copy entire XML button
- Close/minimize controls

---

## Navigation Patterns
- Tab-based navigation for "Create" vs "Manage" modes
- Breadcrumbs for deep navigation (Dashboard > Feed Name > Edit)
- Quick search bar in header for finding feeds by URL or title

## Form Elements
**Inputs:**
- Border style with focus states (ring-2)
- Clear labels above inputs
- Helper text below for context
- Error states with red indicators and messages

**Buttons:**
- Primary: Solid fill, prominent for main actions
- Secondary: Outline style for alternative actions
- Icon buttons: Square, hover states, tooltips
- Consistent height: h-10 or h-12

## Data Display
**Tables (for feed article lists):**
- Striped rows for readability
- Sortable columns (title, date, category)
- Row hover states
- Compact spacing (py-2)

**Cards:**
- Subtle elevation (shadow-sm)
- Border for definition
- Hover lift effect (subtle)
- Consistent padding (p-6)

---

## Animations
**Minimal, purposeful only:**
- Smooth page transitions (150-200ms)
- Hover state transitions on interactive elements
- Loading spinners for async operations
- NO decorative scroll animations

## Accessibility
- Keyboard navigation for all interactive elements
- Focus indicators on all inputs/buttons (ring-2 offset)
- ARIA labels for icon-only buttons
- Proper heading hierarchy (h1 > h2 > h3)
- Form labels associated with inputs

---

## Key Screens

### 1. Create Feed Screen
Centered single-column layout with large URL input form, category selection below, and "Generate" CTA. Preview section appears below form after URL submission.

### 2. My Feeds Dashboard
Grid of feed cards with sidebar filters. Empty state with illustration and "Create your first feed" CTA for new users.

### 3. Feed Detail/Edit
Two-column: metadata sidebar + article preview. Inline editing capabilities for feed settings.

---

This design prioritizes **speed, clarity, and functionality** - a professional tool that users can trust with their content aggregation needs.