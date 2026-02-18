# Mobile UI Specification

**Target**: iPhone 13 (375px width), iPad (768px+), Android phones  
**Framework**: React + Tailwind (responsive design)  
**Priority**: Touch-friendly, fast loading, offline support

---

## 📐 Breakpoints

```
Mobile: 375–480px (default)
Tablet: 481–768px
Desktop: 769px+
```

---

## 🎨 Layout Architecture

### Current (Desktop-First)
```
┌─────────────────────────────────────────┐
│              Header                      │
├─────────────────────────────────────────┤
│ Check-in │ Meals │ Workouts             │ (3-column grid)
├─────────────────────────────────────────┤
│              Footer                      │
└─────────────────────────────────────────┘
```

### New (Mobile-First)
```
┌──────────────────┐
│   Header         │
├──────────────────┤
│ CHECK-IN CARD    │  (full-width, 100vh - header - nav)
├──────────────────┤
│ MEALS CARD       │  (stacked vertically)
├──────────────────┤
│ WORKOUTS CARD    │
├──────────────────┤
│    Footer        │
├──────────────────┤
│  BOTTOM NAV      │  (fixed, 60px height)
│ ✓ | 🍽️ | 💪 | 📅 │
└──────────────────┘
```

---

## 🧩 Component Redesign

### Header (Minimal)
```
┌──────────────────────────────────┐
│ Gym Bro              User: You   │  (14px font on mobile)
└──────────────────────────────────┘
Height: 48px
```

**Changes**:
- Remove "Track your fitness journey" tagline on mobile
- Display only app name + user email
- Smaller font (14px → 12px on mobile)

---

### Bottom Navigation (NEW)

```
┌─────────────────────────────────┐
│ 📊 CHECK │ 🍽️ MEALS │ 💪 WORK │ 📅 HISTORY │
└─────────────────────────────────┘
Height: 60px
Fixed to bottom
```

**Behavior**:
- Icons + labels (12px font)
- Current page highlighted in blue
- Tapping switches active card
- Smooth transitions

**Implementation**:
```jsx
// Add state to App.tsx
const [activeTab, setActiveTab] = useState('checkin')

// Show/hide cards based on activeTab
{activeTab === 'checkin' && <CheckInCard />}
{activeTab === 'meals' && <MealsCard />}
{activeTab === 'workouts' && <WorkoutsCard />}
{activeTab === 'history' && <HistoryCard />}

// Bottom nav component
<nav className="fixed bottom-0 left-0 right-0 bg-white border-t h-16 flex">
  <NavButton icon="📊" label="Check-in" active={activeTab === 'checkin'} />
  {/* ... */}
</nav>

// Adjust main content padding
<main className="pb-20"> {/* pb-20 = 80px = 60px nav + 20px buffer */}
```

---

### Check-in Card (Mobile Version)

**Current**:
```
┌─ Check-in ─────────────────┐
│ Weight (kg)  Steps         │
│ [input]      [input]       │
│ □ Trained  □ Protein met   │
│ Notes [textarea]           │
│ [Save Button]              │
└────────────────────────────┘
```

**New (Mobile)**:
```
┌─ Today ─────────────────────┐
│ 2026-01-12                  │
├─────────────────────────────┤
│ Weight: 75.2 kg             │
│ Trained: Yes                │
│ Protein: Yes                │
│ Steps: 8,200                │
├─────────────────────────────┤
│ [Edit] [Edit History →]     │
└─────────────────────────────┘

[Then show edit form below if Edit clicked]
```

**Changes**:
- Show summary first (read-only)
- "Edit" button to expand form
- Date picker for navigation (← Today →)
- Full-width inputs
- Larger touch targets (48px+ height)

**Code**:
```jsx
// Mobile-friendly input
<input
  type="number"
  className="w-full p-3 rounded border text-lg"  // Larger padding
  placeholder="Enter weight"
/>

// Mobile-friendly button
<button className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold">
  Save Check-in
</button>
```

---

### Meals Card (Mobile Version)

**Current**:
```
┌─ Meals ──────────────────────┐
│ [Input Description] [input]  │
│ [Log Meal Button]            │
│ Recent meals:                │
│ - Chicken (500 cal) 2:30pm   │
│ - Rice (300 cal) 1:00pm      │
└──────────────────────────────┘
```

**New (Mobile)**:
```
┌─ Meals ──────────────────────┐
│ [Tap to add meal]            │
├──────────────────────────────┤
│ Recent meals:                │
│ - Chicken Breast             │
│   500 cal | 12:30pm          │
│   [Edit] [Delete ✕]          │
│ - Banana                     │
│   100 cal | 11:00am          │
│   [Edit] [Delete ✕]          │
└──────────────────────────────┘
```

**Changes**:
- Quick-add button (tap to focus form)
- Edit/Delete buttons on each item
- Larger cards (touch-friendly)
- Meal time displayed clearly
- Swipe-to-delete option (future)

**Code**:
```jsx
// Quick-add button
<button 
  onClick={() => setShowMealForm(!showMealForm)}
  className="w-full py-4 bg-green-50 border-2 border-green-400 rounded-lg text-green-700 font-semibold"
>
  + Add Meal
</button>

// Meal item with edit/delete
<div className="bg-gray-50 p-4 rounded-lg flex justify-between items-start">
  <div className="flex-1">
    <p className="font-semibold text-gray-900">{meal.description}</p>
    <p className="text-sm text-gray-600">{meal.calories} cal</p>
    <p className="text-xs text-gray-500">{formatTime(meal.logged_at)}</p>
  </div>
  <div className="flex gap-2">
    <button className="text-blue-600 text-sm">Edit</button>
    <button className="text-red-600 text-sm">Delete</button>
  </div>
</div>
```

---

### Workouts Card (Similar to Meals)

```
┌─ Workouts ──────────────────┐
│ + Add Workout               │
├──────────────────────────────┤
│ Upper Body                   │
│ 30 min | 2:30pm              │
│ [Edit] [Delete ✕]            │
│ Running                      │
│ 5k | 1:00pm                  │
│ [Edit] [Delete ✕]            │
└──────────────────────────────┘
```

---

### History Card (NEW)

```
┌─ History ───────────────────┐
│ [Date Picker] ← Jan 12 →    │
├──────────────────────────────┤
│ Check-in: 75.2 kg           │
│ Meals: 2,150 calories       │
│ Workouts: 2 sessions        │
│ [Show details ↓]            │
└──────────────────────────────┘
```

**Features**:
- Date picker (calendar or prev/next)
- Show daily summary
- Tap to see detailed breakdown
- Edit past entries

---

## 📏 Typography & Spacing

### Mobile Typography
```
Header:        20px (was 30px)
Card titles:   16px (was 18px)
Body text:     14px (was 14px)
Input labels:  12px
Buttons:       14px (was 12px)

Line height: 1.5x (increases readability on small screens)
```

### Spacing
```
Screen padding:     16px (mobile), 24px (tablet)
Card padding:       16px (mobile), 20px (tablet)
Button height:      48px (touch-friendly minimum)
Input height:       44px+
Gap between items:  12px (mobile), 16px (tablet)
```

---

## 🎨 Responsive CSS (Tailwind)

```jsx
// Example: Responsive grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

// Example: Responsive text
<h1 className="text-xl md:text-2xl lg:text-3xl">

// Example: Responsive padding
<div className="p-4 md:p-6 lg:p-8">

// Example: Mobile-first flex
<div className="flex flex-col md:flex-row">
```

---

## 🔄 Key UX Patterns

### 1. Loading States
- Show skeleton loader (not "Loading..." text)
- Placeholder cards with pulse animation
- Prevent button clicks until loaded

### 2. Error Handling
- Red error banner at top
- Clear error message
- Retry button
- If offline: "Changes will sync when online" message

### 3. Form Submission
- Button shows "Saving..." state
- Disable all inputs while saving
- Success: Brief success message, clear form
- Failure: Show error, keep form data

### 4. Offline Support
- Service worker caches GET requests
- Queue POST/PUT if offline
- "📶 Offline mode" indicator
- "Syncing..." message when connection returns

### 5. Delete Confirmation
```
User taps [Delete ✕]
  ↓
Modal appears: "Delete this meal?"
"Cancel" | "Delete"
  ↓
If confirmed, remove from list
```

---

## 🧪 Mobile Testing Checklist

- [ ] Test on actual iPhone (landscape + portrait)
- [ ] Test on actual Android (landscape + portrait)
- [ ] Test on iPad (layout looks good)
- [ ] Test keyboard interaction (tab navigation)
- [ ] Test offline (use DevTools offline mode)
- [ ] Test slow 3G (Chrome DevTools throttling)
- [ ] Check Lighthouse PWA score (>90)
- [ ] Test on-screen keyboard doesn't hide buttons
- [ ] Test form inputs work (auto-focus, auto-capitalize)
- [ ] Test links/buttons don't have hover states blocking clicks

---

## 🚀 Implementation Priority

### Week 1
1. [ ] Add bottom navigation (tab switching)
2. [ ] Responsive grid (mobile-first)
3. [ ] Larger buttons/inputs
4. [ ] Basic mobile styling (padding, font sizes)

### Week 2
1. [ ] Edit/Delete buttons + modals
2. [ ] Date picker for check-in history
3. [ ] Quick-add buttons for meals/workouts
4. [ ] History card

### Week 3
1. [ ] Service worker enhancements (offline)
2. [ ] Loading skeletons
3. [ ] Error handling polish
4. [ ] Testing on actual devices

---

## 📱 Tools & Resources

- **Chrome DevTools**: Responsive design mode, DevTools → Device toolbar
- **BrowserStack**: Test on real devices (free trial)
- **Tailwind**: Mobile-first utilities (use `sm:`, `md:`, `lg:` prefixes)
- **Lighthouse**: Built into Chrome DevTools (Audits tab)
- **PWA Assessment**: https://web.dev/measure/

---

## 🎯 Success Metrics

| Metric | Target |
|--------|--------|
| Lighthouse PWA score | >90 |
| Mobile Lighthouse score | >85 |
| Page load time | <2s on 4G |
| Time to Interactive | <3s |
| Cumulative Layout Shift | <0.1 |
| First Contentful Paint | <1.5s |
| Works offline | Yes (via service worker) |
| Touch target size | >48x48px |

---

## Next Steps

1. Review this spec
2. Start Week 1 (bottom nav + responsive grid)
3. Test on your phone daily
4. Iterate based on real usage feedback
