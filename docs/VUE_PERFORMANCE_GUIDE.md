# Vue 3 Performance Best Practices

This document outlines performance optimization strategies for the Vue 3 frontend in the Cultivation World Simulator project.

## 1. Handling Large Objects (`shallowRef`)

### Context
When receiving large, deeply nested JSON objects from the backend (e.g., full avatar details, game state snapshots), Vue's default reactivity system (`ref` or `reactive`) converts every single property at every level into a Proxy. This process is synchronous and runs on the main thread.

For complex objects like `AvatarDetail` which may contain lists of relations, materials, and effects, this deep conversion can take significant time (10ms - 100ms+), causing noticeable UI freezes during assignment.

### Solution: `shallowRef`
Use `shallowRef` instead of `ref` for these large, read-only data structures.

```typescript
import { shallowRef } from 'vue';

// BAD: Deep conversion, slow for large objects
const bigData = ref<ComplexType | null>(null);

// GOOD: Only tracks .value changes, no deep conversion
const bigData = shallowRef<ComplexType | null>(null);
```

### When to Use
- **Read-Only Display Data**: Data fetched from the API that is primarily for display and not modified field-by-field in the frontend.
- **Large Lists/Trees**: Game state, logs, inventory lists, relation graphs.

### Important Trade-offs
With `shallowRef`, **deep mutations do NOT trigger updates**.

```typescript
const data = shallowRef({ count: 1, nested: { name: 'foo' } });

// ❌ This will NOT update the UI
data.value.count++;
data.value.nested.name = 'bar';

// ✅ This WILL update the UI (replace the entire object)
data.value = { ...data.value, count: data.value.count + 1 };
// OR assignment from API response
data.value = apiResponse;
```

### Project Usage Example
See `web/src/stores/ui.ts`:
```typescript
// Used for the Info Panel detail data which can be very large
const detailData = shallowRef<AvatarDetail | RegionDetail | SectDetail | null>(null);
```

---

## 2. Component Rendering

### Virtual Scrolling
For lists that can grow indefinitely (e.g., event logs, entity lists), avoid `v-for` rendering all items. Use virtual scrolling (rendering only visible items) to keep the DOM light.

### Memoization
Use `computed` for expensive derived state rather than methods or inline expressions in templates.

## 3. Reactivity Debugging
If UI operations feel sluggish:
1. Check the "Scripting" time in Chrome DevTools Performance tab.
2. If high, look for large object assignments to `ref` or `reactive`.
3. Switch to `shallowRef` if deep reactivity is not strictly required.
