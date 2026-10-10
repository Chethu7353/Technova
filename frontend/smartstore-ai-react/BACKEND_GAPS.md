# SmartStore AI backend integration gaps

The frontend can connect to the known Django endpoints, but these requirements need backend work before they can be claimed as complete:

1. Store logo upload endpoint/storage; structured address field if required.
2. Store update (`PATCH`) endpoint and permissions for owner/staff.
3. Product variants, discounts, image upload, bulk update and robust import.
4. Persisted homepage sections/banner/footer/theme typography and layout settings.
5. Public URL routing and actual production domain/subdomain configuration.
6. Cart/checkout/payment and order creation endpoints.
7. Owner order list/detail/status updates; status notification email/SMS.
8. Order line items and product-level sales aggregates.
9. Historical revenue series for weekly/monthly comparisons.
10. Store-scoped AI assistant endpoint with allowlisted read-only query tools, strict tenant validation and evidence/source fields.
11. Staff membership/invitation endpoints and role-based permissions.
12. Production settings: exact CORS allowlist, HTTPS, secure token handling, logging and error monitoring.

Security reminder: authorization must be enforced by Django on every request. The React UI is not a security boundary.
