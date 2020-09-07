# NAHS-Brickserver / NAHS-TempBrick

## Server

*  Registrieren von Nodes (MAC zuordnung zu namen)
*  Nur registrierte Nodes erlauben (daten sammeln)
*  Feedback-Loop (Daten von Server an Node übermitteln)
    *  Dynamisches Ändern des Sleep intervall
    *  Dynamisches Ändern der Präzession der Temperatursensoren
    *  Dynamisches Ändern der Temperatursensoren Korrekturwerte??? sinnvoll??
    *  Soll einmal am Tag nach der Akku Spannung fragen
*  Telegram Brücke -> Auslagern in eigene Komponente? (Für spätere Integration in NAHS interessant)
*  Nachricht per Telegram wenn Node über längere Zeit keine Messwerte schickt (Akku leer?)
*  Nachricht per Telegram wenn der Akku unter einem gewissen Leven ist (zB 3,5Volt)
*  **erledigt** temps array statt statischem temp wert für speicherung verwenden
*  **erledigt** konfiguration in conf.json auslagern (storagedir,...)

## Brick

*  Config Interface (Initiales Setup speichert Daten in SPIFFS)
    *  WiFi Config
    *  Server Config (IP des Tempserver) - bewusst IP da DNS abfragen Zeit kosten dürften
    *  Temperatursensoren Korrekturwerte
*  Feedback-Loop (Daten von Server annehmen und in RCT-Memory speichern)

## Brick und Server

*  map key auf einzelne zeichen beschränken (ist zwar blöd für leserlichkeit verkürzt aber generation und übertragungszeit)

## PCB:

*  USB (external power) kann entweder das system mit strom versorgen (zum beispiel beim konfigurieren der einstellungen über USB/UART)
oder kann wahlweise (jumper) verwendet werden um den verbauten akku zu laden (und so einen unterprechungfreien betrieb bieten wenn rechtzeitig geladen wird)
*  AKKU direkt an LDO (mit Batt-Protection dazwischen natürlich) - kein step up auf 5V
