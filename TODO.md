# NAHS-Brickserver / NAHS-TempBrick

## Server

*  **erledigt** Administrationsinterface -> möglichkeit zum setzen von werten zur laufzeit
*  **erledigt** Setzen einer Beschreibung für einen Brick (Name/Position)
*  Setzen einer Beschreibung für einen Sensor (Name/Position)
*  Brick(s) zu Gruppen zuweisen (Ortsbestimmung/Funktionsgruppen/...)
*  **erledigt** Feedback-Loop (Daten von Server an Brick übermitteln)
    *  **erledigt** Dynamisches Ändern des Sleep intervall
    *  **erledigt** Dynamisches Ändern der Präzession der Temperatursensoren
    *  **erledigt** Soll einmal am Tag nach der Akku Spannung fragen
*  **erledigt** Telegram Brücke
*  **erledigt** Nachricht per Telegram wenn Brick über längere Zeit keine Messwerte schickt (Akku leer?)
*  **erledigt** Nachricht per Telegram wenn der Akku unter einem gewissen Level ist (zB 3,5Volt)
*  **erledigt** temps array statt statischem temp wert für speicherung verwenden
*  **erledigt** konfiguration in conf.json auslagern (storagedir,...)
*  **erledigt** Returnvalue für cron-interface
*  **erledigt** Verschiedene Returnvalues für admin-Interface Fehler

## Brick

*  **erledigt** Config Interface (Initiales Setup speichert Daten in LittleFS)
    *  **erledigt** WiFi Config
    *  **erledigt** Server Config (IP und Port)
        *  im hintergrund DNS nach IP auflösen und IP speichern, sollte abfragen schneller machen - oder doch nur ein hinweis in der doku?
    *  **erledigt** Temperatursensoren Korrekturwerte
    *  **erledigt** Identify sensors - helper
    *  **erledigt** bat-adc kalibrierungs routine
*  **erledigt** Feedback-Loop (Daten von Server annehmen und in RCT-Memory speichern)
    *  **erledigt** JSON Parser über ArduinoJson
*  **erledigt** RTC Memory:
    *  **erledigt** delay
    *  **erledigt** präzession
    *  **erledigt** array der tempsensoren (dann müssen die id's nicht jedesmal abgefragt werden, was ja zeit kostet)
    *  **erledigt** requests von server, die durchgeführt werden sollen:
        *  **erledigt** bat-voltage
        *  **erledigt** version
        *  **erledigt** features
        *  precision
*  **erledigt** charging-state abfragen (und übermitteln)

## Brick und Server

*  **erledigt** map key auf einzelne zeichen beschränken (ist zwar blöd für leserlichkeit verkürzt aber generation und übertragungszeit)
*  Versionsnummer pro Feature (Interface) und nicht mehr pro Brick
*  BrickType als int also zB TempBrick = 1

## PCB:

*  **erledigt** USB (external power) kann entweder das system mit strom versorgen (zum beispiel beim konfigurieren der einstellungen über USB/UART)
oder kann wahlweise (jumper) verwendet werden um den verbauten akku zu laden (und so einen unterbrechungfreien betrieb bieten wenn rechtzeitig geladen wird)
*  **erledigt** AKKU direkt an LDO (mit Batt-Protection dazwischen natürlich) - kein step up auf 5V
