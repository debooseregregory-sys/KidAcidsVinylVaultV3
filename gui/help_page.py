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
    """Rustige, volledig Nederlandstalige en uitgebreide handleiding binnen MusicVault."""

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

        subtitle = QLabel("Een uitgebreide gids voor het beheren, terugvinden en afspelen van je volledige muziekcollectie.")
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
            QLabel#sectionIntro{color:#aaaab4;font-size:13px;line-height:1.5;}
            QLabel#sectionHeading{color:#ffcf72;font-size:12px;font-weight:900;}
            QLabel#sectionText{color:#c2c2c9;font-size:12px;line-height:1.5;}
            QLabel#tip{background:#17171e;color:#d0d0d6;border-left:3px solid #ffcf72;padding:12px;font-size:12px;}
            QScrollBar:vertical{background:#0d0d11;width:9px;border-radius:4px;}
            QScrollBar::handle:vertical{background:#34343e;border-radius:4px;min-height:35px;}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0px;}
        """))

        sections = [
            ("Welkom", "Welkom bij MusicVault", "MusicVault is je persoonlijke muziekverzameling in één programma. Vinyl, CD's, MP3-bestanden en Livesets hebben elk hun eigen plaats, maar werken samen rond dezelfde centrale speler. Het doel is niet alleen om je collectie te bewaren, maar vooral om ze snel terug te vinden, te bekijken en daadwerkelijk te beluisteren.", [
                ("Waarvoor dient MusicVault?", "Gebruik de bibliotheken wanneer je gericht wilt zoeken, gegevens wilt controleren of koppelingen wilt beheren. De Showcases zijn juist bedoeld voor de visuele kant van je collectie: hoezen, tracklijsten, animaties en het afspelen van muziek komen daar meer op de voorgrond."),
                ("Je eigen muziek blijft van jou", "MusicVault werkt met verwijzingen naar bestanden op je computer. Het programma hoeft je originele MP3-bestanden dus niet in een aparte muziekopslag te stoppen. Daardoor blijven je bestaande mappen en bestanden bruikbaar, terwijl MusicVault de informatie eromheen kan organiseren."),
                ("Wat je in de handleiding vindt", "De hoofdstukken hieronder leggen niet alleen uit wat een onderdeel doet, maar ook wanneer je het gebruikt, welke gegevens belangrijk zijn en wat je kunt controleren als iets niet werkt."),
            ]),
            ("Snel beginnen", "In vier stappen aan de slag", "Je hoeft MusicVault niet in één keer volledig te begrijpen. Begin met de basis: zorg dat de instellingen kloppen, controleer je bibliotheken, kijk na of de audiobestanden goed gekoppeld zijn en probeer daarna een track of Liveset af te spelen. Van daaruit kun je de uitgebreidere functies rustig ontdekken.", [
                ("01  Instellingen controleren", "Open de instellingen en controleer vooral de database- en muziekbibliotheekinstellingen. Als je met Discogs werkt, controleer dan ook de instellingen daarvoor voordat je een import of zoekactie uitvoert."),
                ("02  Je collectie bekijken", "Open Vinyl, CD, MP3 of Livesets en controleer of de verwachte inhoud zichtbaar is. Dit is een goede eerste controle omdat je zo snel merkt wanneer een map, database of configuratie niet correct is ingesteld."),
                ("03  Koppelingen controleren", "Een track kan in MusicVault zichtbaar zijn zonder dat het bijbehorende audiobestand nog op de oorspronkelijke plaats staat. Controleer daarom bij belangrijke muziek of de MP3-koppeling werkelijk naar een bestaand bestand verwijst."),
                ("04  Afspelen", "Open een track, release of Liveset en start het afspelen. De centrale speler verzorgt vervolgens de echte audio. Andere pagina's kunnen die speler gebruiken om te tonen wat op dat moment actief is."),
            ]),
            ("Vinyl", "Vinylbibliotheek en releases", "De Vinylbibliotheek is het administratieve hart van je fysieke vinylcollectie. Hier kun je releases terugvinden, gegevens bekijken en een release openen om de volledige tracklijst en bijbehorende informatie te controleren. De bibliotheek is vooral handig wanneer je precies weet wat je zoekt of wanneer je je collectie wilt onderhouden.", [
                ("Zoeken", "Gebruik de zoekfunctie om artiesten, titels en andere herkenbare releasegegevens te vinden. Zoek bij voorkeur met een duidelijke artiest of titel wanneer je veel resultaten krijgt; zo hoef je niet door je volledige collectie te bladeren."),
                ("Een release openen", "Open een release wanneer je meer wilt zien dan de korte bibliotheekweergave. Je krijgt dan toegang tot de hoes, metadata en tracklijst en kunt van daaruit verder naar de muziek of andere beschikbare acties."),
                ("Tracks en MP3's", "Wanneer een track aan een bestaand audiobestand gekoppeld is, kan MusicVault dat bestand via de centrale speler afspelen. De trackinformatie en het fysieke vinylrecord zijn daarbij de collectiegegevens; het MP3-bestand is de digitale afspeelbron."),
                ("Kastcode en lokale gegevens", "Gegevens zoals een kastcode zijn onderdeel van jouw eigen collectie en kunnen belangrijk zijn om een fysieke plaat terug te vinden. Behandel zulke lokale gegevens daarom anders dan externe metadata: ze beschrijven jouw exemplaar en niet alleen de release op zich."),
            ]),
            ("Vinyl Showcase", "Vinyl als visuele ervaring", "De Vinyl Showcase is gemaakt om je collectie op een aantrekkelijkere manier te beleven. Waar de bibliotheek vooral draait om zoeken en beheren, ligt hier de nadruk op artwork, tracklijsten, grote elementen en het gevoel van een echte muziekcollectie. Je hoeft dus niet eerst alle administratieve details te bekijken om muziek te kunnen ontdekken.", [
                ("Afspelen", "Gebruik de afspeelknoppen bij de tracks om muziek te starten. De actieve track wordt visueel onderscheiden, zodat je snel kunt zien welke track de centrale speler op dat moment afspeelt."),
                ("Bibliotheek versus Showcase", "De Bibliotheek gebruik je wanneer je iets wilt zoeken, aanpassen of controleren. De Showcase gebruik je wanneer je door releases wilt bladeren, de hoes wilt bekijken en muziek op een meer visuele manier wilt beleven."),
                ("Waarom beide bestaan", "Een grote collectie heeft zowel een praktische als een visuele kant. Door die functies uit elkaar te houden blijft de bibliotheek overzichtelijk, terwijl de Showcase ruimte krijgt voor artwork en animatie zonder dat dit je zoekwerk in de weg zit."),
            ]),
            ("CD", "CD-bibliotheek en Showcase", "CD's hebben binnen MusicVault een eigen bibliotheek en een eigen Showcase. Daardoor kunnen ze dezelfde soort afspeelervaring bieden als vinyl, terwijl de gegevens en presentatie specifiek op CD's zijn afgestemd. De CD-bibliotheek is bedoeld voor beheer en terugvinden; de Showcase voor presentatie en luisteren.", [
                ("Bibliotheek", "Zoek een CD, open de gewenste release en controleer de gegevens en tracks. Vanuit de releaseweergave kun je nagaan welke muziek beschikbaar is en welke tracks aan audiobestanden gekoppeld zijn."),
                ("Showcase", "De CD Showcase geeft de release groter en visueler weer. De centrale speler blijft verantwoordelijk voor het echte afspelen, zodat de presentatiepagina niet zelf een aparte muziekbron hoeft te beheren."),
                ("Trackknoppen", "De afspeelknoppen maken onderscheid tussen een track die niet speelt en de track die momenteel actief is. Daardoor hoef je niet te raden welke regel in de tracklijst overeenkomt met de muziek die je hoort."),
                ("Trackgegevens aanpassen", "Wanneer een CD-track niet correct beschreven of gekoppeld is, gebruik je de daarvoor bedoelde editor in plaats van willekeurig gegevens in de database te veranderen. Zo blijft de structuur van de collectie intact."),
            ]),
            ("MP3", "MP3-bibliotheek en koppelingen", "De MP3-bibliotheek bevat de digitale audiobestanden waarop MusicVault kan terugvallen voor het afspelen. Een belangrijk onderscheid is dat de bibliotheekinformatie en de werkelijke bestanden twee verschillende dingen zijn: MusicVault kan een verwijzing naar een bestand bewaren, maar het bestand zelf staat in jouw muziekmap.", [
                ("Bestand versus koppeling", "Een MP3-koppeling is een verwijzing naar een concreet bestand op schijf. Als het bestand bestaat, kan de speler het openen; als het bestand is verdwenen of verplaatst, kan de koppeling nog wel in de database staan terwijl afspelen niet meer mogelijk is."),
                ("Bestanden verplaatsen of hernoemen", "Als je een MP3 buiten MusicVault om verplaatst, hernoemt of verwijdert, verandert de opgeslagen verwijzing niet automatisch mee. Dat is een belangrijke reden om muziekbestanden niet zomaar van map te veranderen zonder daarna de koppelingen te controleren."),
                ("Ontbrekende MP3", "Wanneer een track geen werkend audiobestand meer heeft, verwijder dan niet meteen de track of release. Controleer eerst of het bestand alleen verplaatst is. Vaak is het veiliger om de bestaande koppeling opnieuw aan het juiste bestand te verbinden."),
                ("Meerdere bestanden", "Wanneer er meerdere mogelijke audioversies bestaan, kijk dan goed naar bestandsnaam, artiest en titel voordat je een bestand als voorkeur gebruikt. Zo voorkom je dat een verkeerde versie als standaardafspeelbestand wordt gekozen."),
            ]),
            ("Speler", "De centrale muziekspeler", "De centrale speler is het gemeenschappelijke afspeelpunt van MusicVault. Verschillende onderdelen kunnen een nummer of Liveset starten, maar de daadwerkelijke audio wordt door de centrale speler verzorgd. Hierdoor kan de interface op verschillende pagina's toch dezelfde afspeelstatus volgen.", [
                ("Afspelen", "Start een track vanuit een bibliotheek, Showcase of Liveset. De pagina geeft het bestand door aan de speler, waarna de speler het audiobestand opent en begint af te spelen."),
                ("Actieve inhoud", "Pagina's kunnen naar de afspeelstatus van de centrale speler luisteren. Daardoor kan bijvoorbeeld een trackknop veranderen wanneer een nummer echt begint te spelen, in plaats van alleen wanneer iemand op een knop heeft gedrukt."),
                ("Livesets", "Voor Livesets is het belangrijk dat de speler het echte audiopad krijgt. De afspeelpagina kan vervolgens de titel en artiest van de geselecteerde Liveset tonen, terwijl de speler bepaalt welke audio daadwerkelijk actief is."),
                ("Als iets niet speelt", "Controleer eerst of het bestandspad nog bestaat en of het bestand door Windows geopend kan worden. Als dat in orde is, controleer dan de koppeling in MusicVault en probeer daarna opnieuw af te spelen."),
            ]),
            ("Livesets", "Livesets beheren", "Livesets zijn volledige DJ-sets met hun eigen titel, artiest, datum, locatie, duur, audio en cover. In de Livesetsbibliotheek beheer je deze informatie. Je kunt een nieuwe set toevoegen, bestaande gegevens aanpassen en het daadwerkelijke audiobestand opnieuw koppelen wanneer dat nodig is.", [
                ("Een nieuwe Liveset maken", "Maak een nieuwe Liveset aan wanneer je een set aan je collectie wilt toevoegen. Vul daarna de titel en artiest in en voeg, wanneer bekend, ook datum, locatie en duur toe. Niet ieder veld hoeft verplicht ingevuld te zijn om een Liveset te kunnen bewaren."),
                ("Audio koppelen", "Gebruik KIES AUDIO om het echte MP3- of audiobestand op je computer te selecteren. MusicVault bewaart het pad naar dat bestand. Het oorspronkelijke bestand wordt niet door de editor vervangen of naar een andere locatie verplaatst."),
                ("Opslaan", "Met OPSLAAN worden de gegevens van de geselecteerde Liveset naar de lokale Liveset-gegevens opgeslagen. Als je alleen het audiobestand kiest, wordt de koppeling eveneens bewaard. Controleer na een belangrijke wijziging even of de set opnieuw correct in de lijst verschijnt."),
                ("Cover toevoegen", "Gebruik VERVANG FOTO om een afbeelding aan de Liveset te koppelen. MusicVault kan de gekozen cover lokaal in zijn eigen Liveset-covermap bewaren, zodat je originele afbeelding niet afhankelijk blijft van de oorspronkelijke locatie."),
                ("Verwijderen", "Een Liveset verwijderen uit MusicVault betekent niet dat je oorspronkelijke MP3 automatisch moet verdwijnen. Controleer daarom altijd goed wat je verwijdert en bewaar audiobestanden die je ook buiten MusicVault gebruikt."),
            ]),
            ("Liveset afspelen", "Liveset Showcase en afspeelpagina", "De Liveset Showcase is de visuele ingang naar de echte afspeelpagina van een geselecteerde set. Daar komen de gegevens van de gekozen Liveset, de cover, de afspeelknop en de grote animatie samen. De bedoeling is dat de presentatie altijd overeenkomt met de set die je werkelijk hebt geopend en afgespeeld.", [
                ("Afspeelpagina", "Op de afspeelpagina zie je de cover, titel, artiest en andere beschikbare gegevens van de gekozen set. De afspeelknop gebruikt het audiobestand dat bij die specifieke Liveset is opgeslagen."),
                ("Grote animatie", "De animatie is bedoeld als visuele achtergrond voor het afspelen en gebruikt de ruimte van de pagina om de Liveset meer als een echte muziekervaring te presenteren. Ze staat los van de administratieve Livesetsbibliotheek."),
                ("Nu aan het spelen", "De tekst voor de actieve Liveset moet inhoudelijk aansluiten bij de Liveset die door de centrale speler wordt afgespeeld. Wanneer een andere set actief wordt, hoort de status dus niet bij een oude selectie te blijven hangen."),
                ("Wanneer de verkeerde naam verschijnt", "Controleer eerst welk audiobestand werkelijk door de centrale speler wordt afgespeeld en vergelijk dat met het audiopad van de geselecteerde Liveset. Het is belangrijker om de daadwerkelijke spelerstatus te volgen dan alleen de laatste muisklik."),
            ]),
            ("Covers", "Hoezen en afbeeldingen", "Covers zijn meer dan versiering: ze maken releases, CD's en Livesets onmiddellijk herkenbaar. MusicVault gebruikt afbeeldingen op verschillende plaatsen in de interface, terwijl de collectiegegevens zelf in de database of lokale gegevensbestanden worden bewaard.", [
                ("Toevoegen of vervangen", "Kies op de betreffende pagina een afbeelding wanneer je een cover wilt toevoegen of vervangen. Controleer na het kiezen of de juiste afbeelding zichtbaar is voordat je verdergaat."),
                ("Liveset-covers", "Voor Livesets worden gekozen afbeeldingen lokaal in de daarvoor bestemde covermap bewaard. Daardoor kan de afspeelpagina de afbeelding blijven tonen zonder dat het originele bronbestand op exact dezelfde plaats moet blijven staan."),
                ("Waarom niet handmatig opruimen", "Verwijder geen coverbestanden uit de programmamappen als je niet zeker weet waarnaar de collectie verwijst. Een afbeelding die er onbelangrijk uitziet, kan nog door een release of Liveset gebruikt worden."),
            ]),
            ("Discogs", "Discogs en gegevens verrijken", "Discogs kan nuttige externe informatie leveren over releases, artiesten en tracklijsten. Het is vooral waardevol wanneer je bestaande collectiegegevens wilt aanvullen of een release beter wilt identificeren. Discogs is echter een externe bron: je eigen collectiegegevens en lokale keuzes moeten altijd leidend blijven.", [
                ("Importeren", "Controleer voordat je een import uitvoert welke release je hebt geselecteerd en of het formaat, de artiest en de titel overeenkomen met je eigen exemplaar. Bij grote wijzigingen is het verstandig eerst te testen met een kleine, duidelijk herkenbare release."),
                ("Matchen", "Een goede match bestaat uit meer dan alleen dezelfde titel. Vergelijk waar mogelijk artiest, releasetitel, formaat, catalogusnummer, tracklijst en andere beschikbare kenmerken. Een toevallige titelovereenkomst is geen garantie dat je de juiste release hebt."),
                ("Lokale gegevens beschermen", "Gegevens die specifiek voor jouw collectie zijn toegevoegd, zoals een kastcode of lokale notitie, hebben een andere betekenis dan externe Discogs-metadata. Laat een externe import zulke lokale gegevens niet zonder controle overschrijven."),
                ("Bij twijfel", "Als twee Discogs-releases sterk op elkaar lijken, kies dan niet blind de eerste zoekresultaatoptie. Open de details en vergelijk de kenmerken van het fysieke exemplaar dat je werkelijk bezit."),
            ]),
            ("Instellingen", "Instellingen van MusicVault", "In Instellingen vind je de onderdelen waarmee je MusicVault afstemt op jouw computer en collectie. Omdat sommige instellingen rechtstreeks bepalen waar bestanden of databases worden gezocht, is het verstandig wijzigingen bewust en één voor één uit te voeren.", [
                ("Muziekbibliotheek", "Controleer waar je muziekbestanden staan en hoe MusicVault daarmee moet werken. Een verkeerde hoofdmap kan ervoor zorgen dat veel bestanden niet meer gevonden of gekoppeld lijken, terwijl de bestanden zelf nog gewoon op de computer aanwezig zijn."),
                ("Discogs", "Beheer hier de instellingen die nodig zijn voor Discogs. Wanneer een externe zoekactie niet werkt, controleer eerst deze instellingen voordat je aan de collectie zelf gaat wijzigen."),
                ("Database", "De database bevat belangrijke informatie over je collectie. Wijzig database-instellingen alleen wanneer je weet welk bestand of welke locatie bedoeld wordt. Een databaseprobleem kan meerdere onderdelen tegelijk beïnvloeden."),
                ("Na een instelling wijzigen", "Test na een belangrijke wijziging meteen een concrete functie. Als je bijvoorbeeld de muziekmap hebt aangepast, controleer dan direct of een bekende MP3 teruggevonden en afgespeeld kan worden."),
            ]),
            ("Veilig werken", "Je collectie veilig houden", "MusicVault bevat veel lokale informatie die in de loop van de tijd waardevol wordt: collectiegegevens, koppelingen, covers en instellingen. De veiligste manier van werken is daarom gecontroleerd veranderen, testen en pas daarna verdergaan.", [
                ("Voor grote wijzigingen", "Zorg dat MusicVault correct start en maak indien nodig eerst een backup van belangrijke lokale gegevens. Zeker bij database- of grote importbewerkingen is een herstelpunt veel waardevoller dan achteraf proberen te reconstrueren wat er veranderd is."),
                ("Niet zomaar verwijderen", "Verwijder de database, MP3-bestanden of covermappen niet omdat iets tijdelijk ontbreekt in een bibliotheek. Een ontbrekende verwijzing betekent niet automatisch dat het originele bestand of de collectiegegevens waardeloos zijn."),
                ("Originele muziek", "Behandel de oorspronkelijke MP3-, WAV- of andere audiobestanden als de bronbestanden van je collectie. MusicVault kan ernaar verwijzen, maar je hoeft ze niet te verwijderen of te verplaatsen om de database te onderhouden."),
                ("Na een wijziging", "Test precies de pagina en functie die je hebt aangepast. Een kleine controle direct na een wijziging voorkomt dat meerdere veranderingen zich opstapelen en later moeilijk te herleiden zijn."),
            ]),
            ("Problemen", "Veelvoorkomende problemen", "De meeste problemen zijn terug te brengen tot een verkeerd bestandspad, een ontbrekende koppeling, een niet opgeslagen wijziging of een configuratieprobleem. Kijk daarom eerst naar de concrete gegevens van het item voordat je grotere wijzigingen uitvoert.", [
                ("MP3 speelt niet", "Controleer of het bestand nog bestaat op het opgeslagen pad en of je het bestand buiten MusicVault kunt openen. Als het verplaatst is, stel de koppeling opnieuw in naar de juiste locatie en test daarna opnieuw."),
                ("Liveset speelt niet", "Open de Livesetsbibliotheek, kies de betreffende set en controleer het veld Audio bestand. Kies het audiobestand opnieuw, druk op OPSLAAN en open daarna de set opnieuw om te controleren of het juiste bestand wordt gebruikt."),
                ("De verkeerde Liveset staat bij Nu aan het spelen", "Controleer welke set geselecteerd is én welk audiobestand de centrale speler werkelijk heeft geopend. De afspeelstatus moet gebaseerd zijn op de actieve speler en niet alleen op de laatste selectie in de bibliotheek."),
                ("Cover ontbreekt", "Kies de cover opnieuw vanuit de editor van de betreffende release of Liveset. Controleer ook of het bestand een ondersteund afbeeldingsformaat heeft en na het kiezen zichtbaar wordt."),
                ("Programma start niet", "Start run_v3.py vanuit PowerShell en kijk naar de eerste duidelijke foutmelding. De eerste traceback-regel die naar een eigen Python-bestand verwijst is vaak de beste plaats om te beginnen; losse waarschuwingen van Qt zijn niet altijd een echte crash."),
            ]),
            ("Onderhoud", "Werken met de projectbestanden", "MusicVault wordt als softwareproject onderhouden met Git. Dat maakt het mogelijk om werkende versies te bewaren en wijzigingen gecontroleerd door te voeren. Voor normaal gebruik van MusicVault hoef je Git niet te bedienen, maar bij onderhoud of ontwikkeling is het belangrijk om de projectstatus te begrijpen.", [
                ("Voor nieuwe wijzigingen ophalen", "Controleer eerst of je lokale werkmap schoon is of dat je je eigen wijzigingen bewust hebt opgeslagen. Haal nooit blind nieuwe code op wanneer je lokale wijzigingen door een merge overschreven kunnen worden."),
                ("Na een wijziging", "Compileer het gewijzigde Python-bestand en start MusicVault om de betreffende functie te testen. Zo merk je snel of er een syntaxis- of importfout is voordat je verdergaat met andere onderdelen."),
                ("Bij een conflict", "Stop wanneer Git een conflict meldt en los het conflict eerst op. Een bestand met conflictmarkeringen zoals <<<<<<<, ======= of >>>>>>> is geen geldige Python-code en moet eerst correct worden samengevoegd."),
                ("Bij twijfel", "Verander niet tegelijk tien verschillende bestanden om één probleem op te lossen. Noteer eerst wat er fout gaat, bepaal welk onderdeel verantwoordelijk is en wijzig daarna zo gericht mogelijk."),
            ]),
            ("Over MusicVault", "Kid Acid's MusicVault V3", "MusicVault brengt je fysieke collectie, digitale muziek en Livesets samen in één lokale muziekomgeving. Het programma combineert collectiebeheer met artwork, metadata, MP3-koppelingen, afspelen en visuele Showcases, zodat je collectie zowel praktisch als aantrekkelijk bruikbaar blijft.", [
                ("Het uitgangspunt", "Je collectie blijft van jou. MusicVault is er om je muziek overzichtelijk te beheren, terug te vinden en te beluisteren zonder dat je oorspronkelijke audiobestanden hun normale plaats op je computer hoeven te verliezen."),
                ("Libraries en Showcases", "Gebruik de Libraries voor beheer, zoeken en controleren. Gebruik de Showcases wanneer je vooral wilt bladeren, artwork wilt bekijken en muziek wilt beleven. Beide kanten vullen elkaar aan en hoeven niet dezelfde informatie op dezelfde manier te tonen."),
                ("Een goede werkwijze", "Werk rustig en controleer wijzigingen meteen. Als een track speelt, een Liveset correct opent en je collectiegegevens kloppen, is er meestal geen reden om aan de onderliggende database te komen."),
                ("Veel plezier", "MusicVault is uiteindelijk geen database om naar te kijken, maar een manier om je muziekcollectie opnieuw te beleven. Gebruik de zoekfuncties wanneer je iets nodig hebt en de Showcases wanneer je gewoon zin hebt om door je muziek te bladeren."),
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
