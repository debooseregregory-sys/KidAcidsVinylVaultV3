from __future__ import annotations

from gui.app_settings import paint_accent

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class HelpPage(QWidget):
    """Nederlandstalige, uitgebreide handleiding binnen MusicVault."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("helpPage")
        self._sections = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 24, 30, 24)
        root.setSpacing(14)

        kicker = QLabel("KID ACID'S MUSICVAULT V3")
        kicker.setObjectName("helpKicker")
        root.addWidget(kicker)

        title = QLabel("HANDLEIDING")
        title.setObjectName("helpTitle")
        root.addWidget(title)

        subtitle = QLabel("Een uitgebreide gids voor het beheren, terugvinden, bekijken en afspelen van je muziekcollectie.")
        subtitle.setObjectName("helpSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        self.search = QLineEdit()
        self.search.setObjectName("helpSearch")
        self.search.setPlaceholderText("Zoeken in de handleiding...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._search)
        root.addWidget(self.search)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("helpScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.content = QWidget()
        self.content.setObjectName("helpContent")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(8, 4, 22, 20)
        self.content_layout.setSpacing(0)
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll, 1)

        self.setStyleSheet(paint_accent("""
            QLabel#helpKicker{color:#ffcf72;font-size:10px;font-weight:900;letter-spacing:2px;}
            QLabel#helpTitle{color:#fff;font-size:30px;font-weight:900;}
            QLabel#helpSubtitle{color:#92929d;font-size:13px;}
            QLineEdit#helpSearch{background:#111116;color:#fff;border:1px solid #30303a;border-radius:9px;padding:10px 12px;font-size:12px;}
            QLineEdit#helpSearch:focus{border-color:#ffcf72;}
            QScrollArea#helpScroll{background:transparent;border:0px;}
            QWidget#helpSection{background:transparent;}
            QLabel#sectionNumber{color:#ffcf72;font-size:10px;font-weight:900;letter-spacing:1px;}
            QLabel#sectionTitle{color:#fff;font-size:25px;font-weight:900;}
            QLabel#sectionIntro{color:#aaaab4;font-size:13px;line-height:1.45;}
            QWidget#helpItem{background:transparent;}
            QLabel#itemNumber{color:#5f5f6b;font-size:10px;font-weight:900;}
            QLabel#sectionHeading{color:#ffcf72;font-size:13px;font-weight:900;}
            QLabel#sectionText{color:#c2c2c9;font-size:12px;line-height:1.5;}
            QFrame#helpDivider{color:#292933;background:#292933;border:0px;max-height:1px;}
            QScrollBar:vertical{background:#0d0d11;width:9px;border-radius:4px;}
            QScrollBar::handle:vertical{background:#34343e;border-radius:4px;min-height:35px;}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0px;}
        """))

        self._sections = [
            ("Welkom", "Welkom bij MusicVault", "MusicVault is je persoonlijke muziekverzameling in één programma. Vinyl, CD's, MP3-bestanden en Livesets hebben elk hun eigen plaats, terwijl ze samen gebruikmaken van dezelfde centrale speler. De bedoeling is dat je collectie niet alleen netjes bewaard wordt, maar vooral snel terug te vinden, prettig te bekijken en eenvoudig af te spelen is.", [
                ("Waarvoor dient MusicVault?", "Gebruik de bibliotheken wanneer je gericht wilt zoeken, gegevens wilt controleren of je collectie wilt onderhouden. De Showcases leggen juist meer nadruk op artwork, grote tracklijsten, animatie en de ervaring van het luisteren."),
                ("Je originele muziek blijft behouden", "MusicVault werkt met verwijzingen naar bestanden op je computer. Het programma hoeft je originele MP3-bestanden dus niet in een aparte opslag te kopiëren. Daardoor blijven je bestaande mappen en bestanden bruikbaar terwijl MusicVault de informatie eromheen organiseert."),
                ("De handleiding gebruiken", "Lees een hoofdstuk wanneer je wilt weten hoe een onderdeel bedoeld is. De teksten beschrijven niet alleen wat een knop doet, maar ook waarom een functie bestaat en waar je moet kijken wanneer iets onverwacht werkt."),
            ]),
            ("Snel beginnen", "Van opstarten naar muziek", "Je hoeft MusicVault niet volledig te kennen voordat je ermee kunt werken. Controleer eerst de basisinstellingen, kijk of je bibliotheken gevuld zijn, controleer belangrijke audiokoppelingen en probeer daarna een track of Liveset af te spelen. Zodra dat goed werkt, kun je de uitgebreidere functies rustig ontdekken.", [
                ("Instellingen controleren", "Controleer de database- en muziekmappen voordat je grote wijzigingen uitvoert. Wanneer je externe metadata gebruikt, controleer dan ook de daarvoor bedoelde instellingen zodat zoekacties en imports met de juiste gegevens werken."),
                ("Collectie bekijken", "Open Vinyl, CD, MP3 of Livesets en controleer of de inhoud die je verwacht zichtbaar is. Dit is een eenvoudige maar nuttige eerste controle omdat je meteen merkt wanneer een map, database of configuratie niet correct is ingesteld."),
                ("Audiokoppelingen controleren", "Een track kan zichtbaar zijn terwijl het bijbehorende bestand intussen verplaatst of verwijderd is. Controleer daarom bij belangrijke muziek of de opgeslagen verwijzing werkelijk naar een bestaand audiobestand wijst."),
                ("Afspelen", "Open een track, release of Liveset en start het afspelen. De centrale speler verzorgt de werkelijke audio, terwijl de verschillende pagina's de juiste visuele status kunnen tonen."),
            ]),
            ("Vinyl", "Vinylbibliotheek en releases", "De Vinylbibliotheek is het administratieve gedeelte van je fysieke vinylcollectie. Je gebruikt deze pagina vooral om releases terug te vinden, gegevens te controleren en een release te openen voor de volledige tracklijst en verdere acties.", [
                ("Zoeken", "Zoek op artiest, titel of andere herkenbare releasegegevens. Bij een grote collectie werkt een combinatie van artiest en titel meestal sneller dan alleen een algemeen zoekwoord."),
                ("Release openen", "Open een release wanneer je meer wilt zien dan de korte bibliotheekweergave. Daar kun je de hoes, metadata, tracks en beschikbare afspeelkoppelingen controleren."),
                ("Tracks en MP3's", "Wanneer een track aan een werkend audiobestand gekoppeld is, kan de centrale speler dat bestand afspelen. De vinylrelease blijft daarbij de collectie-informatie; het MP3-bestand is alleen de digitale afspeelbron."),
                ("Kastcode", "Een kastcode of andere lokale locatiegegevens beschrijven jouw eigen exemplaar. Zulke gegevens zijn daarom belangrijk voor het terugvinden van de fysieke plaat en moeten niet worden verward met externe releasegegevens."),
            ]),
            ("Vinyl Showcase", "De visuele kant van vinyl", "De Vinyl Showcase is bedoeld om releases op een aantrekkelijkere en ruimere manier te beleven. De bibliotheek is praktisch en compact; de Showcase gebruikt meer ruimte voor artwork, tracklijsten, afspeelknoppen en visuele effecten.", [
                ("Track afspelen", "Gebruik de afspeelknop bij de gewenste track. Wanneer de centrale speler die track werkelijk actief heeft, wordt de actieve toestand visueel onderscheiden zodat je onmiddellijk ziet wat je hoort."),
                ("Bibliotheek en Showcase", "Gebruik de Bibliotheek voor zoeken, beheren en controleren. Gebruik de Showcase wanneer je vooral door releases wilt bladeren, de hoes wilt bekijken en muziek op een visuelere manier wilt beleven."),
                ("Waarom twee weergaven", "Een grote muziekcollectie heeft zowel een administratieve als een artistieke kant. Door die twee functies te scheiden blijft zoeken overzichtelijk terwijl de Showcase ruimte krijgt voor een veel rijkere presentatie."),
            ]),
            ("CD", "CD-bibliotheek en Showcase", "CD's hebben een eigen bibliotheek en Showcase zodat ze dezelfde comfortabele afspeelervaring kunnen krijgen als vinyl, maar met een presentatie die specifiek op CD-releases gericht is. De bibliotheek blijft bedoeld voor beheer; de Showcase voor presentatie en luisteren.", [
                ("Bibliotheek", "Zoek een CD, open de gewenste release en controleer de gegevens en tracks. Vanuit de releaseweergave kun je zien welke muziek beschikbaar is en welke tracks aan audiobestanden gekoppeld zijn."),
                ("Showcase", "De CD Showcase toont de release groter en visueler. De centrale speler blijft verantwoordelijk voor de echte audio, waardoor de Showcase en de speler dezelfde afspeelstatus kunnen delen."),
                ("Trackknoppen", "Een niet-actieve track gebruikt een andere visuele toestand dan de track die werkelijk speelt. Daardoor hoef je niet te raden welke regel overeenkomt met de muziek die op dat moment uit de speler komt."),
            ]),
            ("MP3", "MP3-bibliotheek en koppelingen", "De MP3-bibliotheek bevat de digitale audiobestanden waarop MusicVault kan terugvallen voor het afspelen. Het is belangrijk om de bibliotheekgegevens en de werkelijke bestanden als twee verschillende zaken te zien: MusicVault kan een pad bewaren, maar het bestand staat fysiek op jouw schijf.", [
                ("Bestand versus koppeling", "Een MP3-koppeling verwijst naar een concreet bestand. Als dat bestand bestaat, kan de speler het openen. Als het is verplaatst of verwijderd, kan de koppeling nog steeds in de database staan terwijl afspelen niet meer lukt."),
                ("Bestanden verplaatsen", "Wanneer je bestanden buiten MusicVault om verplaatst of hernoemt, verandert de opgeslagen verwijzing niet automatisch mee. Controleer daarom koppelingen nadat je grote wijzigingen in je muziekmappen hebt uitgevoerd."),
                ("Ontbrekende MP3", "Verwijder niet meteen een track wanneer een audiobestand ontbreekt. Controleer eerst of het bestand alleen op een andere plaats staat. Vaak is het veiliger om de bestaande koppeling opnieuw naar het juiste bestand te laten wijzen."),
                ("Meerdere versies", "Wanneer verschillende audioversies bestaan, vergelijk dan artiest, titel en bestandsnaam voordat je een bestand als voorkeur gebruikt. Zo voorkom je dat per ongeluk een verkeerde opname als standaard wordt afgespeeld."),
            ]),
            ("Speler", "De centrale muziekspeler", "De centrale speler is het gemeenschappelijke afspeelpunt van MusicVault. Een bibliotheek, Showcase of Liveset kan een bestand doorgeven, maar de daadwerkelijke audio wordt door dezelfde speler geopend en afgespeeld. Daardoor kunnen verschillende schermen dezelfde actieve toestand volgen.", [
                ("Afspelen", "Start een track vanuit een bibliotheek, Showcase of Liveset. De pagina geeft het audiopad door waarna de centrale speler het bestand opent en de muziek start."),
                ("Actieve inhoud", "De visuele onderdelen kunnen luisteren naar de werkelijke afspeelstatus van de speler. Daardoor verandert een knop wanneer de audio echt actief wordt en niet alleen wanneer iemand op de knop heeft geklikt."),
                ("Livesets", "Bij een Liveset is vooral het daadwerkelijke audiopad belangrijk. De afspeelpagina toont de gegevens van de geselecteerde set, terwijl de centrale speler bepaalt welk bestand werkelijk actief is."),
                ("Wanneer iets niet speelt", "Controleer eerst of het bestandspad nog bestaat en of Windows het bestand kan openen. Controleer daarna de MusicVault-koppeling en probeer opnieuw. Zo voorkom je dat je onnodig gegevens uit de collectie verwijdert."),
            ]),
            ("Livesets", "Livesets beheren", "Livesets zijn volledige DJ-sets met hun eigen titel, artiest, datum, locatie, duur, audio en cover. In de Livesetsbibliotheek beheer je deze gegevens en bepaal je welk werkelijk audiobestand bij een set hoort.", [
                ("Nieuwe Liveset", "Maak een nieuwe Liveset aan en vul de bekende gegevens in. Titel en artiest maken de set herkenbaar, terwijl datum, locatie en duur extra context geven wanneer je later door een grote verzameling bladert."),
                ("Audio kiezen", "Gebruik KIES AUDIO om het echte MP3- of audiobestand op je computer te selecteren. MusicVault bewaart het pad naar dat bestand en verandert je originele audio niet."),
                ("Opslaan", "Met OPSLAAN worden de gegevens van de geselecteerde Liveset lokaal bewaard. Na een belangrijke wijziging kun je controleren of de set opnieuw correct in de lijst verschijnt en of het audiopad nog klopt."),
                ("Cover toevoegen", "Met VERVANG FOTO kies je een afbeelding voor de set. De editor kan de gekozen afbeelding lokaal in de Liveset-covermap bewaren zodat de presentatie niet afhankelijk blijft van een tijdelijke oorspronkelijke locatie."),
                ("Verwijderen", "Wanneer je een Liveset verwijdert, wordt de vermelding uit MusicVault verwijderd. Het oorspronkelijke audiobestand blijft behouden, zodat je geen muziekbestand kwijtraakt alleen omdat je de registratie uit de bibliotheek verwijdert."),
            ]),
            ("Liveset afspelen", "De grote Liveset-afspeelpagina", "De Liveset-afspeelpagina brengt de gegevens van de gekozen set, de cover, de afspeelknop en de grote animatie samen. Het doel is een echte afspeelervaring te geven waarbij de visuele informatie overeenkomt met de set die werkelijk is geselecteerd.", [
                ("Titel en artiest", "De afspeelpagina neemt de titel en artiest over van de geselecteerde Liveset. Zo blijft de informatie zichtbaar terwijl de grote animatie de aandacht op het afspelen legt."),
                ("Nu aan het spelen", "De melding voor de actieve Liveset hoort inhoudelijk overeen te komen met de audio die de centrale speler werkelijk afspeelt. De bedoeling is dus niet om een vaste slogan te tonen, maar om de actuele set herkenbaar te maken."),
                ("Animatie", "De grote animatie gebruikt de beschikbare ruimte van de pagina voor een rijkere visuele muziekervaring. Ze is bewust losgekoppeld van de administratieve bibliotheek zodat beheer en presentatie elkaar niet in de weg zitten."),
                ("Verkeerde naam controleren", "Wanneer de getoonde naam niet overeenkomt met de audio, kijk dan eerst naar het werkelijke audiopad van de centrale speler en vergelijk dat met het pad van de geselecteerde Liveset. De echte spelerstatus is de betrouwbare bron voor wat werkelijk klinkt."),
            ]),
            ("Covers", "Hoezen en afbeeldingen", "Covers maken releases en Livesets onmiddellijk herkenbaar en geven de Showcases hun visuele karakter. MusicVault kan covers lokaal gebruiken zonder dat je originele muziekbestanden daardoor worden aangepast.", [
                ("Cover vervangen", "Kies een nieuwe afbeelding wanneer de bestaande cover ontbreekt, verouderd is of niet mooi genoeg is. De editor maakt indien nodig een lokale kopie voor de Liveset."),
                ("Bestandsbeheer", "Een cover en een audiobestand zijn verschillende bestanden. Het verwijderen van een oude cover mag daarom nooit betekenen dat het bijbehorende MP3-bestand wordt verwijderd."),
                ("Goede afbeeldingen", "Gebruik bij voorkeur een scherpe afbeelding met voldoende resolutie zodat de cover ook in een grote Showcaseweergave mooi blijft. JPG, JPEG, PNG en WEBP zijn geschikte gangbare formaten."),
            ]),
            ("Discogs", "Externe release-informatie", "Discogs kan worden gebruikt als bron voor releasegegevens en metadata. Zie externe metadata vooral als aanvulling op jouw eigen collectiegegevens: jouw kastcode, lokale gegevens en werkelijke MP3-koppelingen blijven informatie over jouw eigen collectie.", [
                ("Zoeken en importeren", "Gebruik Discogs wanneer je releasegegevens wilt aanvullen of controleren. Controleer de gevonden release voordat je gegevens overneemt, vooral wanneer meerdere versies van dezelfde titel bestaan."),
                ("Eigen gegevens", "Externe metadata mag je lokale collectie-informatie niet zomaar overschrijven. Een Discogs-release beschrijft een release; jouw kastcode en bestandskoppelingen beschrijven jouw eigen verzameling."),
            ]),
            ("Problemen oplossen", "Als iets niet werkt", "De meeste problemen ontstaan doordat een bestand is verplaatst, een koppeling niet meer bestaat of een pagina niet dezelfde centrale spelerstatus volgt. Werk daarom van buiten naar binnen: controleer eerst het bestand, daarna de koppeling en pas daarna de interface.", [
                ("Audio speelt niet", "Controleer of het audiobestand werkelijk bestaat en door Windows geopend kan worden. Controleer vervolgens het opgeslagen pad en probeer het bestand opnieuw via de juiste pagina te starten."),
                ("Verkeerde Now Playing", "Vergelijk de werkelijk actieve spelerbron met de Liveset of track die op het scherm wordt getoond. De geselecteerde pagina is niet altijd hetzelfde als de audio die de centrale speler momenteel afspeelt."),
                ("Cover ontbreekt", "Controleer eerst of het opgeslagen coverpad nog bestaat. Wanneer de afbeelding is verplaatst of verwijderd, kies dan via de editor een nieuwe cover."),
                ("Wijziging lijkt niet opgeslagen", "Controleer of je de juiste record hebt geselecteerd en gebruik OPSLAAN. Controleer daarna of de gegevens opnieuw in de lijst verschijnen voordat je verdergaat."),
            ]),
            ("Veilig werken", "Je collectie beschermen", "MusicVault bevat waardevolle collectie-informatie. Werk daarom rustig wanneer je grote wijzigingen uitvoert en verwijder geen bestanden of databasegegevens alleen omdat een koppeling tijdelijk niet werkt.", [
                ("Audiobestanden", "Verwijder originele MP3-bestanden niet alleen omdat MusicVault een koppeling niet kan openen. Controleer eerst of het bestand verplaatst of hernoemd is."),
                ("Database", "De database bevat collectie-informatie die niet eenvoudig opnieuw uit je muziekbestanden kan worden afgeleid. Vermijd handmatige databasewijzigingen wanneer een normale editor beschikbaar is."),
                ("Grote wijzigingen", "Voer grote opruimacties stap voor stap uit. Controleer na een wijziging eerst het resultaat voordat je verdergaat met de volgende groep bestanden of releases."),
            ]),
        ]

        self._render_sections()

    def _render_sections(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        query = self.search.text().strip().casefold()

        for index, (name, title, intro, entries) in enumerate(self._sections, 1):
            haystack = " ".join([name, title, intro, *[f"{a} {b}" for a, b in entries]]).casefold()
            if query and query not in haystack:
                continue

            section = QWidget()
            section.setObjectName("helpSection")
            layout = QVBoxLayout(section)
            layout.setContentsMargins(12, 26, 12, 30)
            layout.setSpacing(0)

            number = QLabel(f"HOOFDSTUK {index:02d}")
            number.setObjectName("sectionNumber")
            layout.addWidget(number)

            heading = QLabel(title)
            heading.setObjectName("sectionTitle")
            heading.setWordWrap(True)
            layout.addWidget(heading)

            description = QLabel(intro)
            description.setObjectName("sectionIntro")
            description.setWordWrap(True)
            description.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            layout.addWidget(description)

            intro_divider = QFrame()
            intro_divider.setObjectName("helpDivider")
            intro_divider.setFrameShape(QFrame.Shape.HLine)
            intro_divider.setFrameShadow(QFrame.Shadow.Plain)
            layout.addWidget(intro_divider)
            layout.addSpacing(14)

            for item_index, (item_title, item_text) in enumerate(entries, 1):
                item_widget = QWidget()
                item_widget.setObjectName("helpItem")
                item_layout = QVBoxLayout(item_widget)
                item_layout.setContentsMargins(0, 0, 0, 18)
                item_layout.setSpacing(5)

                item_number = QLabel(f"{item_index:02d}")
                item_number.setObjectName("itemNumber")
                item_layout.addWidget(item_number)

                item_heading = QLabel(item_title)
                item_heading.setObjectName("sectionHeading")
                item_heading.setWordWrap(True)
                item_layout.addWidget(item_heading)

                item_text_label = QLabel(item_text)
                item_text_label.setObjectName("sectionText")
                item_text_label.setWordWrap(True)
                item_text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                item_layout.addWidget(item_text_label)

                layout.addWidget(item_widget)

                if item_index < len(entries):
                    divider = QFrame()
                    divider.setObjectName("helpDivider")
                    divider.setFrameShape(QFrame.Shape.HLine)
                    divider.setFrameShadow(QFrame.Shadow.Plain)
                    layout.addWidget(divider)
                    layout.addSpacing(14)

            self.content_layout.addWidget(section)

        self.content_layout.addStretch(1)

    def _search(self, _text):
        self._render_sections()
