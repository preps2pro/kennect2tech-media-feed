# FeedForge - RSS Feed Generator

## Overview

FeedForge is a web application that generates custom RSS feeds from any website URL. Users can scrape content from web pages, categorize feeds (sports, tech, blockchain, etc.), and access generated RSS feeds for consumption in feed readers. The application now includes a **LinkedIn Publisher** feature for social media content distribution via Zapier webhooks or Buffer API. The application features a clean, Linear/Notion-inspired productivity interface focused on efficiency and clarity.

## Product Architecture

### Core MediaFeed Workflow
The main navigation consists of three core areas:
1. **Sources** - RSS feed creation and content discovery
2. **Portfolio** - Company management and signal-detected updates
3. **Distribute** - LinkedIn publishing via scheduling partners

### Web3 Sports VC News Hub
A public-facing landing page at `/hub` designed to attract VC investors with curated news:
- **Categories**: NFT & Digital Collectibles, Smart Contracts & Blockchain, Sports Sponsorships & Deals, VC Funding & Investment, Financial Management
- **Email Subscription**: Visitors can subscribe for weekly newsletter updates (stored in subscribers.json)
- **RSS Feeds**: Direct access to subscribe via RSS for any category
- **Category Filtering**: Filter news by specific topic areas
- **API Endpoints**:
  - `GET /hub` - News hub landing page
  - `POST /api/hub/subscribe` - Email newsletter signup
  - `GET /api/hub/subscribers` - List subscribers (admin only)

### Ownership Modules (Future Add-Ins)
The following are **optional, paid, separately-governed modules** that will NOT be part of the core MediaFeed workflow or main navigation:

1. **Preps2ProSurance** - Insurance-related services for the Preps2Pro ecosystem
2. **Fan Engagement** - Fan interaction and engagement tools
3. **Web3 Athlete Monetization** - Blockchain-based athlete monetization features

**Module Governance:**
- Opt-in activation only
- Paid tier features
- Separate governance and administration
- Architecturally isolated from core workflow

## LinkedIn Publisher Feature

The app includes a "Publish" tab for managing LinkedIn posts:
- **Post Queue**: Draft, approve, and send posts to LinkedIn
- **LinkedIn Copy Generator**: Automatically generates hook + bullet points + hashtags
- **Integrations**: Supports Zapier Catch Hook webhook or Buffer API
- **Rate Limiting**: Configurable max posts per day (default: 3)
- **Deduplication**: Prevents sending same URL twice

### Environment Variables for Publisher
- `ZAPIER_WEBHOOK_URL`: Your Zapier Catch Hook URL (recommended)
- `BUFFER_ACCESS_TOKEN`: Buffer API access token (alternative)
- `BUFFER_PROFILE_ID`: Buffer profile ID for LinkedIn

### API Endpoints
- `GET /api/publish/queue` - List queue items
- `POST /api/publish/queue` - Add to queue
- `PATCH /api/publish/queue/:id` - Update item
- `DELETE /api/publish/queue/:id` - Delete item
- `POST /api/publish/send/:id` - Send to LinkedIn via webhook
- `GET /api/publish/settings` - Get settings
- `POST /api/publish/settings` - Update settings

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Framework & Build System**
- React 18 with TypeScript for type-safe component development
- Vite as the build tool and development server
- Wouter for lightweight client-side routing (Dashboard, CreateFeed pages)
- TanStack React Query for server state management and caching

**UI Component System**
- Radix UI primitives for accessible, unstyled components
- shadcn/ui design system with custom Tailwind configuration
- "New York" style variant with customized spacing and colors
- Tailwind CSS for utility-first styling with CSS variables for theming
- Class Variance Authority (CVA) for component variant management

**Design System Approach**
- Linear/Notion-inspired productivity interface prioritizing content hierarchy and efficient workflows
- Typography: Inter (primary), JetBrains Mono (code/URLs)
- Spacing system using consistent Tailwind units (2, 4, 6, 8, 12, 16)
- Dark/light theme support with localStorage persistence
- Information-dense layouts with maximum relevant data display

**State Management**
- React Query for API data fetching, caching, and synchronization
- Local component state with React hooks (useState, useForm)
- React Hook Form with Zod validation for form handling
- Custom hooks for responsive behavior (useIsMobile) and toast notifications
- SavedItemsContext for reading list functionality (saved feeds and articles)
  - Uses localStorage for persistence without authentication
  - React Context API with memoized values for performance
  - Provides save/unsave/toggle functions for feeds and articles

### Backend Architecture

**Server Framework**
- Express.js HTTP server with TypeScript
- RESTful API design pattern
- HTTP server creation for potential WebSocket support

**Web Scraping Engine**
- Axios for HTTP requests with custom User-Agent headers
- Cheerio for HTML parsing and DOM manipulation
- Multi-selector strategy to extract articles from diverse website structures
- Automatic metadata extraction (titles, excerpts, URLs, images, publish dates)
- 15-second timeout and 20-article limit per scrape

**RSS Generation**
- Custom RSS 2.0 XML generator with proper escaping and CDATA handling
- Atom feed self-reference links for feed autodiscovery
- Support for images in feed descriptions
- Proper pubDate and lastBuildDate handling

**Data Storage Pattern**
- Abstract IStorage interface for storage layer flexibility
- In-memory storage implementation (MemStorage) for development
- Schema designed for future database migration (Drizzle ORM ready)
- UUID-based feed identification

**Topic Discovery (Search)**
- Bing Web Search API or SerpAPI integration for topic-based website discovery
- Search by topic (e.g., "disney news", "sports tokens") to find relevant websites
- Auto-categorization of search results based on keyword matching
- 5-minute cache TTL to reduce API quota usage
- Fallback support: uses Bing if available, otherwise SerpAPI

**API Design**
- RESTful endpoints:
  - GET /api/feeds - List all feeds
  - GET /api/feeds/:id - Get single feed
  - GET /api/feeds/:id/articles - Get feed articles
  - GET /api/feeds/:id/rss - RSS XML output
  - GET /api/search?q=topic - Search for websites by topic (requires API key)
  - POST /api/scrape - Scrape website
  - POST /api/feeds - Create feed
  - DELETE /api/feeds/:id - Delete feed
  - GET /api/groups - List combined feed groups
  - GET /api/groups/:id/rss - Combined RSS XML output
  - POST /api/groups - Create combined feed group

**Build & Deployment**
- esbuild for server bundling with selective dependency bundling (allowlist strategy)
- Vite for client build
- Production build outputs to dist/ directory
- Static file serving for SPA with fallback routing

### Data Schema Design

**Feed Entity**
- id, title, sourceUrl, feedUrl (generated)
- categories array (sports, tech, blockchain, digital-assets, etc.)
- articleCount, lastUpdated timestamp, isActive status
- Zod validation schemas for type safety

**Article Entity**
- id, feedId (foreign key relationship)
- title, excerpt, url, publishedAt
- optional imageUrl for rich content

**Category System**
- Predefined category types as const array
- Multi-category support per feed
- Color-coded badge system for visual categorization

### Validation & Type Safety

**Schema Validation**
- Zod schemas for runtime validation
- Shared types between client and server (@shared/schema.ts)
- URL validation for feed sources and article links
- Type-safe API contracts

### Development Workflow

**Development Server**
- Vite HMR (Hot Module Replacement) for instant client updates
- Express middleware mode for integrated dev server
- Error overlay plugin for runtime error display
- Replit-specific plugins (cartographer, dev banner)

**Type Checking**
- Strict TypeScript configuration
- Path aliases for clean imports (@/, @shared/, @assets/)
- ESNext modules with bundler resolution

## External Dependencies

### UI Component Libraries
- **Radix UI**: Comprehensive set of accessible, unstyled React primitives (accordion, alert-dialog, avatar, checkbox, dialog, dropdown-menu, popover, select, tabs, toast, tooltip, etc.)
- **Lucide React**: Icon library for consistent iconography

### Data Fetching & State
- **TanStack React Query v5**: Server state management, caching, background refetching
- **React Hook Form**: Form state management with performance optimization
- **@hookform/resolvers**: Zod resolver integration for form validation

### Validation & Utilities
- **Zod**: TypeScript-first schema validation
- **class-variance-authority**: Type-safe component variants
- **clsx / tailwind-merge**: Conditional className utilities
- **date-fns**: Date manipulation and formatting

### Web Scraping
- **Axios**: Promise-based HTTP client with custom headers and timeout support
- **Cheerio**: Fast, jQuery-like HTML parsing for server-side scraping

### Database (Configured but Optional)
- **Drizzle ORM**: TypeScript ORM with PostgreSQL support
- **@neondatabase/serverless**: Serverless PostgreSQL driver
- **drizzle-kit**: Schema management and migrations
- Note: Application currently uses in-memory storage; database integration is prepared but not actively used

### Styling
- **Tailwind CSS**: Utility-first CSS framework
- **PostCSS with Autoprefixer**: CSS processing and vendor prefixing

### Routing
- **Wouter**: Minimalist client-side router (1.5KB alternative to React Router)

### Session Management (Configured)
- **express-session**: Session middleware (prepared for future authentication)
- **connect-pg-simple**: PostgreSQL session store (configured but not actively used)

### Development Tools
- **Vite**: Fast build tool and dev server
- **esbuild**: JavaScript bundler for production server builds
- **tsx**: TypeScript execution for build scripts and development
- **TypeScript**: Static type checking
- **@replit/vite-plugin-runtime-error-modal**: Development error overlay
- **@replit/vite-plugin-cartographer & dev-banner**: Replit-specific development enhancements

### Build Optimization
- Selective dependency bundling strategy (allowlist in build script)
- Server dependencies bundled to reduce cold start syscalls
- External dependencies exclude non-critical packages