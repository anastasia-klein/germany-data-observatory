# GDO Play Axis

`GDOPlayAxis.pbiviz` is a patched copy of Play Axis for the Party Landscape page.

The patch:

- shows the playback controls in a compact visual;
- uses a seven-second interval so the district map can finish rendering;
- disables automatic start and looping;
- removes the repeated-selection loop that caused `OperationCanceled` errors.

## Import in Power BI Desktop

1. Open **More visuals → Import a visual from a file**.
2. Select `powerbi/custom-visuals/GDOPlayAxis.pbiviz`.
3. Add **GDO Play Axis** to the empty space between the election selector and Current view.
4. Add `party_landscape_play_year_selector[election_year]` to its **Field** well.
5. Save the report project.

The ordinary election-year dropdown remains available and is used whenever the play visual has no active year selection.
