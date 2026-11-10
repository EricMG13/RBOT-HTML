# Plan: deploy the visuals catalogue (owner, 2026-11-10: "Implement them all")

Source of truth: `docs/visualisations/catalogue.csv` (91 views). 46 are `Table/content only`
and already render as Reference tables; nothing to build. The other 45 are below.

Today: the library draws a chart only from a `Chart data: …` table a handoff declares, and the
launcher asks only CP-1 for four of them (`CHART_TABLES` S.1–S.4 in `cpos_launch.py`). On the TDG
runs that is four Financial foundation charts.

## Rules every package keeps

- A view draws only from values a handoff (or the run's own records) states. No figure is
  derived, interpolated or filled. A missing input shows as "Not established for this run", never
  zero. Units, periods, basis and source references travel with each point.
- Each new data contract is a fixed-shape Markdown table the launcher asks the owning module
  for, validated in the loop like `chart_issues` (a bad table goes back for repair).
- PR 20's owner ruling stands: values over time are columns per series with periods on the x
  axis. Catalogue rows that say "Line" are drawn that way.
- Every view has an accessible table form and works over `file://` with no network.
- One PR per package, under 800 changed lines, through the project's gates and the owner's review
  regime (implementer, task review, whole-branch review).

## Packages, in order

| # | Package | Views | What changes |
|---|---|---|---|
| 1 | Financial foundation and liquidity figures | CP-1-V05, CP-2D-V01, CP-3C-V01 | Launcher asks for S.5 revenue/EBITDA history, a liquidity bridge and a refinancing-need table; library draws them (columns; one waterfall primitive) |
| 2 | Credit-structure figures | CP-1-V06, CP-1-V07, CP-4-V01, CP-2H-V01, CP-6-V03 | Debt stack, EBITDA adjustment bridge (waterfall), covenant and rating-trigger headroom (bullet primitive), portfolio limit bars |
| 3 | Comparison figures | CP-1B-V01, CP-1B-V02, CP-1C-V01, CP-1C-V02, CP-3D-V01 | Prior/current columns and dumbbell, peer range strip, yield-against-maturity (numeric-x) |
| 4 | Recovery figures | CP-4C-V01 to V04 | Recovery by class; value-allocation waterfalls per supplied scenario |
| 5 | Calendar lanes | CP-0-V03, CP-1A-V01, CP-1B-V04, CP-DR-V03, CP-2D-V03, CP-2E-V03, CP-2H-V03, CP-3-V03, CP-3C-V04, CP-4-V05, CP-6-V04, DELIVERY-V02 | One dated-event contract (event date and precision, publication date, status, source line); the Calendar tab becomes lanes per module with an event table |
| 6 | Maps | CP-0-V02, CP-OS-V01, CP-1A-V02, CP-1A-V04, CP-2-V02, CP-2A-V03, CP-4-V03, CP-4-V04, CP-5-V02 | Status and dependency maps from run records; relationship and transmission maps from fixed node/edge tables the modules declare |
| 7 | Indexes and manifests | CP-MODEL-V02, DELIVERY-V03, CP-OS-V03 | Chart index with table/source drill-down; figure/table/source manifest on Reports; run/revision/file selectors |

Packages 1–4 need no new UI structure; 5–7 add one component each (lane, map, index).

## What can and cannot be proven offline

Every package is built and tested on fixtures labelled synthetic, plus the retained TDG handoffs
where they already hold the data (Financial foundation, Business & governance, Fundamental
credit). Most new contracts have no retained handoff that answers them. Showing them populated
with TDG values needs a new paid live run after the launcher changes, a separate action under
the inbox ruling's cap. Modules that are blocked for missing sources (peers, legal documents,
rating reports, market data) will draw "Not established" until those sources are supplied.

CP-4-V03 and CP-4-V04 are marked "Broader handoff needed" in the catalogue: their maps need the
CP-4B and CP-4D handoffs, which no current pathway launches. Package 6 builds the map; the data
contract is added to those modules' instructions but stays unproven until a pathway runs them.
