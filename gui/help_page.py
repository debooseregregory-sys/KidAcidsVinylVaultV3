from __future__ import annotations

from gui.app_settings import paint_accent

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class HelpPage(QWidget):
    """Rustige, volledig Nederlandstalige handleiding binnen MusicVault."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("helpPage")
        self._sections = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 24, 30, 24)
        root.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(18)

        intro = QVBoxLayout()
        intro.setSpacing(3)

        kicker = QLabel("KID ACID'S MUSICVAULT V3")
        kicker.setObjectName("helpKicker")
        intro.addWidget(kicker)

        title = QLabel("HANDLEIDING")
        title.setObjectName("helpTitle")
        intro.addWidget(title)

        subtitle = QLabel("Alles wat je nodig hebt om je collectie te beheren en muziek af te spelen.")
        subtitle.setObjectName("helpSubtitle")
        subtitle.setWordWrap(True)
        intro.addWidget(subtitle)
        header.addLayout(intro, 1)

        self.search = QLineEdit()
        self.search.setObjectName("helpSearch")
        self.search.setPlaceholderText("Zoeken in de handleiding...")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(270)
        self.search.textChanged.connect(self._search)
        header.addWidget(self.search, 0, Qt.AlignmentFlag.AlignBottom)
        root.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(18)

        self.menu = QListWidget()
        self.menu.setObjectName("helpMenu")
        self.menu.setFixedWidth(205)
        self.menu.currentRowChanged.connect(self._show_section)
        body.addWidget(self.menu)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("helpScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.content = QWidget()
        self.content.setObjectName("helpContent")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(8, 4, 22, 20)
        self.content_layout.setSpacing(14)
        self.scroll.setWidget(self.content)
        body.addWidget(self.scroll, 1)
        root.addLayout(body, 1)

        self.setStyleSheet(paint_accent("""
            QLabel#helpKicker{color:#ffcf72;font-size:10px;font-weight:900;letter-spacing:2px;}
            QLabel#helpTitle{color:#fff;font-size:30px;font-weight:900;}
            QLabel#helpSubtitle{color:#92929d;font-size:13px;}
            QLineEdit#helpSearch{background:#111116;color:#fff;border:1px solid #30303a;border-radius:9px;padding:10px 12px;font-size:12px;}
            QLineEdit#helpSearch:focus{border-color:#ffcf72;}
            QListWidget#helpMenu{background:#0f0f14;border:1px solid #292933;border-radius:10px;padding:8px;outline:0;}
            QListWidget#helpMenu::item{color:#9999a4;padding:11px 12px;border-radius:7px;font-size:11px;font-weight:800;}
            QListWidget#helpMenu::item:hover{background:#18181f;color:#fff;}
            QListWidget#helpMenu::item:selected{background:#28242a;color:#ffcf72;}
            QFrame#helpSection{background:#111116;border:1px solid #292933;border-radius:12px;}
            QLabel#sectionNumber{color:#ffcf72;font-size:10px;font-weight:900;}
            QLabel#sectionTitle{color:#fff;font-size:23px;font-weight:900;}
            QLabel#sectionIntro{color:#aaaab4;font-size:13px;line-height:1.4;}
            QLabel#sectionHeading{color:#ffcf72;font-size:12px;font-weight:900;}
            QLabel#sectionText{color:#c2c2c9;font-size:12px;}
            QLabel#tip{background:#17171e;color:#d0d0d6;border-left:3px solid #ffcf72;padding:12px;font-size:12px;}
            QScrollBar:vertical{background:#0d0d11;width:9px;border-radius:4px;}
            QScrollBar::handle:vertical{background:#34343e;border-radius:4px;min-height:35px;}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0px;}
        """))

        sections = [
            ("Welkom", "Welkom bij MusicVault", "MusicVault is je eigen muziekverzameling in één programma. Vinyl, CD's, MP3-bestanden en Livesets hebben elk hun eigen onderdeel, terwijl de centrale speler de muziek daadwerkelijk afspeelt.", [
                ("Waarvoor dient MusicVault?", "Gebruik de Libraries om je collectie te vinden en te beheren. Gebruik de Showcases wanneer je vooral de muziek, hoezen en visuele presentatie wilt beleven."),
                ("Belangrijk", "Je eigen bestanden blijven op je computer staan. MusicVault bewaart vooral informatie over je collectie, koppelingen en lokale gegevens."),
            ]),
            ("Snel beginnen", "In vier stappen aan de slag", "Als je MusicVault voor het eerst gebruikt, hoef je niet alles tegelijk in te stellen.", [
                ("01  Instellingen", "Controleer eerst de instellingen voor je database, muziekmap en Discogs."),
                ("02  Bibliotheek", "Open Vinyl, CD, MP3 of Livesets en controleer of je collectie zichtbaar is."),
                ("03  Koppelingen", "Controleer bij tracks of het juiste MP3-bestand gekoppeld is."),
                ("04  Afspelen", "Open een track of Liveset en gebruik de centrale speler onderaan."),
            ]),
            ("Vinyl", "Vinylbibliotheek en releases", "De Vinylbibliotheek is bedoeld om je fysieke vinylcollectie te vinden, te bekijken en te beheren.", [
                ("Zoeken", "Gebruik de zoekfunctie om artiesten, titels en releases snel te vinden."),
                ("Release openen", "Open een release om de hoes, gegevens en volledige tracklijst te bekijken."),
                ("Tracks", "Wanneer een track aan een MP3 gekoppeld is, kun je die rechtstreeks afspelen."),
                ("Kastcode", "Lokale gegevens zoals je kastcode horen bij je eigen collectie. Wijzig die alleen wanneer je dat bewust wilt."),
            ]),
            ("Vinyl Showcase", "Vinyl als visuele ervaring", "De Vinyl Showcase is de presentatiekant van je collectie. Hier draait het minder om administratie en meer om bladeren, artwork en muziek.", [
                ("Afspelen", "Gebruik de afspeelknoppen bij de tracks. De actieve track krijgt een duidelijke actieve status."),
                ("Bibliotheek versus Showcase", "De Bibliotheek is voor zoeken en beheren; de Showcase is voor bekijken en beleven."),
            ]),
            ("CD", "CD-bibliotheek en Showcase", "CD's hebben binnen MusicVault een eigen bibliotheek en eigen Showcase.", [
                ("Bibliotheek", "Zoek een CD, open hem en bekijk de gegevens en tracks."),
                ("Showcase", "De CD Showcase is de visuele weergave. De centrale speler verzorgt het echte afspelen."),
                ("Trackknoppen", "De knop toont duidelijk wanneer een track actief aan het afspelen is."),
            ]),
            ("MP3", "MP3-bibliotheek en koppelingen", "De MP3-bibliotheek bevat de werkelijke audiobestanden die op je computer staan.", [
                ("Bestand versus koppeling", "Een MP3-koppeling is een verwijzing naar een bestand op schijf. Het bestand zelf wordt niet in de database opgeslagen."),
                ("Bestanden verplaatsen", "Als je een MP3 buiten MusicVault verplaatst of hernoemt, kan de bestaande koppeling ongeldig worden."),
                ("Ontbrekende MP3", "Controleer eerst of het originele bestand nog bestaat voordat je een track of databasegegeven verwijdert."),
            ]),
            ("Speler", "De centrale muziekspeler", "De speler onderaan is de gemeenschappelijke afspeelvoorziening van MusicVault.", [
                ("Afspelen", "Start een track vanuit een Library, Showcase of Liveset. De centrale speler neemt de daadwerkelijke audio over."),
                ("Actieve inhoud", "Pagina's kunnen naar de speler luisteren om te tonen welke track of Liveset werkelijk speelt."),
                ("Probleem", "Speelt iets niet? Controleer eerst het bestandspad en probeer daarna de koppeling opnieuw in te stellen."),
            ]),
            ("Livesets", "Livesets beheren", "Livesets zijn volledige DJ-sets met hun eigen titel, artiest, datum, locatie, duur, audio en cover.", [
                ("Nieuwe Liveset", "Maak een nieuwe Liveset aan en vul de gegevens in."),
                ("Audio koppelen", "Gebruik KIES AUDIO om het echte MP3- of audiobestand te selecteren."),
                ("Opslaan", "Met OPSLAAN worden de gegevens bewaard. Het oorspronkelijke audiobestand wordt daarbij niet gekopieerd of verwijderd."),
                ("Cover", "Gebruik VERVANG FOTO om een afbeelding aan de Liveset te koppelen."),
            ]),
            ("Liveset afspelen", "Liveset Showcase en afspeelpagina", "De Showcase brengt je naar de speciale afspeelpagina van de geselecteerde Liveset.", [
                ("Afspeelpagina", "Daar zie je de echte cover, titel, artiest en gegevens van de gekozen set."),
                ("Animatie", "De grote animatie hoort bij de afspeelpagina en reageert op de actieve Liveset."),
                ("Nu aan het spelen", "De weergegeven naam moet overeenkomen met de Liveset die daadwerkelijk door de centrale speler wordt afgespeeld."),
            ]),
            ("Covers", "Hoezen en afbeeldingen", "Covers maken de collectie visueel herkenbaar.", [
                ("Toevoegen", "Kies op de betreffende pagina een afbeelding om een cover toe te voegen of te vervangen."),
                ("Livesets", "Liveset-covers worden lokaal in de daarvoor bestemde covermap bewaard."),
                ("Veiligheid", "Verwijder geen coverbestanden handmatig als je niet zeker weet welke gegevens ernaar verwijzen."),
            ]),
            ("Discogs", "Discogs en gegevens verrijken", "Discogs levert externe releasegegevens die je kunt gebruiken om je collectie aan te vullen.", [
                ("Importeren", "Controleer altijd eerst welke release je selecteert voordat je een grote import uitvoert."),
                ("Matchen", "Vergelijk artiest, titel, formaat, catalogusgegevens en tracklijst. Eén overeenkomst is niet altijd voldoende."),
                ("Lokale gegevens", "Discogs-gegevens zijn niet hetzelfde als je eigen collectiegegevens. Lokale informatie mag niet zomaar worden overschreven."),
            ]),
            ("Instellingen", "Instellingen van MusicVault", "In Instellingen vind je de onderdelen waarmee je MusicVault configureert.", [
                ("Muziekbibliotheek", "Controleer waar je muziekbestanden staan en hoe de bibliotheek ermee werkt."),
                ("Discogs", "Beheer hier de instellingen die nodig zijn voor Discogs."),
                ("Database", "Ga voorzichtig om met database-instellingen. Wijzig niets zonder te weten welk effect het heeft."),
            ]),
            ("Veilig werken", "Je collectie veilig houden", "MusicVault bevat veel lokale gegevens. Kleine, gecontroleerde wijzigingen zijn daarom beter dan grote wijzigingen in één keer.", [
                ("Voor grote wijzigingen", "Zorg dat MusicVault correct start en maak indien nodig eerst een backup."),
                ("Niet zomaar verwijderen", "Verwijder de database, MP3-bestanden of covermappen niet omdat iets tijdelijk ontbreekt in een Library."),
                ("Na een wijziging", "Test precies de pagina en functie die je hebt aangepast voordat je verdergaat."),
            ]),
            ("Problemen", "Veelvoorkomende problemen", "De meeste problemen zijn terug te brengen tot een verkeerd bestandspad, een ontbrekende koppeling of een configuratieprobleem.", [
                ("MP3 speelt niet", "Controleer of het bestand nog bestaat op het opgeslagen pad. Stel de koppeling opnieuw in als het bestand verplaatst is."),
                ("Liveset speelt niet", "Open de Livesetsbibliotheek, kies de set, controleer Audio bestand, kies het bestand opnieuw en druk op OPSLAAN."),
                ("Cover ontbreekt", "Kies de cover opnieuw vanuit de editor van de betreffende release of Liveset."),
                ("Programma start niet", "Start run_v3.py vanuit PowerShell en kijk naar de eerste foutmelding. Die wijst meestal naar het bestand dat aandacht nodig heeft."),
            ]),
            ("Onderhoud", "Werken met de projectbestanden", "MusicVault wordt als softwareproject onderhouden met Git. Dat maakt het mogelijk om werkende versies te bewaren en wijzigingen gecontroleerd door te voeren.", [
                ("Voor ophalen van nieuwe wijzigingen", "Controleer eerst of je lokale werkmap schoon is of dat je je wijzigingen bewust hebt opgeslagen."),
                ("Na een wijziging", "Compileer het gewijzigde Python-bestand en start MusicVault om de betreffende functie te testen."),
                ("Bij twijfel", "Niet blijven experimenteren met meerdere bestanden tegelijk. Noteer eerst wat er precies fout gaat."),
            ]),
            ("Over MusicVault", "Kid Acid's MusicVault V3", "MusicVault brengt je fysieke collectie, digitale muziek en Livesets samen in één lokale muziekomgeving, met artwork, metadata, koppelingen, afspelen en visuele Showcases.", [
                ("Het uitgangspunt", "Je collectie blijft van jou. MusicVault helpt je om ze overzichtelijk te beheren, terug te vinden en te beluisteren."),
                ("Tip", "Gebruik de Libraries voor beheer en de Showcases wanneer je gewoon door je muziek wilt bladeren en luisteren."),
            ]),
        ]

        for index, (name, title, intro_text, items) in enumerate(sections, 1):
            self._sections.append((name, title, intro_text, items))
            self.menu.addItem(QListWidgetItem(name))

        if sections:
            self.menu.setCurrentRow(0)

    def _show_section(self, index: int):
        if index < 0 or index >= len(self._sections):
            return

        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        name, title, intro_text, items = self._sections[index]

        card = QFrame()
        card.setObjectName("helpSection")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(26, 24, 26, 26)
        layout.setSpacing(14)

        number = QLabel(f"{index + 1:02d}  /  {name.upper()}")
        number.setObjectName("sectionNumber")
        layout.addWidget(number)

        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        intro = QLabel(intro_text)
        intro.setObjectName("sectionIntro")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        for heading, text in items:
            heading_label = QLabel(heading)
            heading_label.setObjectName("sectionHeading")
            layout.addWidget(heading_label)

            text_label = QLabel(text)
            text_label.setObjectName("sectionText")
            text_label.setWordWrap(True)
            layout.addWidget(text_label)

        self.content_layout.addWidget(card)
        self.content_layout.addStretch(1)
        self.scroll.verticalScrollBar().setValue(0)

    def _search(self, query: str):
        query = query.strip().casefold()
        if not query:
            for row in range(self.menu.count()):
                self.menu.item(row).setHidden(False)
            return

        first_match = -1
        for index, (name, title, intro_text, items) in enumerate(self._sections):
            haystack = " ".join([name, title, intro_text] + [f"{h} {t}" for h, t in items]).casefold()
            match = query in haystack
            self.menu.item(index).setHidden(not match)
            if match and first_match < 0:
                first_match = index

        if first_match >= 0 and self.menu.currentRow() != first_match:
            self.menu.setCurrentRow(first_match)
