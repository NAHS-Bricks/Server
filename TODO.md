# NAHS-Brickserver / NAHS-TempBrick

## Server

*  Administrationsinterface -> möglichkeit zum setzen von werten zur laufzeit (zB korrekturwerte des sensoren)
*  Registrieren von Nodes (MAC zuordnung zu namen)
*  Nur registrierte Nodes erlauben (daten sammeln)
*  Feedback-Loop (Daten von Server an Node übermitteln)
    *  **erledigt** Dynamisches Ändern des Sleep intervall
    *  Dynamisches Ändern der Präzession der Temperatursensoren
    *  Dynamisches Ändern der Temperatursensoren Korrekturwerte??? sinnvoll??
    *  **erledigt** Soll einmal am Tag nach der Akku Spannung fragen
*  Telegram Brücke -> Auslagern in eigene Komponente? (Für spätere Integration in NAHS interessant)
*  Nachricht per Telegram wenn Node über längere Zeit keine Messwerte schickt (Akku leer?)
*  Nachricht per Telegram wenn der Akku unter einem gewissen Level ist (zB 3,5Volt)
*  **erledigt** temps array statt statischem temp wert für speicherung verwenden
*  **erledigt** konfiguration in conf.json auslagern (storagedir,...)

## Brick

*  Config Interface (Initiales Setup speichert Daten in LittleFS)
    *  **erledigt** WiFi Config
    *  **erledigt** Server Config (IP und Port)
        *  im hintergrund DNS nach IP auflösen und IP speichern, sollte abfragen schneller machen - oder doch nur ein hinweis in der doku?
    *  **erledigt** Temperatursensoren Korrekturwerte
    *  **erledigt** Identify sensors - helper
    *  **erledigt** bat-adc kalibrierungs routine
*  Feedback-Loop (Daten von Server annehmen und in RCT-Memory speichern)
    *  **erledigt** JSON Parser über ArduinoJson
    *  setzen der korrekturwerte noch nicht realisiert, ist aber schon alles für vorbereitet nur die struktur der feedback-loop fehlt noch
*  **erledigt** RTC Memory:
    *  **erledigt** delay
    *  **erledigt** präzession
    *  **erledigt** array der tempsensoren (dann müssen die id's nicht jedesmal abgefragt werden, was ja zeit kostet)
    *  **erledigt** requests von server, die durchgeführt werden sollen:
        *  **erledigt** bat-voltage
        *  **erledigt** version
        *  **erledigt** features
*  **erledigt** charging-state abfragen (und übermitteln)

## Brick und Server

*  **erledigt** map key auf einzelne zeichen beschränken (ist zwar blöd für leserlichkeit verkürzt aber generation und übertragungszeit)

## PCB:

*  **erledigt** USB (external power) kann entweder das system mit strom versorgen (zum beispiel beim konfigurieren der einstellungen über USB/UART)
oder kann wahlweise (jumper) verwendet werden um den verbauten akku zu laden (und so einen unterbrechungfreien betrieb bieten wenn rechtzeitig geladen wird)
*  **erledigt** AKKU direkt an LDO (mit Batt-Protection dazwischen natürlich) - kein step up auf 5V
