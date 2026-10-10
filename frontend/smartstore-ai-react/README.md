# SmartStore AI — React + TypeScript frontend

A green-and-white commerce workspace inspired by the supplied standalone demo, redesigned as a responsive React + TypeScript/Vite application.

## Requirements

- Node.js 20 or newer recommended
- Your existing Django REST API running locally
- npm

## Run locally

1. Extract this ZIP.
2. Open a terminal inside `smartstore-ai-react`.
3. Install packages:

   ```bash
   npm install
   ```

4. Copy `.env.example` to `.env` and confirm the API URL:

   ```env
   VITE_API_BASE_URL=http://127.0.0.1:8000/api
   ```

5. Start the frontend:

   ```bash
   npm run dev
   ```

6. Open `http://localhost:5173`.

Keep Django running at `http://127.0.0.1:8000`. For browser requests from port 5173, configure Django CORS to allow that origin. Do not enable unrestricted CORS in production.

## Existing API integration

The frontend calls the existing API routes for:

- JWT login, refresh and current user
- Store list and creation
- Categories and bulk category creation
- Product list, creation, update and deletion
- Theme read/update
- Publish endpoint
- Store analytics
- Public store data

The app expects your backend to use the API paths and payload shapes documented in the project conversation. If your local backend differs, adjust `src/api.ts`.

## Checkpoint implementation map

1. **Onboarding wizard** — store name, business type, contact email, phone, address and description; basic browser validation. Logo upload currently previews locally only because the current API contract does not confirm a logo-upload endpoint.
2. **Categories** — predefined categories, custom category UI and API save.
3. **Dummy products** — sample product data with names, descriptions, prices and image URLs; sent to the product API. Some samples can fail if their SKU already exists; errors appear in the import report.
4. **CSV import** — downloadable CSV template, simple header checking, row validation, and error report. This first version parses simple comma-separated rows; for production, use a CSV parser library to support quoted commas, Excel `.xlsx`, column mapping and a downloadable error file.
5. **Themes** — four distinct themes with live preview and API theme selection. Persistent font/layout settings need additional backend schema support.
6. **Store URL** — the frontend shows a store path based on the slug. The current API publish response returns a path, not a configured subdomain or hosted public domain.
7. **Storefront** — responsive local preview with category navigation, search, product cards and a local cart. Real checkout/payment/order creation are not implemented by the current API.
8. **Admin dashboard** — connects to current analytics; the trend chart is illustrative because the API currently returns summary totals rather than time-series data.
9. **Content control** — content editor UI is prepared; saving arbitrary homepage sections, banners, footer and full brand styles needs additional API/model support. Current store PATCH support should be verified/implemented.
10. **Inventory management** — add, edit price/stock, delete, sample import and CSV import. Variants, bulk edit, discounts and image upload need backend support.
11. **Orders** — placeholder UI. Need order list/detail/status endpoints, line items, customer contact and notification/email service.
12. **Multi-tenant access** — frontend uses selected store slug, but actual isolation and owner/staff roles must be enforced by Django permissions/querysets. Do not rely on frontend checks for security.
13. **AI database assistant** — reads current analytics and low-stock information in local preview; optional endpoint hook supported via `VITE_AI_CHAT_ENDPOINT`. A real AI chatbot requires a store-scoped backend endpoint.
14. **AI safety/evidence** — UI shows source labels and refuses unsupported claims. Server must enforce read-only access, tenant scope, query allowlists, safe aggregation and source payloads.
15. **Responsive UI** — mobile/tablet/desktop CSS included for the dashboard, wizard, catalogue, themes and storefront.

## Backend work still needed for all 15 checkpoints

- Store logo file upload/storage and address/business fields as structured data.
- Product bulk edit, variants, discount pricing and image upload.
- `.xlsx` import, robust CSV parsing, column mapping and downloadable per-row error reports.
- Persisted visual/page-builder model for banners, sections, footer, fonts and colors.
- Real domain/subdomain routing and deployment.
- Shopping cart persistence, checkout, payment integration, order creation and customer emails/status updates.
- Order list/detail/status update APIs and order-item/product sales aggregates.
- Staff invitation/membership management and role-aware permissions.
- Store-scoped read-only AI endpoint that only queries safe, allowlisted data and returns evidence.
- Historical revenue series and top-selling-product aggregates.
- Production deployment configuration: CORS allowlist, HTTPS, secure secrets, logging, backups and error monitoring.

## Security notes

- JWT tokens are stored in browser local storage in this demo. For a higher-security production deployment, consider secure HttpOnly cookies and a reviewed CSRF/session strategy.
- Never expose Gemini/OpenAI provider keys in `VITE_*` environment variables.
- The AI assistant must not execute arbitrary SQL or trust a store slug supplied by a client without validating it against the authenticated user's memberships.
- Treat the storefront cart as a preview only until checkout and order endpoints exist.
