# Week 1 Checklist: Mobile UX Foundation

**Goal**: Get app running on your phone with bottom navigation  
**Time commitment**: 15–20 hours over 7 days  
**Start date**: January 13, 2026

---

## 📋 Pre-Week Setup (Do this today if possible)

- [ ] Review `MOBILE_UI_SPEC.md` (understand the design)
- [ ] Review `IMPLEMENTATION_ROADMAP.md` (understand timeline)
- [ ] Test app on your phone (current state) using `npm run dev`
  - Note: What's annoying about current UI?
  - Does 3-column layout work on phone? (Answer: No)
- [ ] Install phone testing tools:
  - [ ] Chrome DevTools "Device Toolbar" (F12 → toggle device toolbar)
  - [ ] Optional: BrowserStack account for real device testing

---

## Daily Breakdown

### **Day 1: Design & Plan** (2 hours)
**Goal**: Understand exact mobile layout**

Tasks:
- [ ] Sketch mobile layout on paper or Figma:
  - Navigation bar at bottom with 4 icons
  - Check-in card (full width)
  - Meals card (full width)
  - Workouts card (full width)
  - History card (full width)
- [ ] List components to create/modify:
  - `BottomNav.tsx` (new component)
  - Update `App.tsx` (add tab state, bottom nav)
  - Update `CheckInCard`, `MealsCard`, `WorkoutsCard` (responsive styling)
  - `HistoryCard.tsx` (new component for past check-ins)
- [ ] Identify Tailwind utilities needed:
  - Responsive grid: `grid-cols-1`, `md:grid-cols-3`
  - Fixed bottom nav: `fixed bottom-0 h-16 w-full`
  - Full-width containers: `w-full p-4`
  - Touch targets: Min 44–48px height

**Deliverable**: Design sketch + component list

---

### **Days 2–3: Bottom Navigation Component** (4 hours)
**Goal**: Implement tab-based navigation**

Tasks:
- [ ] Create `gymbro-web/src/components/BottomNav.tsx`:
  ```tsx
  type Props = {
    activeTab: 'checkin' | 'meals' | 'workouts' | 'history'
    onTabChange: (tab: typeof activeTab) => void
  }
  
  export function BottomNav({ activeTab, onTabChange }: Props) {
    return (
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t h-16 flex justify-around">
        <TabButton icon="📊" label="Check-in" />
        <TabButton icon="🍽️" label="Meals" />
        <TabButton icon="💪" label="Workouts" />
        <TabButton icon="📅" label="History" />
      </nav>
    )
  }
  ```

- [ ] Update `gymbro-web/src/App.tsx`:
  ```tsx
  const [activeTab, setActiveTab] = useState<'checkin' | 'meals' | 'workouts' | 'history'>('checkin')
  
  return (
    <div className="pb-20"> {/* pb-20 = 80px for bottom nav */}
      {activeTab === 'checkin' && <CheckInCard />}
      {activeTab === 'meals' && <MealsCard />}
      {activeTab === 'workouts' && <WorkoutsCard />}
      {activeTab === 'history' && <HistoryCard />}
      
      <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  )
  ```

- [ ] Test locally: `npm run dev`
  - Navigate between tabs (should work)
  - Check layout on phone (use DevTools Device Toolbar)

**Deliverable**: Bottom navigation working, tabs switch content

---

### **Days 3–4: Responsive Layout** (3 hours)
**Goal**: Mobile-first CSS**

Tasks:
- [ ] Update card styling in `App.tsx`:
  ```tsx
  // Old: max-w-7xl mx-auto px-4
  // New: px-4 md:max-w-7xl md:mx-auto (mobile-first)
  
  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 px-4">
    {/* cards */}
  </div>
  ```

- [ ] Increase touch targets:
  - Buttons: `py-3` (12px padding top/bottom) instead of `py-2`
  - Inputs: `p-3` (12px padding) instead of default
  - Min height: 44px for all interactive elements

- [ ] Reduce padding on mobile:
  - Cards: `p-4` (mobile), `p-6 md:p-8` (tablet+)
  - Spacing: `gap-3` (mobile), `gap-4 md:gap-6` (tablet+)

- [ ] Font sizes:
  - Heading: `text-xl md:text-2xl` (mobile first)
  - Body: `text-sm md:text-base`

- [ ] Test on phone:
  - [ ] Buttons easy to tap (no tiny targets)
  - [ ] Inputs don't get covered by keyboard
  - [ ] Text readable (not too small)
  - [ ] Cards don't overflow width

**Deliverable**: App works on phone without horizontal scrolling

---

### **Day 5: Edit/Delete Buttons** (3 hours)
**Goal**: Add edit/delete to meals & workouts**

Tasks:
- [ ] Update `MealsCard` to show edit/delete buttons:
  ```tsx
  {foodLogs.map((meal) => (
    <div key={meal.id} className="border rounded p-3 flex justify-between">
      <div>
        <p className="font-medium">{meal.description}</p>
        <p className="text-sm">{meal.calories} cal</p>
      </div>
      <div className="flex gap-2">
        <button className="text-blue-600 text-sm">Edit</button>
        <button className="text-red-600 text-sm">Delete</button>
      </div>
    </div>
  ))}
  ```

- [ ] Implement delete functionality:
  - [ ] Add confirm dialog: "Delete this meal?"
  - [ ] Remove from local state on confirm
  - [ ] Call API to delete: `DELETE /food-logs/{id}`
  - [ ] Handle errors

- [ ] Implement edit functionality:
  - [ ] Show edit form when "Edit" clicked
  - [ ] Pre-fill form with meal data
  - [ ] Call API: `PUT /food-logs/{id}` with updated data
  - [ ] Update local state on success

- [ ] Repeat for WorkoutsCard

- [ ] Test:
  - [ ] Create meal → Edit description → Verify change
  - [ ] Create meal → Delete → Confirm dialog shows
  - [ ] Offline test → Delete queued, syncs when online

**Deliverable**: Can edit and delete meals/workouts

---

### **Days 5–6: History & Date Navigation** (3 hours)
**Goal**: View/edit past check-ins**

Tasks:
- [ ] Create `HistoryCard.tsx`:
  ```tsx
  export function HistoryCard() {
    const [selectedDate, setSelectedDate] = useState(new Date())
    const [checkins, setCheckins] = useState([])
    
    useEffect(() => {
      // Load check-ins for selected date
      api.getDailyCheckIn(selectedDate.toISOString().slice(0, 10))
    }, [selectedDate])
    
    return (
      <div>
        <div className="flex justify-between items-center mb-4">
          <button onClick={() => setSelectedDate(new Date(selectedDate.getTime() - 86400000))}>←</button>
          <span>{selectedDate.toLocaleDateString()}</span>
          <button onClick={() => setSelectedDate(new Date(selectedDate.getTime() + 86400000))}>→</button>
        </div>
        
        {/* Show check-in for selected date */}
        {checkins && <CheckInCard checkin={checkins[0]} />}
      </div>
    )
  }
  ```

- [ ] Update API to support date-specific check-ins:
  - Already works: `GET /daily-checkins/today` and `GET /daily-checkins/{date}`
  - Use existing endpoint

- [ ] Test:
  - [ ] Navigate to yesterday → Show yesterday's data
  - [ ] Edit past check-in
  - [ ] Create check-in for future date

**Deliverable**: Can view/edit check-ins for any date

---

### **Days 6–7: Testing & Polish** (3 hours)
**Goal**: Ready for daily use**

Tasks:
- [ ] Test on actual phone (not just DevTools):
  - [ ] Open on iPhone/Android
  - [ ] All tabs work
  - [ ] No layout issues
  - [ ] Keyboard doesn't cover buttons
  - [ ] Works in both portrait & landscape

- [ ] Performance check:
  - [ ] Page loads <2 seconds
  - [ ] Tap response is instant
  - [ ] No lag when scrolling

- [ ] Polish:
  - [ ] Add icons to buttons (use emoji: ✏️ for edit, ✕ for delete)
  - [ ] Add loading state while submitting
  - [ ] Add success message after edit/delete
  - [ ] Better error messages

- [ ] Check console:
  - [ ] No JavaScript errors
  - [ ] No console warnings

- [ ] Lighthouse audit (DevTools → Lighthouse):
  - [ ] PWA score >80 (goal: >90)
  - [ ] Accessibility score >90
  - [ ] Performance score >80

- [ ] Commit to GitHub:
  ```bash
  git add .
  git commit -m "feat: mobile UI with bottom nav, edit/delete, date navigation"
  git push origin main
  ```

**Deliverable**: Production-ready mobile UX, can use daily

---

## 📱 Testing Strategy

### Day-to-Day
- Use app on your phone for at least 2 hours
- Log check-in, meal, workout every day
- Note any UX pain points
- Fix in next iteration

### Chrome DevTools
- F12 → Device Toolbar (or Ctrl+Shift+M)
- Test on "iPhone 13", "Pixel 5", "iPad"
- Rotate device (test landscape)
- Throttle network (3G) to test slow loading

### Real Device Testing
- Use actual phone you'll be using daily
- Landscape and portrait
- With and without network
- Different font sizes (system settings)

---

## 🐛 Known Potential Issues

### Keyboard covers button
- Solution: Add `pb-20` to inputs (push up when focused)
- Test on actual phone keyboard

### Bottom nav overlaps content
- Solution: Add `pb-20` to main content wrapper
- Verify spacing in DevTools

### Edit/Delete buttons too small
- Solution: Increase button size to 44px minimum
- Use `p-2` padding instead of `p-1`

### Slow on 3G
- Solution: Optimize images (already done)
- Use DevTools throttling to test

---

## ✅ Definition of Done (Day 7)

By end of Day 7, you should be able to:

- [ ] Open app on home screen (no browser)
- [ ] Navigate between 4 tabs (no lag)
- [ ] Log check-in in <10 seconds
- [ ] Log meal in <15 seconds
- [ ] Log workout in <15 seconds
- [ ] Edit any log you just created
- [ ] Delete any log with confirmation
- [ ] View check-ins from yesterday
- [ ] Use in portrait AND landscape
- [ ] Works offline (logs queue, sync online)
- [ ] Service worker caching works (DevTools → Application → Cache)

**If all boxes checked**: Ready for deployment! 🎉

---

## 📚 Resources

- `MOBILE_UI_SPEC.md` — Design reference
- Tailwind docs: https://tailwindcss.com/docs
- React hooks: https://react.dev/reference/react/hooks
- Chrome DevTools: https://developer.chrome.com/docs/devtools/

---

## 🚀 Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Time to log meal | <15 sec | ⏳ |
| Mobile readability | No zoom needed | ⏳ |
| Touch target size | >44px | ⏳ |
| Offline support | Logs queue | ⏳ |
| Lighthouse PWA | >90 | ⏳ |
| Personal usage | Daily for 7 days | ⏳ |

---

## Questions to Clarify BEFORE Starting

1. **Design**: Do you want exact bottom nav icons/labels, or have ideas?
   - Currently suggesting: 📊 Check-in | 🍽️ Meals | 💪 Workouts | 📅 History

2. **Edit flow**: Should editing show a modal, or replace the card?
   - Recommending: Expand/collapse (tap Edit → show form, tap Save → hide form)

3. **Date navigation**: Calendar picker or prev/next buttons?
   - Recommending: Prev/next buttons (simpler for mobile)

4. **Delete confirmation**: Modal dialog or swipe gesture?
   - Recommending: Modal (more accessible)

5. **Offline**: Should "offline mode" indicator show?
   - Recommending: Yes, small badge in header

---

## Next Steps After Week 1

✅ **Week 1 done**: Mobile UX complete, using app daily  
👉 **Week 2**: Start Vercel deployment (while continuing mobile use)  
👉 **Week 3**: Live on internet  
👉 **Week 4–6**: Google OAuth (multi-user auth)

---

**Ready? Start Day 1 design work!** 🚀

Questions? Ask before you start coding!
