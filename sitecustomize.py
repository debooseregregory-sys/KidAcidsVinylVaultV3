"""VinylVault runtime customization.

The legacy ReleaseDetailPage still owns the old multi-row MP3 editor card.
The visible Vinyl release flow now uses the compact CD-style track card while
keeping the existing editor, MP3 search, preferred-link and unlink actions.
"""

try:
    from gui import release_detail_page
    from gui.compact_track_card import CompactTrackCard
    release_detail_page.TrackCard = CompactTrackCard
except Exception:
    # Never prevent VinylVault from starting if optional runtime patching fails.
    pass
