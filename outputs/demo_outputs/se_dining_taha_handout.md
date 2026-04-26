% Calibration handout — taha
% Design and develop a web app for campus dining information

**Annotator:** taha

**Brief:** Build a web application that helps students find and navigate campus dining options. The app should surface real-time or scheduled information about dining halls, menus, hours, and wait times. Students should be able to filter, search, and plan their meals. Deliver a working prototype with at least 3 core features, a brief design document explaining your architecture decisions, and a short demo.

**Rate each plan:** Feasibility 1-5 (1=not viable, 5=clearly doable) | Scope fit 1-5 (1=wrong size, 5=perfectly scoped for 14 days) | One sentence.

\bigskip

**Plan 1:** React (component-based, large ecosystem, quick prototyping) → Node.js/Express with third-party dining/campus API integration (e.g., HotSpot, Tapingo)

The project builds a React-based web application that aggregates real-time dining hall data from third-party campus APIs (via a Node.js/Express backend) to let students search, filter, and compare dining options by location, hours, and wait times. The core feature is a dynamic dashboard that updates wait-time estimates and menu availability throughout the day, allowing students to plan meal timing and choose between dining halls. The two scenarios compare a student planning ahead using historical menu data versus one making a same-day decision based on current wait times and live inventory.

Feasibility: 3 / 5 \quad Scope fit: 3 / 5

Notes: Real-time data would require building out those campus APIs as well, or finding previous projects that worked on this idea and connecting with those developers. Difficult for a 14 day project.

\medskip

**Plan 2:** React (component-based, large ecosystem, quick prototyping) → Node.js/Express server with scraped dining hall data (HTML parsing or Playwright)

The student is building a React web app that pulls dining hall information (menus, hours, wait times) from campus sources using a Node.js backend that scrapes and updates the data regularly. The app's core feature is a filterable search interface where students can view available dining locations, current operating status, and meal options in real time. The two scenarios being compared would likely be comparing the user experience of browsing by location versus browsing by meal type, or contrasting peak dining times against off-peak availability.

Feasibility: 5 / 5 \quad Scope fit: 4 / 5

Notes: Achievable but somewhat easier to implement plan. Would also teach the students the basics of CRUD apps. React is also more popular in the industry right now.

\medskip

**Plan 3:** Vue (lighter learning curve, good for rapid development) → Serverless backend (Firebase/Supabase) with pre-loaded or real-time dining data

This project uses a Vue.js frontend with a serverless Firebase backend to build a campus dining finder app where students can search dining halls, filter by menu items or hours, and see current wait times. The core feature is a real-time data sync system that updates wait times and menu availability as students check in, creating a live picture of which dining spots are busy. The two scenarios are distinguished by whether wait times are manually updated by dining staff (scheduled data mode) or pulled from anonymous student check-ins (crowdsourced real-time mode).

Feasibility: 5 / 5 \quad Scope fit: 5 / 5

Notes: Cool idea. The real-time data sync can be implemented in these 14 days and is a stand-out feature.

\medskip

**Plan 4:** Vue (lighter learning curve, good for rapid development) → Simple Node.js/Express server with mocked/static dining data (fastest, no external dependencies)

This project builds a web application using Vue.js on the front end and Node.js/Express on the back end to display campus dining hall information—menus, hours, and wait times—that students can search and filter by location or meal type. The core mechanism is a simple client-server architecture where the server serves pre-loaded dining data and the front end handles interactive filtering and meal planning, allowing students to compare options across halls at a glance. The two scenarios are distinguished by whether the student is browsing all available dining options at once or planning a specific meal at a particular time by filtering down to open halls and relevant menus.

Feasibility: \_\_\_ / 5 \quad Scope fit: \_\_\_ / 5

Notes: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

\medskip

**Plan 5:** Plain HTML/CSS/JS (minimal dependencies, simpler deployment) → Public dining API if available (most reliable, but may not exist for target campus)

This project builds a web app using vanilla HTML, CSS, and JavaScript that aggregates campus dining information and displays it with search and filter capabilities for students planning meals. The core mechanism is a client-side data layer that either pulls from a public dining API or falls back to manually maintained JSON files, allowing the app to function regardless of whether the campus provides an official data source. The two scenarios differ in data freshness and maintenance burden: the API scenario delivers real-time information but depends on external infrastructure, while the manual data scenario requires periodic updates but gives full control over what students see.

Feasibility: 3 / 5 \quad Scope fit: 3 / 5

Notes: Too minimal, students wouldn't pick up skills for app development frameworks. Also the APIs would likely not be available.

\medskip

**Plan 6:** Plain HTML/CSS/JS (minimal dependencies, simpler deployment) → Mock/hardcoded dataset (full control, no external dependencies, faster development)

This project builds a web application using vanilla HTML, CSS, and JavaScript that aggregates campus dining information from a hardcoded dataset, allowing students to search and filter dining halls by location, menu items, and operating hours. The core feature is a dynamic filtering system where students can view real-time wait times and meal plans across multiple dining locations, with the two scenarios distinguished by whether a student searches by specific dietary preferences (vegetarian options available now) versus browsing all open dining halls at their current time of day.

Feasibility: 5 / 5 \quad Scope fit: 2 / 5

Notes: Too simple and relying on hardcoded data. Not enough for a 14 day project.

\medskip
