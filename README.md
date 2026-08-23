# Kid Acid's VinylVault V3

**A personal music collection and playback vault for Vinyl, CD, MP3 and Livesets.**

VinylVault V3 is a desktop music application built around a local collection database, with dedicated library, editing, showcase and playback views.

## What is included?

### Vinyl
- Browse and search the vinyl collection.
- Open a release to view its tracks and details.
- Use the Showcase for a visual playback experience.
- Link available MP3 files to tracks.

### CD
- Browse the CD collection separately from Vinyl.
- Open CD releases and view their tracks.
- Use the CD Showcase for playback.
- Track play buttons indicate the active track.

### MP3
- Browse the scanned MP3 collection.
- Search and inspect MP3 files.
- Link MP3 files to music tracks.
- Play music through the integrated player.

### Livesets
- Add and edit livesets in **Livesets Library**.
- Enter title, artist/DJ, date, location and duration.
- Link the actual liveset audio file with **KIES AUDIO**.
- Add or replace a liveset cover.
- Save changes with **OPSLAAN**.
- Open a liveset in the dedicated playback view.
- Play the linked liveset and use the animated visualizer.

## Starting VinylVault

From the project folder, run:

```powershell
python run_v3.py
```

On startup, VinylVault shows its animated introduction before opening the main application.

## Libraries and playback

The application separates collection management from the visual Showcase views. This means you can edit and organize your collection in the Library pages and then use the Showcase pages for a more visual playback experience.

When a liveset or track is played, playback is handled by the application's central media player.

## Adding a liveset

1. Open **Livesets Library**.
2. Choose **NIEUWE LIVESET**.
3. Enter the title and other information.
4. Click **KIES AUDIO** and select the liveset audio file.
5. Optionally choose a cover with **VERVANG FOTO**.
6. Click **OPSLAAN**.
7. Open the liveset in the playback view and press **PLAY LIVESET**.

The audio file itself remains at its original location. VinylVault stores the path to the file rather than copying the audio into the project.

## Covers and local data

Local application data is stored under the `data` directory. Covers used by the application may also be stored there.

The main collection database is local and is intentionally not treated as source code. Large media files such as MP3, WAV and FLAC files are also not stored in Git.

## Discogs and metadata

VinylVault can use Discogs-related tools and metadata features where configured. These features are intended to enrich the local collection without replacing the local collection itself.

## Troubleshooting

### The application does not start

Run the following from the project folder:

```powershell
python -m py_compile run_v3.py
python run_v3.py
```

If a Python file was recently changed, it can also be checked directly with:

```powershell
python -m py_compile gui\filename.py
```

### A liveset does not play

Open **Livesets Library** and check the liveset's **Audio bestand** field. Make sure the selected audio file still exists at that location.

### A cover is missing

Open the liveset in the Library and use **VERVANG FOTO** to select the cover again.

### MP3 links are missing

Check the MP3 Library and the track's linked MP3 files. MP3 files are referenced by their filesystem paths, so moving or renaming the original files can break an existing link.

## Important

VinylVault is designed around a local music collection. Keep the original music files in their intended locations and avoid manually editing the local database unless you know exactly what you are changing.

## Project structure

```text
KidAcidsVinylVaultV3/
├── data/                 Local application data
├── database/             Database code
├── gui/                  User interface pages
├── tools/                Utility and import tools
├── run_v3.py             Application launcher
└── README.md             This guide
```

## Current stable development branch

The current working branch is:

`rescue-my-work-cd`

This branch contains the current tested VinylVault V3 application, including the CD Showcase work, Livesets playback/visualizer and startup splash screen.

---

**Kid Acid's VinylVault V3**  
*Built for managing, exploring and playing a personal music collection.*
