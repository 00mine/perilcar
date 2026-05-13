# Errore build_app.bat — Soluzione

## Problema
Hai **Python 3.14** installato. PyWebView su Windows usa una libreria chiamata `pythonnet` che **non è ancora compatibile con Python 3.13/3.14**.

Risultato: l'installazione fallisce con `Failed building wheel for pythonnet`.

## Soluzione: installa Python 3.12

Python 3.12 è la versione **LTS stabile** raccomandata da Microsoft e supportata da tutte le librerie.

### Passi:

1. **Scarica Python 3.12.8** (versione stabile più recente della serie 3.12):
   https://www.python.org/downloads/release/python-3128/
   
   Scegli il file **Windows installer (64-bit)** — `python-3.12.8-amd64.exe`

2. **Installa** spuntando OBBLIGATORIAMENTE:
   - ☑️ **Add python.exe to PATH** (importantissimo!)
   - ☑️ **Install for all users** (consigliato)

3. **Verifica** in un nuovo prompt:
   ```cmd
   python --version
   ```
   Deve mostrare `Python 3.12.8`. Se mostra ancora 3.14, riavvia il PC.

4. **Disinstalla Python 3.14** (opzionale ma consigliato per evitare confusione):
   Pannello di Controllo → Programmi → Disinstalla Python 3.14

5. **Riprova la build**:
   ```cmd
   build_app.bat
   ```

## Domande frequenti

**Posso tenere entrambi i Python?**  
Sì, ma assicurati che `python --version` mostri 3.12. Se mostra 3.14, vai in *Variabili d'ambiente* e sposta Python 3.12 sopra Python 3.14 nel PATH.

**Devo reinstallare i dipendenti?**  
No — l'utente finale userà l'`.exe` che già contiene tutto incorporato. Python 3.12 serve solo a te per buildare.

**Perché non Python 3.13?**  
3.13 è uscito da poco e molte librerie non sono ancora compatibili. 3.12 è la scelta professionale (la userà Microsoft fino al 2028).
