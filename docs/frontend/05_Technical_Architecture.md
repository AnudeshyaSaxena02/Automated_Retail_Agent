# IDAM Retail Intelligence Platform

# 05_Technical_Architecture.md

---

# Document Metadata

| Property | Value |
|----------|-------|
| Document ID | IDAM-TA-001 |
| Version | 1.0 |
| Status | Draft |
| Owner | Frontend Architecture Team |
| Parent Documents | 01_Product_Vision.md, 02_Information_Architecture.md, 03_Design_System.md, 04_Page_Specifications.md |
| Related Documents | 06_Component_Library.md, 07_API_Mapping.md, 08_Implementation_Roadmap.md |

---

# Purpose

This document defines the technical architecture of the frontend application.

It establishes architectural standards, implementation patterns, project organization, rendering strategy, state management, API communication, authentication flow, performance optimizations, security considerations, and deployment architecture.

The objective is to ensure that the application remains scalable, maintainable, testable, and extensible throughout its lifecycle.

---

# Architecture Goals

The frontend architecture is designed around the following objectives.

## Scalability

- Modular feature organization
- Reusable UI components
- Independent feature development
- Minimal coupling

---

## Maintainability

- Predictable project structure
- Strict coding conventions
- Consistent state management
- Shared utilities

---

## Performance

- Fast initial load
- Minimal bundle size
- Optimized rendering
- Efficient data fetching

---

## Reliability

- Graceful error handling
- Retry mechanisms
- Fault isolation
- Stable navigation

---

## Security

- Secure authentication
- Protected routes
- Token handling
- API validation

---

## Developer Experience

- Strong typing
- Component isolation
- Fast builds
- Excellent debugging
- Predictable architecture

---

# Technology Stack

| Layer | Technology |
|---------|------------|
| Framework | Next.js 15 |
| UI | React 19 |
| Language | TypeScript |
| Styling | Tailwind CSS |
| Component Library | shadcn/ui |
| Icons | Lucide React |
| Animations | Framer Motion |
| State Management | Zustand |
| Server State | TanStack Query |
| Forms | React Hook Form |
| Validation | Zod |
| HTTP Client | Axios |
| Charts | Recharts |
| Tables | TanStack Table |
| Notifications | Sonner |
| Authentication | JWT |
| Testing | Vitest + Playwright |
| Linting | ESLint |
| Formatting | Prettier |

---

# High-Level Architecture

                        User

                         │

                Next.js Application

                         │

         ┌───────────────┼───────────────┐

         │               │               │

   UI Layer       Application Layer   Data Layer

         │               │               │

         │               │               │

   Components      Business Logic   API Services

         │               │               │

         └───────────────┼───────────────┘

                         │

                 FastAPI Backend

                         │

          SQLite / Vector Store / LLM


---

# Architectural Principles

The application follows several architectural principles.

## Separation of Concerns

Presentation, business logic, and data access remain isolated.

---

## Feature-Based Organization

Each business domain owns its own components, hooks, services, and utilities.

---

## Reusability

Shared UI components are developed once and reused throughout the application.

---

## Composition over Inheritance

Complex interfaces are assembled through component composition rather than inheritance.

---

## Single Responsibility

Every module should perform one clearly defined responsibility.

---

## Explicit Data Flow

Data should flow predictably through:

```

API

↓

TanStack Query

↓

Page

↓

Components

```

---

# Frontend Project Structure

```
frontend/

├── app/
│
├── components/
│
├── features/
│
├── hooks/
│
├── lib/
│
├── services/
│
├── stores/
│
├── providers/
│
├── types/
│
├── utils/
│
├── styles/
│
├── public/
│
├── tests/
│
└── middleware.ts

```

---

# Application Layers

The application is divided into logical layers.

## Presentation Layer

Responsible for:

- UI
- Layout
- Components
- Styling
- Animations

Contains

- app
- components

---

## Feature Layer

Responsible for:

- Business workflows
- Feature-specific logic

Contains

- features

---

## State Layer

Responsible for:

- Client state
- Global preferences
- UI state

Contains

- stores

---

## Data Layer

Responsible for:

- HTTP communication
- API integration
- Query management

Contains

- services

---

## Infrastructure Layer

Responsible for:

- Authentication
- Providers
- Utilities
- Shared configuration

Contains

- providers
- lib
- middleware

# Detailed Project Structure

The frontend follows a feature-oriented architecture while maintaining a clear separation between presentation, business logic, infrastructure, and shared utilities.

Each directory has a single, well-defined responsibility.

---

## Root Directory

```
frontend/

├── app/
├── components/
├── features/
├── services/
├── stores/
├── hooks/
├── providers/
├── lib/
├── types/
├── utils/
├── styles/
├── public/
├── tests/
├── middleware.ts
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── .env.local
```

---

# App Directory

```
app/

├── dashboard/
├── products/
├── customers/
├── orders/
├── ai/
├── knowledge/
├── login/
├── layout.tsx
├── page.tsx
├── loading.tsx
├── error.tsx
├── not-found.tsx
└── globals.css
```

## Responsibilities

The App Router is responsible for:

- Route definitions
- Nested layouts
- Loading boundaries
- Error boundaries
- Route-level metadata
- Server Components (where appropriate)

The `app` directory should contain routing logic only.

Business logic should never be implemented inside route files.

---

# Components Directory

```
components/

├── ui/
├── layout/
├── navigation/
├── dashboard/
├── products/
├── customers/
├── orders/
├── ai/
├── knowledge/
├── shared/
└── feedback/
```

---

## ui/

Contains reusable UI primitives.

Examples

```
Button

Input

Card

Badge

Avatar

Dialog

Tooltip

Tabs

Accordion

Dropdown

Table
```

These components should remain business-agnostic.

---

## layout/

Contains reusable layout components.

Examples

```
Sidebar

Header

Footer

Breadcrumb

PageContainer

Section

ContentLayout

WorkspaceLayout
```

---

## navigation/

Contains navigation-related components.

Examples

```
NavigationMenu

SidebarItem

SearchBar

CommandPalette

NavigationBreadcrumb

UserMenu
```

---

## dashboard/

Dashboard-specific reusable components.

Examples

```
KPICard

AnalyticsChart

RecentActivity

QuickActions

AIInsightPanel
```

---

## products/

Examples

```
ProductCard

ProductTable

ProductHeader

InventoryCard

RecommendationPanel

PricingCard
```

---

## customers/

Examples

```
CustomerCard

CustomerSummary

PurchaseHistory

MemoryTimeline

BehaviorCard
```

---

## orders/

Examples

```
OrderCard

OrderTable

Timeline

OrderSummary

StatusBadge
```

---

## ai/

Examples

```
ChatPanel

MessageBubble

PromptInput

CitationPanel

ResponseCard

TypingIndicator
```

---

## knowledge/

Examples

```
KnowledgeCard

SearchResult

DocumentPreview

RetrievedContext

CitationCard
```

---

## shared/

Contains reusable business-independent components.

Examples

```
PageHeader

EmptyState

LoadingSkeleton

SectionHeader

ConfirmationDialog

DataTableToolbar
```

---

## feedback/

Application feedback components.

Examples

```
Toast

Alert

ErrorBoundary

LoadingOverlay

ProgressIndicator
```

---

# Features Directory

The feature layer contains business logic.

```
features/

├── dashboard/
├── products/
├── customers/
├── orders/
├── ai/
├── knowledge/
└── auth/
```

Each feature owns:

```
feature/

├── api/
├── hooks/
├── services/
├── schemas/
├── types/
├── utils/
└── constants.ts
```

Example:

```
features/

products/

├── api/
│     getProducts.ts
│     getProduct.ts
│
├── hooks/
│     useProducts.ts
│     useProduct.ts
│
├── services/
│     productService.ts
│
├── schemas/
│     productSchema.ts
│
├── types/
│     product.ts
│
├── utils/
│     productHelpers.ts
│
└── constants.ts
```

---

# Services Directory

```
services/

├── api.ts
├── auth.ts
├── recommendation.ts
├── search.ts
├── customer.ts
├── product.ts
├── order.ts
└── ai.ts
```

Responsibilities

- HTTP client
- Request wrappers
- Response parsing
- API configuration
- Error normalization

Services should never contain UI code.

---

# Stores Directory

Global client state managed with Zustand.

```
stores/

├── authStore.ts
├── themeStore.ts
├── uiStore.ts
├── productStore.ts
├── customerStore.ts
├── aiStore.ts
└── preferenceStore.ts
```

Stores should contain only client-side state.

Server state belongs to TanStack Query.

---

# Hooks Directory

Reusable hooks shared across features.

```
hooks/

├── useDebounce.ts
├── usePagination.ts
├── useLocalStorage.ts
├── useMediaQuery.ts
├── usePrevious.ts
├── useTheme.ts
└── useKeyboardShortcut.ts
```

Rules

- Hooks should remain generic.
- Feature-specific hooks belong inside `features/<feature>/hooks`.

---

# Providers Directory

Application-wide providers.

```
providers/

├── QueryProvider.tsx
├── ThemeProvider.tsx
├── AuthProvider.tsx
├── ToastProvider.tsx
└── AppProvider.tsx
```

Responsibilities

- Context Providers
- Dependency Injection
- Global Configuration

---

# Lib Directory

Shared infrastructure.

```
lib/

├── axios.ts
├── queryClient.ts
├── auth.ts
├── logger.ts
├── env.ts
├── constants.ts
└── permissions.ts
```

---

# Types Directory

Global shared types.

```
types/

├── api.ts
├── auth.ts
├── common.ts
├── pagination.ts
├── response.ts
└── index.ts
```

Feature-specific interfaces should remain inside the respective feature.

---

# Utils Directory

Pure utility functions.

```
utils/

├── formatDate.ts
├── formatCurrency.ts
├── debounce.ts
├── download.ts
├── validation.ts
├── storage.ts
└── helpers.ts
```

Utilities must:

- Be deterministic
- Be stateless
- Have no side effects unless explicitly documented

---

# Styles Directory

```
styles/

├── globals.css
├── variables.css
├── animations.css
└── utilities.css
```

Responsibilities

- Global styles
- CSS variables
- Animation utilities
- Shared utility classes

---

# Public Directory

```
public/

├── images/
├── icons/
├── logos/
├── illustrations/
└── fonts/
```

Static assets only.

No generated content should be stored here.

---

# Tests Directory

```
tests/

├── unit/
├── integration/
├── e2e/
├── fixtures/
└── mocks/
```

Testing levels

- Unit Tests
- Integration Tests
- End-to-End Tests
- Mock Data
- Test Fixtures

---

# File Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Components | PascalCase | `ProductCard.tsx` |
| Hooks | camelCase with `use` prefix | `useProducts.ts` |
| Services | camelCase | `productService.ts` |
| Stores | camelCase | `authStore.ts` |
| Types | camelCase | `product.ts` |
| Utilities | camelCase | `formatCurrency.ts` |
| Constants | camelCase | `productConstants.ts` |

---

# Import Hierarchy

Imports should follow a consistent order.

1. React / Next.js
2. External libraries
3. Shared infrastructure (`lib`)
4. Services
5. Stores
6. Feature hooks
7. Components
8. Types
9. Utilities
10. Relative imports

This ordering improves readability and reduces merge conflicts.

---

# Dependency Rules

To preserve architectural boundaries:

- UI components must not call APIs directly.
- Route files must not contain business logic.
- Services must not import UI components.
- Utilities must not depend on React.
- Shared components must remain feature-independent.
- Feature modules should communicate through shared services or state, not direct cross-imports.

These constraints reduce coupling and improve maintainability.

# Routing Architecture

The application uses the **Next.js App Router** to implement a hierarchical, file-based routing system.

Routing is organized around business workspaces rather than technical modules.

This structure ensures predictable navigation, scalable route management, and independent feature ownership.

---

# Route Hierarchy

```
/

├── login
│
├── dashboard
│
├── products
│   ├── [productId]
│   └── search
│
├── customers
│   ├── [customerId]
│   └── [customerId]/memory
│
├── orders
│   └── [orderId]
│
├── ai
│
├── knowledge
│   └── chat
│
├── 403
│
└── 404
```

---

# Route Groups

Routes are organized into logical groups.

| Group | Responsibility |
|---------|---------------|
| Public | Login |
| Protected | Dashboard, Products, Customers, Orders |
| AI | AI Assistant, Knowledge Center |
| System | Error Pages |

---

# Layout Hierarchy

The application minimizes layout re-rendering by using nested layouts.

```
Root Layout

↓

Authenticated Layout

↓

Workspace Layout

↓

Page Layout

↓

Components
```

---

## Root Layout

Responsibilities

- Global Providers
- Theme
- Fonts
- Metadata
- Global CSS
- Error Boundary

Loaded once during application startup.

---

## Authenticated Layout

Responsibilities

- Sidebar
- Header
- Notifications
- User Menu
- Command Palette

Persists while navigating between protected pages.

---

## Workspace Layout

Each business module may define its own layout.

Examples

```
Products Layout

Customers Layout

Orders Layout

Knowledge Layout
```

Responsibilities

- Workspace navigation
- Secondary actions
- Shared filters
- Workspace breadcrumbs

---

## Page Layout

Responsible for page-specific composition only.

Should contain:

- Header
- Main content
- Supporting panels

Should **not** contain:

- Authentication logic
- API configuration
- Business services

---

# Rendering Strategy

The application uses a hybrid rendering model.

| Page Type | Rendering Strategy |
|-----------|-------------------|
| Login | Server Component |
| Dashboard | Server + Client |
| Product List | Server + Client |
| Product Details | Server + Client |
| Customer Pages | Server + Client |
| Orders | Server + Client |
| AI Workspace | Client Component |
| Knowledge Chat | Client Component |

---

## Server Components

Server Components are preferred whenever possible.

Responsibilities

- Static UI
- Initial data loading
- Layout rendering
- Metadata generation

Advantages

- Reduced JavaScript
- Faster initial load
- Better SEO
- Smaller bundles

---

## Client Components

Client Components are used only when interactivity is required.

Examples

- Search
- Filters
- Forms
- Chat
- Animations
- Tables
- Charts

---

## Rendering Rules

Use Server Components when:

- No browser APIs are required
- No local state is needed
- Data is rendered once

Use Client Components when:

- User interaction exists
- Local state exists
- Effects are required
- Browser APIs are used

---

# Route Protection

Protected pages require an authenticated session.

```
Request

↓

Middleware

↓

Authentication Check

↓

Authorized?

↓

Yes → Continue

↓

No → Redirect Login
```

---

## Protected Routes

The following routes require authentication.

```
/dashboard

/products

/customers

/orders

/ai

/knowledge
```

---

## Public Routes

```
/login

/403

/404
```

---

# Authentication Flow

```
Login Request

↓

Backend Validation

↓

JWT Issued

↓

Token Stored

↓

User Profile Loaded

↓

Redirect Dashboard
```

---

## Session Validation

Every protected request performs:

- Token validation
- Session verification
- Automatic refresh (if supported)
- Redirect on failure

---

# Middleware Responsibilities

The middleware layer performs:

- Authentication validation
- Route protection
- Redirect handling
- Security headers
- Permission checks (future)

Business logic must never be implemented inside middleware.

---

# Navigation Lifecycle

Standard navigation flow:

```
User Click

↓

Next.js Router

↓

Route Resolution

↓

Layout Reuse

↓

Server Fetch (if required)

↓

Hydration

↓

Interactive Page
```

---

## Navigation Rules

Navigation should:

- Preserve application state where appropriate
- Avoid full page reloads
- Maintain layout persistence
- Restore scroll position when appropriate
- Display loading indicators during transitions

---

# Breadcrumb Strategy

Every protected page displays a breadcrumb.

Example

```
Dashboard

↓

Products

↓

Product Details
```

Example

```
Dashboard

↓

Customers

↓

Customer Profile

↓

Customer Memory
```

Breadcrumbs should:

- Reflect the current navigation path
- Support direct navigation to parent pages
- Be generated dynamically where possible

---

# Deep Linking

Every page should support direct access through its URL.

Examples

```
/products/123

/customers/456

/orders/789
```

Requirements

- Load required data from the URL
- Validate identifiers
- Display appropriate error pages when resources are unavailable

---

# Error Routing

The routing layer must handle failures gracefully.

| Situation | Destination |
|-----------|-------------|
| Unknown Route | 404 |
| Unauthorized | 403 |
| Authentication Failure | Login |
| Missing Resource | Page-level Error State |
| Unexpected Exception | Global Error Boundary |

---

# Metadata Strategy

Each page defines metadata for browser presentation.

Required metadata

- Page Title
- Description
- Open Graph Title
- Open Graph Description
- Favicon
- Theme Color

Example

```
Products | IDAM Retail Intelligence

Customer Profile | IDAM Retail Intelligence

AI Workspace | IDAM Retail Intelligence
```

---

# URL Design Principles

URLs should be:

- Human-readable
- Predictable
- Stable
- REST-inspired
- Lowercase
- Hyphen-separated where applicable

Examples

Good

```
/products

/customers

/orders

/knowledge/chat
```

Avoid

```
/getProductPage

/customerDetailsPage

/order_info
```

---

# Route Performance Guidelines

Navigation should achieve the following targets.

| Metric | Target |
|---------|---------|
| Route Transition | < 200 ms |
| Initial Page Load | < 2 seconds |
| First Contentful Paint | < 1.8 seconds |
| Largest Contentful Paint | < 2.5 seconds |
| Time to Interactive | < 3 seconds |

---

# Routing Design Principles

The routing architecture follows these principles:

- File-based routing with App Router
- Persistent layouts across workspaces
- Clear separation of public and protected routes
- Hybrid rendering strategy
- URL-driven application state
- Minimal route-level business logic
- Optimized navigation performance
- Predictable route organization

# State Management Architecture

The frontend follows a layered state management strategy that separates server state, client state, form state, and local component state.

Each state category has a single owner to avoid duplication, synchronization issues, and unnecessary re-renders.

---

# State Ownership Model

The application uses four distinct state layers.

| State Type | Owner | Examples |
|------------|-------|----------|
| Server State | TanStack Query | Products, Customers, Orders, AI Responses |
| Global Client State | Zustand | Authentication, Theme, Sidebar, Preferences |
| Form State | React Hook Form | Login, Search Forms, Filters |
| Local UI State | React | Dialogs, Dropdowns, Hover States |

---

# State Hierarchy

```
Backend APIs

↓

TanStack Query

↓

Feature Hooks

↓

Pages

↓

Components

↓

Local Component State
```

Global application preferences remain in Zustand and are accessible throughout the application.

---

# Server State

## Purpose

Server state represents data retrieved from backend services.

Examples

- Products
- Customers
- Orders
- AI Conversations
- Knowledge Results
- Recommendations

This data is owned exclusively by TanStack Query.

---

## Responsibilities

TanStack Query is responsible for:

- Data fetching
- Caching
- Background refetching
- Retry logic
- Pagination
- Cache invalidation
- Optimistic updates
- Request deduplication

---

## Query Flow

```
Component

↓

Feature Hook

↓

Query Hook

↓

API Service

↓

Backend

↓

Query Cache

↓

Component Update
```

---

## Query Keys

Query keys should uniquely identify cached resources.

Examples

```
["products"]

["products", productId]

["customers"]

["customers", customerId]

["orders"]

["orders", orderId]

["recommendations", productId]

["semantic-search", query]

["knowledge", prompt]
```

---

## Cache Lifetime

| Data Type | Recommended Stale Time |
|-----------|-----------------------:|
| Products | 5 minutes |
| Customers | 5 minutes |
| Orders | 2 minutes |
| Dashboard Metrics | 60 seconds |
| Recommendations | 10 minutes |
| AI Responses | Session Only |
| Knowledge Search | 10 minutes |

---

## Cache Invalidation Rules

Invalidate affected queries after successful mutations.

Examples

```
Product Updated

↓

Invalidate

["products"]

↓

Invalidate

["products", id]
```

```
Customer Updated

↓

Invalidate

["customers"]

↓

Invalidate

["customers", id]
```

---

## Retry Strategy

Default retry policy:

- Network failure → Retry
- Timeout → Retry
- HTTP 500 → Retry
- HTTP 400 → Do not retry
- HTTP 401 → Redirect to Login
- HTTP 403 → Display Unauthorized Page
- HTTP 404 → Display Page-level Not Found State

---

# Global Client State

Global client state is managed with Zustand.

This layer stores UI-related and session-related state that is independent of server resources.

---

## Global Stores

```
authStore

themeStore

uiStore

preferenceStore

productStore

customerStore

aiStore
```

---

## Store Responsibilities

### authStore

Stores

- Authentication status
- User profile
- Access token metadata
- Session status

---

### themeStore

Stores

- Theme
- Accent color (future)
- Font scaling (future)

---

### uiStore

Stores

- Sidebar collapsed state
- Active dialogs
- Global loading indicators
- Notification visibility

---

### preferenceStore

Stores

- User preferences
- Table density
- Language (future)
- Dashboard configuration

---

### aiStore

Stores

- Active conversation ID
- Conversation context
- Prompt draft
- Recent prompts

---

# Form State

React Hook Form manages all form interactions.

Examples

- Login
- Search
- Filters
- AI Prompt
- Profile Forms

---

## Validation

Validation uses Zod schemas.

```
User Input

↓

React Hook Form

↓

Zod Validation

↓

Valid?

↓

Yes → Submit

↓

No → Display Errors
```

---

## Validation Principles

- Validate on submit by default
- Validate on blur when immediate feedback improves usability
- Never duplicate validation logic in components
- Keep schemas independent from UI

---

# Local Component State

React local state is used only for transient UI state.

Examples

- Dialog open/close
- Selected tab
- Tooltip visibility
- Expanded rows
- Hover state
- Temporary input values

---

## Local State Rules

Local state should never contain:

- API data
- Authentication
- Shared business data
- Global preferences

---

# Data Flow Architecture

The application follows a unidirectional data flow.

```
Backend

↓

API Service

↓

TanStack Query

↓

Feature Hook

↓

Page

↓

Reusable Components

↓

User Interaction

↓

Mutation

↓

Backend
```

---

# Feature Hooks

Each business feature exposes dedicated hooks.

Examples

```
useProducts()

useProduct()

useCustomers()

useCustomer()

useOrders()

useOrder()

useRecommendations()

useSemanticSearch()

useKnowledgeSearch()

useConversation()
```

Responsibilities

- Execute queries
- Execute mutations
- Normalize data
- Hide API implementation details
- Return typed results

Pages should consume hooks rather than calling services directly.

---

# Optimistic Updates

Optimistic updates may be used for operations with a high probability of success.

Recommended candidates:

- User preferences
- Dashboard layout
- Favorites (future)
- Saved prompts

Do not use optimistic updates for:

- Financial data
- Order status changes
- Inventory quantities
- Authentication

---

# Background Refetching

Background refresh is enabled where freshness is important.

| Resource | Strategy |
|----------|----------|
| Dashboard | Interval Refetch |
| Orders | Window Refocus |
| Products | Manual / Stale Time |
| Customers | Manual / Stale Time |
| AI Conversations | Manual |
| Knowledge Search | Manual |

---

# Pagination Strategy

Large datasets use server-side pagination.

```
Page

↓

Query

↓

Backend Pagination

↓

Result

↓

Cache

↓

Render
```

Pagination state includes:

- Current page
- Page size
- Total records
- Total pages
- Sort order

---

# Search State

Search is implemented using controlled form state with debounced server requests.

```
Input

↓

Debounce (300–500 ms)

↓

API Request

↓

Cache

↓

Render Results
```

Requirements

- Preserve search during navigation
- Cancel outdated requests
- Cache repeated queries

---

# Error State Management

Errors are categorized into four levels.

| Level | Example | Handling |
|--------|---------|----------|
| Component | Invalid field | Inline message |
| Feature | Failed query | Error card with retry |
| Page | Resource unavailable | Page-level error state |
| Application | Unexpected exception | Global error boundary |

---

# Loading State Management

Every asynchronous operation must expose a loading state.

Common patterns:

- Skeleton loaders
- Progress indicators
- Streaming placeholders (AI)
- Disabled submit buttons
- Optimistic placeholders where appropriate

Loading indicators should preserve layout stability to minimize layout shift.

---

# State Design Principles

The state management architecture follows these principles:

- Single source of truth for each state type
- Clear ownership boundaries
- Predictable data flow
- Minimal duplication
- Type-safe state access
- Cached server resources
- Small, focused global stores
- Reusable feature hooks
- Stateless presentation components

# API Communication Architecture

The frontend communicates with the backend exclusively through a centralized API layer.

All HTTP communication is abstracted behind service modules to ensure consistency, maintainability, testability, and type safety.

Components must never communicate with backend endpoints directly.

---

# Architecture Overview

```
UI Component

↓

Feature Hook

↓

API Service

↓

Axios Client

↓

HTTP Middleware

↓

FastAPI Backend

↓

Response

↓

TanStack Query Cache

↓

UI Update
```

---

# Design Principles

The API layer follows these principles.

- Single HTTP client
- Strong typing
- Centralized configuration
- Centralized error handling
- Consistent response normalization
- Automatic authentication
- Retry where appropriate
- Feature isolation

---

# Backend Integration

The frontend communicates with the existing FastAPI backend.

Primary backend capabilities include:

- Authentication
- Products
- Customers
- Orders
- Recommendations
- Semantic Search
- AI Assistant
- Retrieval-Augmented Generation (RAG)

The frontend should treat the backend as the single source of truth.

---

# HTTP Client

Axios is used as the application's HTTP client.

Responsibilities include:

- Request execution
- Authentication
- Timeout handling
- Retry integration
- Request cancellation
- Error normalization

---

## Client Configuration

```
Base URL

↓

Authentication Headers

↓

Timeout

↓

Request Interceptors

↓

Response Interceptors

↓

Error Handling
```

Recommended configuration

| Property | Value |
|----------|-------|
| Base URL | Environment Variable |
| Timeout | 30 seconds |
| Content Type | application/json |
| Credentials | Configurable |
| Compression | Enabled |

---

# Environment Configuration

Environment variables should isolate deployment-specific configuration.

```
NEXT_PUBLIC_API_URL

NEXT_PUBLIC_APP_NAME

NEXT_PUBLIC_ENVIRONMENT

NEXT_PUBLIC_ENABLE_AI

NEXT_PUBLIC_ENABLE_RAG
```

Sensitive values should never be exposed through public environment variables.

---

# Service Organization

Each business domain owns a dedicated service.

```
services/

auth.ts

product.ts

customer.ts

order.ts

recommendation.ts

search.ts

ai.ts

knowledge.ts
```

Responsibilities

- Execute requests
- Parse responses
- Normalize errors
- Return typed data

---

# Endpoint Organization

Endpoints are grouped by business capability.

```
Authentication

Products

Customers

Orders

Recommendations

Semantic Search

AI Assistant

Knowledge
```

Each feature interacts only with its own service layer.

---

# Request Lifecycle

```
Component

↓

Feature Hook

↓

API Service

↓

Axios Request

↓

FastAPI

↓

Response

↓

Normalization

↓

TanStack Query

↓

Component
```

---

# Authentication

Authenticated requests automatically include authorization headers.

```
User Login

↓

JWT Issued

↓

Stored Securely

↓

Interceptor Adds Header

↓

Authenticated Request
```

Unauthorized requests trigger session recovery or redirect to the login page.

---

# Request Interceptors

Request interceptors execute before every request.

Responsibilities

- Attach JWT
- Attach request ID (future)
- Attach locale (future)
- Log development requests
- Add tracing headers (future)

Business logic must never be implemented inside interceptors.

---

# Response Interceptors

Response interceptors process all backend responses.

Responsibilities

- Normalize responses
- Normalize errors
- Refresh authentication (future)
- Handle expired sessions
- Centralize logging

---

# Error Normalization

Backend errors are converted into a consistent frontend format.

Normalized structure

```
status

code

message

details

timestamp
```

This enables all UI components to consume errors uniformly.

---

# Error Categories

| HTTP Status | Meaning | Frontend Action |
|-------------|---------|-----------------|
| 400 | Invalid Request | Display validation error |
| 401 | Authentication Required | Redirect to Login |
| 403 | Permission Denied | Display Unauthorized Page |
| 404 | Resource Not Found | Display Page-level Not Found State |
| 409 | Conflict | Display conflict message |
| 422 | Validation Failed | Highlight invalid fields |
| 429 | Rate Limited | Display retry guidance |
| 500 | Server Error | Retry when appropriate |
| 503 | Service Unavailable | Retry with backoff |

---

# Response Normalization

All successful responses should follow a predictable structure before reaching the UI.

```
Response

↓

Normalization

↓

Typed Model

↓

Query Cache

↓

Component
```

The normalization layer converts backend payloads into frontend domain models where necessary, reducing coupling between UI components and backend response shapes.

---

# API Service Pattern

Each service follows a consistent internal structure.

```
Service

↓

HTTP Request

↓

Response Validation

↓

Response Mapping

↓

Return Typed Object
```

This ensures feature hooks always receive consistent, strongly typed data.

---

# Query Integration

TanStack Query is responsible for consuming API services.

Example flow

```
Page

↓

Feature Hook

↓

Query Hook

↓

API Service

↓

Axios

↓

Backend
```

Feature hooks abstract query configuration from pages.

---

# Mutation Flow

```
User Action

↓

Mutation Hook

↓

API Service

↓

Backend

↓

Success

↓

Cache Invalidation

↓

UI Refresh
```

Mutations should:

- Return typed results
- Invalidate affected queries
- Display success or error notifications
- Preserve navigation context where applicable

---

# Request Cancellation

Long-running requests should support cancellation.

Applicable scenarios

- Semantic Search
- AI Conversations
- Knowledge Search
- Live Search
- Auto-complete

If a newer request supersedes an older one, the older request should be cancelled to avoid stale responses.

---

# Pagination Strategy

Large datasets use server-side pagination.

Request parameters

```
page

pageSize

sort

direction

filters
```

The backend returns

```
items

page

pageSize

totalItems

totalPages
```

The frontend should not calculate pagination metadata.

---

# Search Requests

Search interactions use debounced API calls.

```
User Types

↓

Debounce

↓

API Request

↓

Cached Response

↓

Render Results
```

Repeated identical searches should reuse cached responses when appropriate.

---

# AI Request Pipeline

AI interactions may require multiple backend capabilities.

```
Prompt

↓

AI Service

↓

LLM Endpoint

↓

Optional Retrieval

↓

LLM Response

↓

Streaming Parser

↓

Conversation Update
```

The frontend should support streaming responses when provided by the backend.

---

# Semantic Search Flow

```
Natural Language Query

↓

Semantic Search Endpoint

↓

Vector Retrieval

↓

Ranked Results

↓

Result Cards
```

Semantic search results should include explanatory metadata when available.

---

# Recommendation Pipeline

```
Selected Entity

↓

Recommendation Endpoint

↓

Recommendation Engine

↓

Recommendation List

↓

Recommendation Components
```

Recommendations should load independently from the primary page content to avoid blocking initial rendering.

---

# Retry Policy

Automatic retries are limited to transient failures.

| Condition | Retry |
|-----------|-------|
| Network Failure | Yes |
| Timeout | Yes |
| HTTP 500 | Yes |
| HTTP 503 | Yes |
| HTTP 400 | No |
| HTTP 401 | No |
| HTTP 403 | No |
| HTTP 404 | No |
| Validation Error | No |

Retry attempts should use exponential backoff.

---

# Logging Strategy

Development

- Log request method
- Log endpoint
- Log duration
- Log response status

Production

- Log errors only
- Remove sensitive information
- Integrate with centralized monitoring (future)

---

# Security Considerations

The API layer should:

- Never expose secrets
- Sanitize request data
- Validate response structures
- Prevent accidental logging of tokens
- Enforce HTTPS in production
- Handle authentication failures consistently

---

# API Performance Guidelines

Target metrics

| Metric | Target |
|---------|-------:|
| API Response | < 500 ms |
| Search Response | < 700 ms |
| Recommendation Response | < 800 ms |
| AI First Token | < 2 seconds |
| AI Complete Response | < 10 seconds |

Performance targets should be monitored and reviewed as backend capabilities evolve.

---

# API Communication Principles

The API architecture follows these principles:

- Centralized HTTP client
- Feature-oriented services
- Strongly typed interfaces
- Consistent request lifecycle
- Uniform error handling
- Predictable caching
- Independent feature integration
- Minimal coupling between UI and backend

# Authentication & Security Architecture

The frontend implements a layered security model that protects application resources, user sessions, and communication with backend services.

Authentication, authorization, and route protection are implemented independently to maintain separation of concerns.

---

# Security Objectives

The architecture aims to achieve the following objectives.

## Authentication

- Verify user identity
- Establish authenticated sessions
- Protect private routes

---

## Authorization

- Restrict access to protected resources
- Prepare for role-based access control
- Prevent unauthorized navigation

---

## Data Protection

- Secure API communication
- Prevent data leakage
- Protect authentication tokens

---

## Session Integrity

- Detect expired sessions
- Recover gracefully when possible
- Prevent unauthorized requests

---

# Authentication Flow

```
User

↓

Login Form

↓

POST /auth/login

↓

Backend Authentication

↓

JWT Token

↓

Store Session

↓

Load User Profile

↓

Redirect Dashboard
```

---

# Session Lifecycle

```
Application Start

↓

Check Session

↓

Session Valid?

↓

Yes

↓

Load Application

↓

No

↓

Redirect Login
```

---

## Login Process

The login workflow consists of the following steps.

1. User enters credentials.
2. Client-side validation executes.
3. Authentication request is submitted.
4. Backend validates credentials.
5. JWT token is returned.
6. User profile is loaded.
7. Authenticated session is established.
8. User is redirected to the dashboard.

---

# Logout Flow

```
Logout

↓

Clear Session

↓

Clear Query Cache

↓

Clear Stores

↓

Redirect Login
```

Logging out should remove all user-specific data from client memory.

---

# Session Storage Strategy

The application separates authentication state from cached business data.

| Data | Storage |
|------|---------|
| Authentication Status | Zustand |
| User Profile | Zustand |
| Cached Resources | TanStack Query |
| Theme Preference | Local Storage |
| UI Preferences | Local Storage |

Sensitive authentication data should never be persisted in plain text.

---

# Protected Routes

The following routes require authentication.

```
/dashboard

/products

/customers

/orders

/ai

/knowledge
```

Unauthenticated users should be redirected to the login page.

---

# Route Authorization

Current Version

- Authenticated users
- Single permission level

Future Versions

- Administrator
- Manager
- Sales Executive
- Customer Support
- Read-only Analyst

The routing architecture should accommodate future role-based authorization without structural changes.

---

# Authorization Model

```
User

↓

Authenticated?

↓

Yes

↓

Permission Check

↓

Authorized?

↓

Yes

↓

Render Page
```

Unauthorized access results in the 403 page.

---

# Authentication Context

The authentication provider exposes the following information.

```
Current User

Authentication Status

Loading Status

Login

Logout

Session Refresh (future)
```

Business modules consume authentication state through the provider rather than directly accessing storage.

---

# Token Management

Responsibilities include:

- Attach token to authenticated requests
- Detect expired sessions
- Prevent duplicate authentication requests
- Clear invalid sessions
- Support future refresh-token workflows

The frontend should avoid direct manipulation of token values outside the authentication layer.

---

# Security Headers

Production deployments should enforce:

- HTTPS
- Strict Transport Security (HSTS)
- Content Security Policy (CSP)
- X-Frame-Options
- X-Content-Type-Options
- Referrer-Policy

Header configuration should be managed by the deployment environment.

---

# Input Validation

All user input must be validated before submission.

Validation occurs at two levels.

Client

- Required fields
- Format validation
- Immediate user feedback

Server

- Business validation
- Authorization
- Data integrity

Client validation improves usability but does not replace server validation.

---

# Output Handling

Responses displayed in the UI should:

- Escape untrusted content
- Avoid rendering raw HTML
- Display normalized error messages
- Prevent injection through dynamic content

---

# File Upload Security (Future)

If document uploads are introduced:

- Restrict supported file types
- Validate file size
- Scan uploaded content
- Reject malformed files
- Display upload progress
- Handle failures gracefully

---

# AI Security Considerations

AI interactions should follow additional safeguards.

- Preserve conversation isolation
- Prevent unauthorized context leakage
- Clearly distinguish generated content from retrieved content
- Display citations where available
- Avoid exposing internal system prompts

---

# Sensitive Information Handling

The frontend should never:

- Embed secrets in source code
- Expose API keys
- Log authentication tokens
- Display stack traces
- Store confidential information in browser storage

---

# Session Timeout

Inactive sessions should eventually expire.

Typical lifecycle

```
Idle User

↓

Session Timeout

↓

Warning (future)

↓

Logout

↓

Redirect Login
```

Future versions may implement automatic session refresh where supported by the backend.

---

# Security Event Handling

Critical security events include:

- Invalid authentication
- Expired session
- Unauthorized request
- Repeated failed login attempts
- Network failures during authentication

The application should respond predictably without exposing sensitive implementation details.

---

# Authentication Error Handling

| Scenario | Frontend Response |
|----------|-------------------|
| Invalid Credentials | Display login error |
| Expired Session | Redirect to login |
| Unauthorized | Display 403 page |
| Network Failure | Retry option |
| Backend Unavailable | Service unavailable message |

---

# Security Design Principles

The authentication and security architecture follows these principles:

- Least privilege
- Secure by default
- Defense in depth
- Centralized authentication
- Consistent authorization
- Protected route access
- Minimal exposure of sensitive data
- Separation of authentication from business logic

# Performance & Optimization Strategy

Performance is a core architectural requirement.

The frontend is designed to minimize bundle size, reduce unnecessary rendering, optimize network communication, and maintain a responsive user experience across supported devices.

---

# Performance Objectives

Target metrics:

| Metric | Target |
|---------|--------:|
| First Contentful Paint (FCP) | < 1.8 s |
| Largest Contentful Paint (LCP) | < 2.5 s |
| Time to Interactive (TTI) | < 3.0 s |
| Cumulative Layout Shift (CLS) | < 0.1 |
| Route Transition | < 200 ms |

---

# Rendering Optimization

Rendering strategies include:

- Server Components by default
- Client Components only for interactive features
- Incremental hydration
- Stable layouts during loading
- Minimized re-rendering

---

# Code Splitting

The application uses route-based and component-level code splitting.

Examples:

- AI Workspace
- Knowledge Center
- Analytics Charts
- Document Preview
- Recommendation Panels

Large modules should be loaded only when required.

---

# Lazy Loading

The following resources should be lazy loaded:

- Charts
- Images
- AI conversations
- Knowledge previews
- Heavy dialogs
- Optional panels

This reduces the initial JavaScript payload.

---

# Asset Optimization

Images should be:

- Responsive
- Optimized
- Compressed
- Served in modern formats when possible

Fonts should:

- Load efficiently
- Minimize layout shifts
- Avoid blocking rendering

---

# Data Fetching Optimization

Best practices:

- Cache frequently accessed data
- Avoid duplicate requests
- Cancel obsolete requests
- Prefetch predictable navigation targets
- Batch requests where appropriate

---

# Component Optimization

Reusable components should:

- Minimize prop drilling
- Avoid unnecessary state
- Memoize expensive calculations when justified
- Use stable keys for lists

Optimization should be driven by measurement rather than premature assumptions.

---

# Bundle Optimization

Strategies include:

- Tree shaking
- Dynamic imports
- Dependency review
- Eliminate unused code
- Avoid duplicate libraries

---

# Network Optimization

The frontend should:

- Use HTTP compression
- Reuse cached responses
- Minimize payload size
- Avoid redundant API calls

---

# AI Performance

AI workflows should:

- Stream responses when supported
- Display progressive output
- Load citations independently
- Keep the interface interactive during generation

---

# Monitoring Targets

Performance should be measured continuously using:

- Lighthouse
- Core Web Vitals
- Browser performance tools
- Production monitoring

---

# Performance Design Principles

The optimization strategy follows these principles:

- Fast initial render
- Progressive enhancement
- Efficient data transfer
- Predictable rendering
- Responsive interactions
- Continuous performance monitoring

# Testing Architecture

Testing is implemented as a multi-layer strategy to ensure correctness, stability, accessibility, and maintainability throughout the application lifecycle.

Testing responsibilities are distributed across unit, integration, end-to-end, performance, and accessibility testing.

---

# Testing Objectives

The testing strategy aims to:

- Detect regressions early
- Validate business workflows
- Verify API integrations
- Ensure UI consistency
- Maintain accessibility compliance
- Support continuous delivery

---

# Testing Pyramid

```

                End-to-End Tests
                     ▲
                     │
             Integration Tests
                     ▲
                     │
                Unit Tests

```

The majority of tests should be unit tests, followed by integration tests, with end-to-end tests focused on critical user journeys.

---

# Testing Stack

| Layer | Technology |
|--------|------------|
| Unit Testing | Vitest |
| Component Testing | React Testing Library |
| Integration Testing | Vitest + Mock Service Worker |
| End-to-End Testing | Playwright |
| Accessibility Testing | axe-core |
| Performance Testing | Lighthouse |

---

# Unit Testing

Unit tests validate isolated business logic.

Examples:

- Utility functions
- Custom hooks
- Validation schemas
- State stores
- Data transformers

Unit tests should not perform network requests.

---

# Component Testing

Component tests verify:

- Rendering
- User interaction
- Conditional states
- Accessibility
- Component composition

Common scenarios:

- Loading state
- Empty state
- Error state
- Success state

---

# Integration Testing

Integration tests validate communication between multiple frontend layers.

Examples:

- Page + Query Hook
- Form + Validation
- Mutation + Cache Invalidation
- Navigation + Protected Routes

Backend APIs should be mocked where practical.

---

# End-to-End Testing

Critical business workflows require browser-based validation.

Core scenarios include:

- User Login
- Dashboard Navigation
- Product Discovery
- Customer Search
- Order Inspection
- AI Conversation
- Knowledge Search
- Logout

---

# Accessibility Testing

Accessibility validation includes:

- Keyboard navigation
- Focus management
- Color contrast
- Screen-reader compatibility
- Semantic HTML
- Form labeling

Target compliance:

WCAG 2.1 AA

---

# Performance Testing

Performance validation measures:

- Lighthouse Score
- Core Web Vitals
- Bundle Size
- Route Transitions
- API Response Time

Performance regressions should block release until reviewed.

---

# Code Coverage Targets

| Category | Target |
|----------|--------:|
| Utilities | 95% |
| Hooks | 90% |
| Stores | 90% |
| Services | 85% |
| Components | 80% |
| Overall | 85% |

Coverage targets guide testing priorities but should not replace meaningful test design.

---

# Build Architecture

The frontend uses a production-oriented build pipeline based on Next.js.

---

## Build Process

```
Developer

↓

Type Checking

↓

Linting

↓

Unit Tests

↓

Production Build

↓

Optimization

↓

Deployment Artifact
```

---

## Build Validation

Every production build must complete:

- TypeScript compilation
- ESLint validation
- Unit tests
- Build optimization
- Static asset generation

---

# Deployment Architecture

The application supports multiple deployment environments.

| Environment | Purpose |
|------------|---------|
| Development | Local development |
| Testing | Automated validation |
| Staging | Release verification |
| Production | Live application |

---

## Deployment Flow

```
Git Repository

↓

Continuous Integration

↓

Automated Testing

↓

Production Build

↓

Deployment

↓

Health Check

↓

Release
```

Deployments should be repeatable and environment-independent.

---

# Configuration Management

Environment-specific configuration includes:

- API Base URL
- Feature Flags
- Logging Level
- Analytics
- AI Capabilities

Application behavior should not require code changes between environments.

---

# Observability & Monitoring

The application should expose operational visibility into frontend behavior.

---

## Monitoring Objectives

- Detect failures
- Measure performance
- Track user experience
- Identify regressions
- Support debugging

---

## Metrics

Key frontend metrics include:

- Route transitions
- API latency
- Error frequency
- AI response duration
- Search response duration
- Bundle size
- Core Web Vitals

---

## Error Reporting

Production error reporting should capture:

- Timestamp
- Route
- Browser
- Device
- Error message
- Stack trace (sanitized)
- Request identifier (when available)

Sensitive user information must never be logged.

---

## Logging Strategy

Development

- Detailed diagnostic logging

Production

- Structured error logging
- Minimal console output
- Centralized monitoring integration

---

# Coding Standards

The project follows consistent coding conventions.

---

## TypeScript

- Strict mode enabled
- Avoid `any`
- Explicit interfaces
- Strong typing for APIs

---

## Components

- One responsibility per component
- Prefer composition
- Keep presentation stateless
- Avoid duplicated logic

---

## Hooks

Hooks should:

- Be reusable
- Encapsulate business logic
- Avoid direct DOM manipulation
- Return typed values

---

## Services

Services should:

- Contain API communication only
- Return normalized data
- Remain UI-independent

---

## Naming Conventions

| Element | Convention |
|----------|------------|
| Components | PascalCase |
| Hooks | camelCase (`use...`) |
| Stores | camelCase |
| Services | camelCase |
| Types | PascalCase |
| Constants | UPPER_SNAKE_CASE |

---

# Documentation Standards

Each feature should include:

- Purpose
- Public API
- Dependencies
- Example usage
- Known limitations

Public components should include inline documentation where appropriate.

---

# Architecture Decision Records (ADRs)

Major architectural decisions should be documented.

Recommended ADR topics:

- Next.js App Router adoption
- Zustand selection
- TanStack Query adoption
- Tailwind CSS
- shadcn/ui
- Axios
- JWT authentication
- AI streaming strategy
- Feature-based architecture

Each ADR should capture:

- Context
- Decision
- Alternatives considered
- Consequences

---

# Technical Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Backend API changes | High | Strong typing and API abstraction |
| Large bundle size | Medium | Code splitting and lazy loading |
| AI latency | Medium | Streaming responses and placeholders |
| Cache inconsistency | Medium | Defined invalidation strategy |
| Authentication failures | High | Centralized session handling |
| Accessibility regressions | Medium | Automated accessibility testing |

---

# Architecture Traceability Matrix

| Architecture Area | Supporting Document |
|-------------------|---------------------|
| Product Vision | 01_Product_Vision.md |
| Information Architecture | 02_Information_Architecture.md |
| Design System | 03_Design_System.md |
| Page Specifications | 04_Page_Specifications.md |
| Technical Architecture | 05_Technical_Architecture.md |
| Component Definitions | 06_Component_Library.md |
| API Contracts | 07_API_Mapping.md |
| Delivery Plan | 08_Implementation_Roadmap.md |

---

# Architecture Summary

The frontend architecture establishes a modular, scalable, and maintainable foundation for the IDAM Retail Intelligence Platform.

The architecture emphasizes:

- Feature-oriented organization
- Strong separation of concerns
- Predictable data flow
- Type-safe API communication
- Efficient state management
- High-performance rendering
- Accessibility by default
- Comprehensive testing
- Secure authentication
- Production-ready deployment

Together with the Product Vision, Information Architecture, Design System, and Page Specifications, this document provides a complete technical blueprint for frontend implementation.

---

# Conclusion

This document defines the technical standards, architectural patterns, implementation guidelines, operational considerations, and governance required to build and maintain the frontend of the IDAM Retail Intelligence Platform.

It serves as the authoritative reference for frontend engineers, technical architects, QA engineers, and future contributors, ensuring consistency across development, testing, deployment, and long-term maintenance.
