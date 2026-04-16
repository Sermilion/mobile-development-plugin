# Android Compose Adaptive Layouts

Use this topic file only after `android-compose` has already been selected for routed `kmp` work.

Read this file when the diff touches list-detail, panes, rails, `NavigationSuiteScaffold`, supporting panes, or large-screen-specific Compose surfaces.

This guidance adapts the adaptive panes and scene-oriented themes from the official Android navigation skills into a governed KMP add-on shape.

## Implementation guidance

- Treat adaptive list-detail and pane layouts as navigation/state problems, not just layout reshuffles.
- Keep selection state, detail-pane state, and top-level navigation state explicit so compact and expanded layouts can share the same underlying model.
- Avoid baking handset-only assumptions into list/detail flows. Expanded layouts often need both panes active without destroying the compact navigation story.
- When using adaptive scaffolds, apply insets to the individual panes or screens rather than padding the outer scaffold container.
- Navigation chrome such as rails, bars, or supporting panes should not own the content state they merely reveal.

## Review focus

- Check that compact and expanded layouts share the same underlying selection and detail state rather than maintaining divergent logic paths.
- Flag panes or navigation chrome that accidentally become the source of truth for domain state.
- Flag handset-only assumptions that break when more than one pane is visible at once.
- Flag adaptive scaffold usage that clips edge-to-edge content by padding the outer scaffold instead of the panes.

## Boundary

- Use this topic only for Android adaptive/pane behavior. Generic Compose layout cleanliness still belongs to `compose-guidelines.md`.
