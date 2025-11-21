# TODO: Add Pagination to Community Games Section in Admin

## Implementation Steps
- [x] Edit templates/admin.html to add pagination HTML after the Community Games table, using page_suggestions and total_pages_suggestions variables.
- [x] Ensure pagination links include both page and page_suggestions parameters to preserve state for both games and suggestions sections.

## Testing and Verification
- [x] Test pagination by navigating through pages and verifying correct suggestions are displayed.
- [x] Verify that changing pages for games doesn't reset suggestion pages and vice versa.
