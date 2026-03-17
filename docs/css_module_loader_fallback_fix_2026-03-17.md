# CSS module loader fallback fix

## Problem
The secondary CSS module files were not loaded reliably because the discovery logic only scanned one project-root based path.
Depending on the active runtime layout, that path could be empty even though the module CSS files existed under the Flask static directory.

## Fix
- Prefer `APP.static_folder/css/modules`
- Fall back to `/app/code/...` layout
- Fall back to `/project-core/code/...` layout
- Return the first non-empty module list

## Result
`base.html` keeps the existing loop, but `css_module_files` is now populated reliably for raw-list module CSS and later CSS modules.
