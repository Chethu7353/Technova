# Frontend–backend API audit

Audited against `frontend/smartstore-ai-react/src/api.ts`, `src/App.tsx`, `backend/config/api_urls.py`, `backend/apps/stores/views.py`, `import_views.py`, `assistant_views.py`, and DRF settings.

Protected JSON requests send `Authorization: Bearer <access>`. Login/registration/refresh and the slug-availability route are public. Public-store routes expose published stores only. Store APIs scope access through membership; writes require owner, admin, or editor membership where enforced. Store list pagination is DRF page-number pagination (`{count,next,previous,results}`); nested category/product endpoints return arrays.

| Frontend operation | Method and resolved path | Request | Auth | Backend response / verification |
|---|---|---|---|---|
| `register` | POST `/api/auth/register/` | JSON `username,email,password` (8+ chars) | Public | 201 `{id,username,email}`; serializer creates user |
| `login` | POST `/api/auth/login/` | JSON `email,password` | Public | 200 `{access,refresh}`; SimpleJWT uses email `USERNAME_FIELD` |
| refresh | POST `/api/auth/refresh/` | JSON `{refresh}` | Public | 200 `{access}`; refresh rotation is explicitly disabled |
| `me` | GET `/api/auth/me/` | — | JWT | 200 `{id,username,email}`; bearer round-trip tested |
| `stores` | GET `/api/stores/` | optional `page` query | JWT + membership | Paginated store serializer results; ordering is stable by primary key |
| `createStore` | POST `/api/stores/` | JSON store serializer fields | JWT | 201 store; owner membership created transactionally; anonymous 401 tested |
| `updateStore` | PATCH `/api/stores/{id}/` | Partial JSON store fields | JWT + membership | Updated store serializer |
| `uploadStoreAssets` | POST `/api/stores/{id}/assets/` | multipart `logo_image`, `banner_image` | JWT + writable membership | Store serializer with media URLs; image type/size validation tested |
| `slugAvailability` | GET `/api/stores/slug-availability/?slug=...` | slug query | Public | 200 `{slug,available}`; no store details; anonymous test passed |
| `categories` | GET `/api/stores/{slug}/categories/` | — | JWT + membership | Category array; tested |
| `createCategory` | POST same path | JSON `{name}` | JWT + writable membership | 201 category; duplicate name returns 400 |
| `bulkCategories` | POST `/api/stores/{slug}/categories/bulk/` | JSON `{categories:[{name}]}` | JWT + writable membership | 201 `{created,categories}`; validates duplicates before transaction |
| `products` | GET `/api/stores/{slug}/products/` | — | JWT + membership | Product array; tenant isolation tested |
| `createProduct` | POST same path | Product serializer JSON | JWT + writable membership | 201 product; category must belong to store; price must be positive |
| `updateProduct` | PATCH `/api/stores/{slug}/products/{id}/` | Partial product JSON | JWT + writable membership | Updated product; product scoped to store |
| `deleteProduct` | DELETE same path | — | JWT + writable membership | 204; product scoped to store |
| `importProducts` | POST `/api/stores/{slug}/products/import/` | multipart `file`, `commit` | JWT + writable membership | 200 preview/commit or 207 row errors; validates again and writes accepted rows in one transaction |
| `downloadXlsxTemplate` | GET `/api/stores/{slug}/products/import/template/` | — | JWT + writable membership | XLSX attachment with required/optional columns and store category; authorization tested |
| `themes` | GET `/api/stores/{slug}/theme/` (a plural `/themes/` alias also exists) | — | JWT + membership | `{themes,selected,settings}`; endpoint tested |
| `updateTheme` | PATCH `/api/stores/{slug}/theme/` | JSON `{theme,theme_settings}` | JWT + writable membership | `{theme,theme_settings}`; DB persistence tested |
| `publish` | POST `/api/stores/{slug}/publish/` | Empty JSON | JWT + writable membership | `{slug,url_path,is_published}`; persistence tested |
| `analytics` | GET `/api/stores/{slug}/analytics/` | — | JWT + membership | `{period_days,revenue,orders,pending_orders,low_stock}`; real database aggregates |
| `aiChat` | POST `/api/ai/chat/` | JSON `{store_slug,question}` | JWT + store membership | `{answer,store_slug,evidence}`; mocked provider, missing config, failure and tenant isolation tested |
| `publicStore` | GET `/api/public/stores/{slug}/` | — | Public; published only | Store/theme/categories and active non-demo products; unpublished 404 tested |
| `publicProduct` | GET `/api/public/stores/{slug}/products/{id}/` | — | Public; published store, active non-demo product | Customer-safe product fields; published/real-product behavior tested |
| Store slug creation | POST `/api/stores/` | Store name; slug optional | JWT | Django generates a normalized unique slug and retries collisions; duplicate-name and existing-record behavior covered by tests |
| `checkoutConfig` | GET `/api/public/stores/{slug}/checkout/config/` | — | Public; published store | Currency, configured delivery charge, COD enabled and Razorpay availability; never returns provider secret |
| `checkout` | POST `/api/public/stores/{slug}/checkout/` | JSON customer name/phone/address, `{items:[{product_id,quantity}]}`; UUID `Idempotency-Key` | JWT customer; published store | Server calculates current item prices and totals, validates stock, reserves inventory and persists order atomically; same key/request is idempotent, key reuse for another request returns 409 |
| `createPayment` | POST `/api/orders/{order_number}/payment/create/` | Empty JSON | JWT order owner | Creates a Razorpay provider order using server-held credentials and server-calculated amount; returns public key ID only; disabled with 503 when credentials unavailable |
| `verifyPayment` | POST `/api/orders/{order_number}/payment/verify/` | Razorpay payment/order IDs and signature | JWT order owner | Checks HMAC, queries Razorpay server-to-server, validates order, amount and currency, then records authorized/captured state; duplicate confirmed callback is idempotent |
| `failPayment` | POST `/api/orders/{order_number}/payment/fail/` | Empty JSON | JWT order owner | Marks unpaid attempt failed and releases reserved inventory exactly once; cannot downgrade authorized/paid order |
| `myOrders` / `customerOrder` | GET `/api/orders/my/`, GET `/api/orders/my/{order_number}/` | — | JWT customer | Returns only the authenticated customer’s persisted non-demo orders |
| `cancelMyOrder` | POST `/api/orders/my/{order_number}/cancel/` | Empty JSON | JWT order owner | Cancels eligible unpaid order and restores stock once; paid/authorized cancellation requires refund handling |
| `storeOrders` | GET `/api/stores/{slug}/orders/` | — | JWT store member | Returns only orders belonging to accessible store |
| `updateOrderStatus` | PATCH `/api/stores/{slug}/orders/{order_number}/status/` | JSON `{status}` | JWT owner/admin/editor | Enforces store membership and allowed fulfilment transitions; records status history, keeps payment state separate |
| `collectCodPayment` | POST `/api/stores/{slug}/orders/{order_number}/payment/collect/` | Empty JSON | JWT owner/admin/editor | Confirms a pending COD payment only after delivery; repeat confirmation is idempotent |

## Auth and 401 findings

Django is configured for `JWTAuthentication`, `Bearer`, HS256 signed by the configured Django secret, five-minute access tokens, one-day refresh tokens, no issuer/audience, and no refresh rotation. `/api/stores/` correctly returns 401 without an access token. The live local unauthenticated GET returned 401 with `WWW-Authenticate: Bearer` and the expected CORS origin. An authenticated JWT login → `/auth/me/` → `/stores/` test succeeds, as does refresh → protected request.

The API client had a confirmed stale-session defect: module-level tokens were read only at page load, so a second tab could continue sending stale credentials after another tab changed or cleared local storage. Refreshes also were not shared across concurrent 401s. The client now syncs storage changes, skips Authorization on auth endpoints, coordinates one refresh request, persists an optional rotated refresh token, retries a protected request at most once, and clears rejected sessions. This is a confirmed client defect; without a browser network capture, it cannot be asserted as the sole cause of the reported Chrome request.

## Remaining API limitations

Razorpay credentials are optional: set `RAZORPAY_MODE=test`, `RAZORPAY_KEY_ID` with the `rzp_test_` prefix, and `RAZORPAY_KEY_SECRET` in ignored `backend/.env`. The public storefront never receives the secret. If keys are absent, card checkout is unavailable while COD remains enabled. The backend tests stub provider HTTP responses; they verify signature/status handling but do not demonstrate a real Razorpay transaction. Paid-order refund processing and delivery-provider integration are not implemented. Production media storage/CDN is not configured; `FileSystemStorage` and `/media/` serving are development-only.
