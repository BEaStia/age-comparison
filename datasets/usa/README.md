# USA elite age / factions dataset, 1945-2026 snapshot

Created: 2026-05-05
Country: United States of America
Coverage: mostly federal national-level elites from 1945 to 2026-05-05.

## Modeling note on “Deep State” and “globalists”

This dataset does **not** claim that a single hidden command structure exists.
Instead it models observable proxies:

- `fac_natsec_establishment`: "Deep State / national security establishment (analytical proxy)". This captures continuity networks around NSC, CIA, FBI, Defense and State.
- `fac_globalists`: "Globalists / foreign-policy internationalists (analytical label)". This captures internationalist/multilateral policy orientation and visible elite networks.
- `fac_cfr_trilateral`: documented public think-tank/private policy network proxy where sources support it.

Use `confidence`, `notes`, and `source_url` before making strong claims. Low-confidence faction assignments should be treated as hypotheses, not facts.

## Core elite definition

A person is `is_core_elite=true` in `positions.csv` if they held one of the following national-level roles or equivalent influence positions:

1. President / Vice President / congressional chamber leadership.
2. Secretary of State, Secretary of Defense, National Security Advisor.
3. Director of Central Intelligence/CIA or FBI Director.
4. A non-state elite network node with documented policy influence, included at lower tier/weight.

`influence_weight` is a relative, within-dataset weight: President = 1.0; very high policy-control offices ~0.85-0.9; congressional/agency/network nodes lower.

## Approximation rules

- Month-only dates are represented by the first day of the month and noted in `notes`.
- Active current offices have empty `end_date`.
- Faction membership is interval-based only when clear; otherwise intervals may be empty and confidence should guide analysis.

## Files

- persons.csv
- positions.csv
- political_entries.csv
- events.csv
- factions.csv
- person_factions.csv
- faction_relations.csv
- elite_edges.csv
- periods.csv

## Recommended first checks

1. Validate person IDs across all files.
2. Plot yearly ruler age using `positions.is_ruler=true`.
3. Plot yearly core elite age using `positions.is_core_elite=true` and `influence_weight`.
4. Treat faction analysis as exploratory until every faction assignment has been reviewed.


## Expansion note — 2026-05-05

Expanded the personnel layer for the USA profile. The dataset now includes presidents and post-1945 vice presidents, major Secretaries of State, CIA/DCI and FBI directors, Federal Reserve chairs, Chief Justices and selected Supreme Court justices, House Speakers, Senate leaders, and selected defense/finance/donor/network figures.

Important modeling note: labels such as `fac_natsec_establishment`, `fac_globalists`, and `fac_cfr_trilateral` are analytical proxies, not claims that a single secret organization exists. Use `confidence`, `relation_type`, and `notes` to filter stricter or looser interpretations.

Row counts after expansion:

- persons.csv: 121
- positions.csv: 136
- political_entries.csv: 121
- factions.csv: 13
- person_factions.csv: 234
- elite_edges.csv: 36


## Event layer expansion

This version expands `events.csv` to 160 events covering founding-era, constitutional, electoral, foreign-policy, security-state, financial, judicial, civil-rights, and 21st-century political events. The `Deep State` and `globalist` faction references remain analytical proxies, not claims of a single hidden command structure. Use `confidence`, `initiator_faction_id`, `decision_domain`, and `notes` for filtering.
