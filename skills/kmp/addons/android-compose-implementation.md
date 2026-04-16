# KMP Android Compose Add-On

Use this governed add-on only after stack routing has already selected `kmp` and the current work clearly touches Android Compose UI.

This file is an implementation index, not a standalone skill or review rubric. It adapts transferable Android/Compose patterns from Google's public `android/skills` repository for use inside the governed KMP add-on model.

## Section index

Scan this file first. Then open only the linked topic files whose cues match the current work instead of loading all Android guidance by default.

- `## Activation signals`
  Read first to decide whether `android-compose` should apply at all.
- `[android-compose-edge-to-edge.md](android-compose-edge-to-edge.md)`
  Read when the diff touches `Scaffold`, app bars, lists, `WindowInsets`, system bars, IME behavior, Android activities, or `AndroidManifest.xml`.
- `[android-compose-navigation.md](android-compose-navigation.md)`
  Read when the diff touches `NavHost`, route models, deep links, multiple back stacks, conditional navigation, or returned results from subflows.
- `[android-compose-adaptive-layouts.md](android-compose-adaptive-layouts.md)`
  Read when the diff touches list-detail, panes, `NavigationSuiteScaffold`, rails, supporting panes, or large-screen-specific Android Compose surfaces.
- Generic Compose API and enforcement work stays in `compose-guidelines.md`; use this add-on only for Android-specific depth beyond the base Compose rubric.

## Activation signals

Activate `android-compose` when the routed KMP work includes signals such as:

- `@Composable` screens or reusable composables
- Compose UI state models or `collectAsStateWithLifecycle()`
- `Modifier` chains, previews, `remember*`, or Compose side effects
- Android UI-safe-area concerns such as system bars, IME, list inset handling, or activity-level Compose setup
- Android navigation/state concerns such as `NavHost`, deep links, pane navigation, or multi-back-stack flows

## Exclusions

Do not use this add-on for:

- XML/View-to-Compose migration workflows
- Android Studio, AGP, Gradle, Kotlin, or dependency upgrade playbooks
- Play Billing or other product-specific Android upgrade tasks
- Non-Compose KMP work

## Android-specific verification checklist

- The Android activity boundary enables the platform behavior the screen expects.
- Insets and IME handling are applied once, at the right layer, and still preserve usable scrolling.
- Navigation state survives the transitions this screen is expected to survive.
- Adaptive layouts preserve the same domain state across compact and expanded layouts.
- Returned results are consumed exactly once.

## Implementation boundary

This add-on should enrich KMP implementation work only after `kmp` routing. It must not be treated as a new top-level package, slash command, or default workflow outside the owning stack.
