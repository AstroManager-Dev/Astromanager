# Guest mobile overflow fix

## Scope
- guest-only mobile overflow on settings/info screens
- segmented settings tabs with lock icons
- guest topbar and collapse summary width handling
- locked overview bottom-nav label density

## Technical changes
- body role class added from auth context
- segmented switch forced into horizontal internal scrolling
- guest role gets denser tab spacing and smaller lock/icon spacing
- settings/info wrappers clamp overflow on guest mobile
- collapse summary rows may wrap for guest on narrow widths
- topbar inner/brand/actions now shrink safely for guest
- guest bottom-nav lock icon spacing reduced
