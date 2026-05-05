# Dataset Requirements

This project can describe another country if the input data follows the same
basic contract. The goal is not perfect historical reconstruction on day one.
The goal is to provide enough structure for:

- ruler age and elite age timelines
- political age and renewal metrics
- event timelines and elite-initiated events
- faction analysis, if the faction layer exists
- correlation summaries and narrative takeaways

## 1. Required core tables

These four tables are the minimum needed for a usable country profile.

### `persons.csv`

Required columns:

- `person_id`
- `name`
- `birth_date`

Recommended columns:

- `death_date`
- `country_label`
- `notes`

Rules:

- `person_id` must be unique and stable.
- `birth_date` must be in ISO format: `YYYY-MM-DD`.
- Use empty values for unknown dates, not fake dates.

### `positions.csv`

Required columns:

- `person_id`
- `position`
- `institution`
- `start_date`
- `end_date`
- `is_ruler`
- `is_core_elite`
- `tier`
- `influence_weight`

Recommended columns:

- `notes`

Rules:

- `person_id` must match `persons.csv`.
- `start_date` and `end_date` must be ISO dates.
- `start_date` must be less than or equal to `end_date` when both are known.
- `is_ruler` and `is_core_elite` must be boolean-like values.
- `influence_weight` must be numeric.

### `political_entries.csv`

Required columns:

- `person_id`
- `political_entry_date`
- `elite_entry_date`
- `ruling_circle_entry_date`

Recommended columns:

- `notes`

Rules:

- These dates can be approximate, but the uncertainty should be explicit.
- `person_id` must match `persons.csv`.
- Dates must be ISO format when known.

### `events.csv`

Required columns:

- `event_id`
- `date`
- `event_name`
- `event_type`
- `severity`
- `elite_initiated`
- `confidence`

Recommended columns:

- `decision_domain`
- `initiator_group`
- `initiator_person_id`
- `initiator_faction_id`
- `event_scope`
- `notes`

Rules:

- `event_id` must be unique and stable.
- `date` must be ISO format.
- `severity` should be on a bounded ordinal scale, ideally `1..5`.
- `elite_initiated` must be boolean-like.
- `confidence` must be between `0` and `1`.
- If `decision_domain` or `initiator_group` are missing, the event layer is still usable,
  but the dense cross-tab views will be weaker.

## 2. Optional faction layer

Add these tables when the country has a meaningful faction/network layer.
This is optional, but it unlocks much stronger analysis.

### `factions.csv`

Required columns:

- `faction_id`
- `faction_name`
- `faction_type`

Recommended columns:

- `start_year` or `start_date`
- `end_year` or `end_date`
- `description`
- `notes`

Rules:

- `faction_id` must be unique and stable.
- `faction_type` should be a controlled vocabulary.
- If the faction is period-specific, its active range must be explicit.

### `person_factions.csv`

Required columns:

- `person_id`
- `faction_id`
- `confidence`

Recommended columns:

- `start_year` or `start_date`
- `end_year` or `end_date`
- `relation_type`
- `notes`

Rules:

- One person may belong to multiple factions.
- `confidence` must be between `0` and `1`.
- Membership should be interval-based when possible.

### `faction_relations.csv`

Required columns:

- `source_faction_id`
- `target_faction_id`
- `relation_type`

Recommended columns:

- `start_year` or `start_date`
- `end_year` or `end_date`
- `intensity`
- `confidence`
- `notes`

### `elite_edges.csv`

Required columns:

- `source_person_id`
- `target_person_id`
- `edge_type`

Recommended columns:

- `start_year` or `start_date`
- `end_year` or `end_date`
- `weight`
- `confidence`
- `notes`

## 3. Recommended period metadata

This file is not required for the core pipeline, but it improves summaries and
period plots.

### `periods.csv`

Recommended columns:

- `period_id`
- `label`
- `start_year`
- `end_year`
- `slug`

Optional columns:

- `label_ru`
- `label_en`
- `notes`

Rules:

- Periods should not overlap unless that is a deliberate modeling choice.
- `period_id` should be stable and machine-readable.

## 4. Quality rules

The following rules matter more than perfect completeness:

- Every identifier must be stable across reloads.
- Unknown values should be empty, not invented.
- Dates must be ISO-8601.
- `confidence` must stay in `[0, 1]`.
- `influence_weight` should have one consistent meaning inside a dataset.
- `is_ruler` and `is_core_elite` should be explicit.
- The core elite definition must be documented.

## 5. What the project can do with this contract

With the core tables, the project can build:

- yearly ruler age snapshots
- yearly core elite age snapshots
- political age and renewal metrics
- event summaries
- correlations and narrative takeaways

With the optional faction layer, the project can also build:

- faction power share over time
- faction type power share
- faction fragmentation
- event context by faction
- cross-tabs between initiators, faction types, and decision domains

## 6. Minimum recommended package for a new country

If the goal is to get useful charts fast, start with:

1. `persons.csv`
2. `positions.csv`
3. `political_entries.csv`
4. `events.csv`
5. `periods.csv`

Add the faction tables only after the basic timeline is working.

