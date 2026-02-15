# BreathCheck

BreathCheck is a local-first desktop app for anxiety self-help. It combines a guided CBT-style learning flow, practical coping tools, and progress tracking in a PyQt5 application.

## Current App Structure

### Navigation (sidebar)
- Learn
- Tools
- Progress
- Support
- Settings

### Access flow
- Login with master password (create on first run).
- On first successful login, onboarding is shown.
- Onboarding requires acknowledgement before entering the app.

## Learn

BreathCheck currently presents **6 sequential modules**:
1. Understanding Anxiety
2. Relaxation
3. Our Thoughts
4. Changing Thoughts
5. Coping with Worry
6. Lifestyle Factors

Rules:
- Module 1 is available first.
- Next module unlocks only after previous module is complete.
- Locked modules remain visible; actions are disabled.
- Each module card has `Overview`, `Sources`, and `Open`/`Resume`.

### Learn Module Status
Modules 1-6 are implemented as **10-step wizards** with:
- Persistent save per step
- Resume from `last_step_index`
- Overview page showing saved inputs
- Left media panel with image/audio placeholders + quote
- Step progress and validation
- Guide/Examples notes under user inputs
- Step 10 completion parity (summary cards + final check-out slider(s) + optional one-sentence commitment)

Module 1 covers:
- Orientation/baseline and anxiety pattern mapping
- Fight-or-flight body signals and most-bothersome symptoms
- Worry-cycle and trigger pattern tracking
- Avoidance/safety behavior costs and support planning
- Personal summary plan
- Completion step with summary cards, final anxiety/tension check-out, and optional commitment

Module 6 covers:
- Sleep snapshot and sleep action planning
- Food regularity and weekly nutrition upgrade
- Caffeine trigger boundary planning
- Movement baseline and realistic minimum plan
- Mindfulness plan and schedule
- Setback If-Then maintenance plan
- Completion summary cards, anxiety-now check-out, maintain-confidence check-out, and commitment

## Tools

Tools page includes only:
- **BreathCheck** breathing session tool
  - Pace selector
  - Duration selector
  - Timer + phase guidance
  - Start/Pause
  - Usage logging
- **Thought Log**
  - Situation
  - Automatic thought
  - Emotion intensity (0-10)
  - Alternative/balanced thought
  - Re-rate intensity
  - Save to database
  - AI feedback (streamed when available, fallback text otherwise)

History section includes:
- Breathing usage history
- Thought log history (expandable details, includes stored AI feedback)

## Progress

Progress page includes:
- Program completion summary
- Weekly engagement summary
- Streak
- Tool usage summary
- Milestones grid

Milestones are service-driven and include:
- Module completion milestones (1-6)
- Tool and engagement milestones
- Program completion milestone

## Support

Support page includes compact cards for:
- Emergency support steps
- Crisis hotline contacts (user-managed)
- Counseling resources (user-managed)
- University mental health resources (user-managed)

Users can:
- Add contacts/resources
- View saved entries
- Delete saved entries

## Settings

Settings currently includes:
- Change master password
- Reset progress
- Delete account
- Delete all data
- Comfort mode toggle
- Font size
- Reminder preference
- Export data (JSON/CSV from UI)

Notes:
- API key management UI is not exposed in settings.
- Local encryption status is shown.

## Privacy and Security

- Data is stored locally (SQLite).
- Sensitive text fields are encrypted before persistence.
- Encryption keys and master password are managed through keyring-based security utilities.
- App messaging emphasizes local data storage and confidentiality.

## Window and UI Behavior

- Main window uses screen available geometry on startup.
- Window resizing is disabled (fixed to available screen size).
- Dropdown fields (combo boxes) open with a single click app-wide.
- UI is optimized for no animation transitions and responsive interactions.

## Tech Stack

- Python 3.11+
- PyQt5
- SQLAlchemy (SQLite)
- python-dotenv
- keyring
- cryptography
- openpyxl

## Run

```bash
python -m anxiety_app.main
```

## Tests

```bash
python -m pytest src/anxiety_app/tests
```

or with local venv explicitly:

```bash
/home/jxmppng/Documents/Projects/BC_TEST/.venv/bin/python -m pytest src/anxiety_app/tests
```

## Additional Documentation

- Developer-focused architecture and implementation notes:
  - `CODEBASE_EXPLAINER.txt`
- User-facing app guide:
  - `APP_USER_GUIDE.txt`
- Modules 1-6 authored content reference:
  - `modules_1_to_6_content.txt`
- Milestone text reference:
  - `milestones.txt`
