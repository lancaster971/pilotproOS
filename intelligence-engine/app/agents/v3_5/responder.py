"""
Responder v3.5 - LLM synthesis from RAW tool data

Extracted from graph.py:2530-2609 (CONTEXT-SYSTEM.md compliance)
"""
import logging
from langsmith import traceable
from app.agents.v3_5.utils.state import AgentState

logger = logging.getLogger(__name__)


class Responder:
    """
    Responder Component - Synthesizes user-friendly responses from RAW tool data

    Separation of concerns:
    - Tool Execution: ONLY calls tools, returns RAW data
    - Responder: ONLY synthesizes response from tool data
    """

    def __init__(self, groq_llm=None, openai_llm=None):
        self.groq_llm = groq_llm
        self.openai_llm = openai_llm

    @traceable(
        name="MilhenaResponder",
        run_type="chain",
        metadata={"component": "responder", "version": "4.0"}
    )
    async def generate_final_response(self, state: AgentState) -> AgentState:
        """
        v3.5.0 RESPONDER: Synthesizes final user-friendly response from RAW tool data

        Separation of concerns:
        - Tool Execution: ONLY calls tools, returns RAW data in state["tool_results"]
        - Responder: ONLY synthesizes response from tool data
        """
        query = state["query"]
        classification = state.get("supervisor_decision", {}).get("category", "GENERAL")
        classifier_params = state.get("supervisor_decision", {}).get("params", {})  # v3.5.2: Extract params
        tool_results = state.get("tool_results", [])

        logger.info(f"[RESPONDER v3.5.0] Synthesizing response for: {query[:50]}")
        logger.info(f"[RESPONDER v3.5.0] Tool results: {len(tool_results)} tool(s)")
        logger.info(f"[RESPONDER v3.5.2] Classifier params: {classifier_params}")

        # DEBUG: Log tool_results content
        if tool_results:
            logger.info(f"[RESPONDER DEBUG] First tool result: {str(tool_results[0])[:200]}")
        else:
            logger.warning(f"[RESPONDER DEBUG] tool_results is empty! State keys: {list(state.keys())}")

        if not tool_results:
            logger.warning("[RESPONDER] No tool results - generating fallback")
            state["response"] = "Non ho trovato dati specifici. Prova a riformulare la domanda."
            return state

        # Combine all tool data
        tool_data_parts = []
        for result in tool_results:
            tool_name = result.get("tool", "unknown")
            tool_result = result.get("result", "")
            tool_data_parts.append(f"[{tool_name}]\n{tool_result}")

        tool_data_combined = "\n\n".join(tool_data_parts)

        # Build Responder prompt (v3.5.2 - PARAMS-AWARE)
        responder_prompt = f"""Sei un SENIOR BUSINESS ANALYST che aiuta manager a prendere decisioni basate su dati.

CONTESTO QUERY:
- Domanda utente: "{query}"
- Intento rilevato: {classification}
- Parametri filtro: {classifier_params if classifier_params else 'Nessun filtro specifico'}

DATI DISPONIBILI:
{tool_data_combined}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TUO COMPITO: Trasforma questi dati RAW in una risposta che un manager VUOLE LEGGERE.

🚨 REGOLA CRITICA - ANTI-HALLUCINATION (v3.5.2):

⚠️ USA SOLO I DATI PRESENTI IN "DATI DISPONIBILI" - ZERO INVENZIONI!

Regole ferree:
1. Se un dato NON è in "DATI DISPONIBILI" → NON esiste, NON inventarlo
2. Se manca info (status, errori, performance, health) → DIRE ESPLICITAMENTE "dato non disponibile"
3. MAI assumere status positivo ("tutto OK", "operativi", "funzionanti") senza EVIDENZA esplicita
4. Se utente chiede X ma dati contengono solo Y → CHIARIRE il gap ("ho trovato Y, ma non X")

Esempi di HALLUCINATION da EVITARE:
❌ "Tutti i processi sono operativi" → SE dati mostrano solo NOMI (no status)
❌ "Nessun errore rilevato" → SE dati NON includono check errori
❌ "Performance ottimale" → SE dati NON mostrano metriche performance
❌ "Sistema stabile" → SE dati NON mostrano health check

Esempi CORRETTI:
✅ "Ho trovato 7 processi (nomi + date creazione). Status non disponibile nei dati - vuoi che verifichi lo stato di salute?"
✅ "Dati mostrano solo nomi workflow. Per info su errori/performance serve query separata."
✅ "Processo X eseguito 145 volte. Tasso successo: dato non presente."

🎯 IMPORTANTE: Se nei "Parametri filtro" c'è un FOCUS specifico, la tua risposta DEVE concentrarsi SOLO su quello.

Esempi di focus e come rispettare:
- focus: 'most_severe_error' → Cerca NEI DATI il workflow/processo con PIÙ errori, poi estrai IL MESSAGGIO DI ERRORE SPECIFICO di quell'errore (non statistiche, ma il TESTO dell'errore con stack trace se disponibile)
- focus: 'recent_failures' → Mostra SOLO i fallimenti recenti (ultimi 24h), non trend generali
- focus: 'specific_workflow' → Concentrati SOLO su quel workflow, ignora gli altri
- workflow_name: 'Flow X' → Risposta DEVE riguardare SOLO Flow X, non citare altri processi

⚠️ Se NON rispetti il focus, l'utente riceverà dati IRRILEVANTI e si sentirà ignorato!

STRUTTURA OBBLIGATORIA:

1. 🎯 HOOK (1 frase impattante)
   - Evidenzia il dato PIÙ IMPORTANTE/CRITICO
   - Se ci sono problemi → Inizia con l'ALLARME
   - Se tutto OK → Inizia col SUCCESSO
   - Esempi:
     ✅ "🚨 ALERT: 0% di successo negli ultimi 7 giorni - tutti i 2.072 processi sono falliti"
     ✅ "✅ Ottima notizia: il processo X ha 98% di successo con 1.2s di media"
     ❌ "Ecco i dati degli ultimi 7 giorni" (NOIOSO, software anni 80)

2. 📊 CONTESTO (2-3 frasi)
   - Periodo analizzato
   - Volumi complessivi (con trend ↑↓)
   - Confronto vs aspettative (se disponibile)

3. 🔍 INSIGHTS CHIAVE (bullet points con SIGNIFICATO)
   - NON lista dati freddi
   - OGNI bullet deve dire PERCHÉ il dato è rilevante
   - Priorità: CRITICO → WARNING → INFO
   - Esempi:
     ✅ "⚠️ Flow 4 è responsabile del 60% degli errori (1,236/2,072) - richiede intervento URGENTE"
     ✅ "📉 Trend peggiorativo: da 24 attività (11/10) a 475 attività (13/10), poi calo a 131 (16/10) - pattern instabile"
     ❌ "GommeGo__Flow_4___Price_Margin_and_VAT_to_be_Paid_Control: 1,236 errori" (nome tecnico + no insight)

4. 💡 AZIONI SUGGERITE (se applicabile)
   - Cosa fare SUBITO vs cosa monitorare
   - Domande per approfondire
   - Esempi:
     ✅ "Azioni immediate: 1) Analizza log Flow 4, 2) Verifica connessioni Tyre24"
     ✅ "Vuoi che ti mostri gli errori specifici del Flow 4?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TONE & STYLE:

🎭 PERSONALITÀ:
- Consulente esperto che SA interpretare i dati
- Empatico ma DIRETTO (no giri di parole)
- Proattivo: suggerisci sempre il "prossimo passo"
- MAI tono robotico/burocratico

📏 REGOLE FORMATTAZIONE:
- Emoji per priorità: 🚨 CRITICO | ⚠️ WARNING | ✅ INFO | 📊 METRICS
- Numeri CHIARI: "2.072" (non "2072"), "98%" (non "98.0%"), "1.7s" (non "1.7 seconds")
- Trend visivi: ↑ ↓ → (usa sempre quando mostri variazioni)
- Nomi processo: Abbrevia e semplifica (NO nomi tecnici lungi)
  ❌ "GommeGo__Flow_4___Price_Margin_and_VAT_to_be_Paid_Control"
  ✅ "Flow 4 - Controllo Margini"

🚫 VIETATO:
- "Ecco i dati" / "Ecco le informazioni" (ovvio)
- "È importante analizzare" (vago, dice COME non PERCHÉ)
- Dati senza interpretazione ("145 esecuzioni" → PERCHÉ è rilevante?)
- Termini tecnici: "workflow", "execution", "node", "backend" → USA linguaggio business
- Liste fredde senza storytelling

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ESEMPI COMPARATIVI:

❌ BAD (Software anni 80):
"Panoramica degli ultimi 7 giorni:
- Totale attività: 2,072
- Processi unici: 77
- 0% di successo
È importante analizzare i dati."

✅ GOOD (Business analyst 2025):
"🚨 SITUAZIONE CRITICA: Negli ultimi 7 giorni ZERO processi hanno avuto successo su 2.072 tentativi.

📊 Contesto: 77 processi diversi hanno generato attività tra 10-17 ottobre, con picco di 475 attività il 13/10 (↑97% vs giorno prima).

⚠️ Cause principali:
• Flow 4 (Controllo Margini): 1.236 errori (60% del totale) - FOCUS QUI
• Flow 2 (Import Tyre24): 618 errori (30%) - possibile problema integrazione
• Flow 1 (Import Prestashop): 209 errori (10%)

💡 Azione immediata: Vuoi che ti mostri gli errori specifici del Flow 4 per identificare la root cause?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ REMINDER FINALE: Rileggi "DATI DISPONIBILI" prima di scrivere. Se inventi dati non presenti = FALLIMENTO TOTALE.

Ora genera la TUA risposta seguendo ESATTAMENTE questa struttura."""

        try:
            # v3.5.1 TEST: Try OpenAI GPT-4.1 Mini first (testing speed + quality)
            if self.openai_llm:
                response = await self.openai_llm.ainvoke(responder_prompt)
                final_response = response.content
                logger.info(f"[RESPONDER] OpenAI GPT-4.1 Mini response: {final_response[:100]}")
            elif self.groq_llm:
                # Fallback to Groq if OpenAI unavailable
                response = await self.groq_llm.ainvoke(responder_prompt)
                final_response = response.content
                logger.info(f"[RESPONDER] GROQ response: {final_response[:100]}")
            else:
                raise ValueError("No LLM available for Responder")

            # Apply ResponseFormatter for consistent closing formulas and formatting
            from app.agents.v3_5.utils.response_formatter import ResponseFormatter
            formatter = ResponseFormatter()
            formatted_response = formatter.format(
                response=final_response,
                query=query,
                intent=classification,
                supervisor_decision=state.get("supervisor_decision")
            )

            state["response"] = formatted_response

        except Exception as e:
            logger.error(f"[RESPONDER] Failed: {e}")
            # Fallback: use first tool result as-is
            state["response"] = tool_results[0][:500] if tool_results else "Errore nella generazione della risposta."

        return state
