% Calibration handout — taha
% Build visualizations to explore user journeys and behaviors on an app

**Annotator:** taha

**Brief:** Given a dataset of user events (clicks, page views, session starts/ends, conversions) from a mobile or web app, design and implement a visualization suite that reveals how users move through the product. The deliverable should help a product team answer: where do users drop off, which paths lead to conversion, and how do power users differ from casual ones. Deliver at least 2 distinct visualization types and a 1-page written interpretation.

**Rate each plan:** Feasibility 1-5 (1=not viable, 5=clearly doable) | Scope fit 1-5 (1=wrong size, 5=perfectly scoped for 10 days) | One sentence.

\bigskip

**Plan 1:** Use publicly available real dataset (e.g., Kaggle mobile app events, Google Analytics sample data) → Tableau or PowerBI for rapid prototyping with built-in funnel and flow templates

The student will build a Tableau-based visualization suite using public mobile app event data to map user journeys from session start through conversion, featuring a funnel chart to identify drop-off points and a Sankey diagram to show which navigation paths lead to purchase. The core mechanism focuses on segmenting users by engagement level (power users vs. casual visitors) to reveal whether high-value users follow different routes through the app. The two scenarios compare the conversion funnel and path patterns between the two user segments, highlighting where casual users abandon the journey versus where power users progress further.

Feasibility: 5 / 5 \quad Scope fit: 4 / 5

Notes: Using Sankey diagrams is a smart choice for user journeys. However, for a 10 day project, interactivity might have been a highlight that could make it stand out,

\medskip

**Plan 2:** Use publicly available real dataset (e.g., Kaggle mobile app events, Google Analytics sample data) → D3.js or Observable for custom, publication-ready interactive visualizations

The student will build an interactive visualization suite using D3.js on real app event data to model user navigation as a flow through the product, with one visualization showing dropout points across the conversion funnel and another revealing the most common multi-step paths that power users take compared to one-time visitors. The core mechanism is tracking session sequences and aggregating them to expose both where users leave the app and which route combinations correlate with repeated engagement. The two scenarios are distinguished by segmenting users into power-user and casual-user cohorts, then comparing their funnel completion rates and path preferences side by side.

Feasibility: 5 / 5 \quad Scope fit: 5 / 5

Notes: Fittingg idea with excellent custom, interactive visualizations which would be a useful skill for the students.

\medskip

**Plan 3:** Generate realistic synthetic event-log data from scratch with defined user personas and journey patterns → Sankey diagram (paths/flows) + heatmap (temporal drop-off by stage)

This project uses event-log simulation and flow visualization to explore user behavior in a mobile app environment. The core approach generates synthetic user journeys across distinct personas (casual vs. power users), then reveals dropout patterns through a Sankey diagram showing path frequencies and a temporal heatmap tracking where users abandon the funnel at each stage. The two scenarios are distinguished by user type: casual users follow shorter, more variable paths with higher early-stage drop-off, while power users exhibit deeper engagement and repeat-conversion sequences.

Feasibility: 4 / 5 \quad Scope fit: 3 / 5

Notes: Would need to spend time building up to some realistic synthetic data and would also have to find a way to prove its relaibility.

\medskip

**Plan 4:** Generate realistic synthetic event-log data from scratch with defined user personas and journey patterns → Funnel chart (conversion by stage) + sequence diagram (power-user vs casual paths)

The project applies event-log visualization to mobile app analytics, generating synthetic user session data with distinct personas to model conversion behavior. The core mechanism compares two user cohorts—power users and casual users—by overlaying their distinct traversal paths through the app alongside a funnel chart that shows where each group drops off at key conversion stages. The two scenarios are distinguished by user engagement level: power users follow high-frequency, multi-step paths with strong conversion rates, while casual users take shorter paths with higher abandonment at early funnels.

Feasibility: 4 / 5 \quad Scope fit: 3 / 5

Notes: Same as above for the synthetic data but also there might be more groups than just the two of power user and casual paths so should spend more time researching those.


\medskip
