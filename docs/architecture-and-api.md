# Architecture and API contract

## Architecture

`backend/config` owns settings and URL routing. `backend/apps/accounts` supplies the email-unique user model. `backend/apps/stores` owns store membership and store-scoped catalog/order schema. Membership roles are owner, admin, editor, and viewer; mutations currently allow owner/admin/editor. Store records are never selected solely from a client supplied ID: views resolve the slug through the authenticated user's membership.

PostgreSQL is selected when `DB_NAME` is configured. Currency and totals use decimal database fields. Products carry stock and low-stock threshold; order items preserve product name and unit price at sale time. Order creation and inventory decrement are not implemented yet, so no transactional checkout guarantees are claimed.

## Frontend coordination

The initial contract preserves the routes in the development prompt. Responses currently use serializer JSON for stores/categories/products and a small object for theme/publication/analytics. Login uses email as the JWT identity. The frontend should not assume imports, order management, or assistant endpoints exist until their implementation and tests land. `POST /api/stores/` returns a slug generated server-side; canonical public host is deployment configuration, not returned as a live URL.

### Example

```http
POST /api/stores/
Authorization: Bearer <access>
Content-Type: application/json

{"name":"Chetan's Corner"}
```

```json
{"id":1,"name":"Chetan's Corner","slug":"chetans-corner","logo":"","contact_email":"","phone":"","business_info":{},"theme":"modern-clean","theme_settings":{},"is_published":false,"created_at":"..."}
```

Store-scoped list endpoints currently return arrays. DRF page pagination is configured globally, but these views do not yet use a paginated response wrapper. This is a known contract detail to align with Akshatha before frontend integration.
