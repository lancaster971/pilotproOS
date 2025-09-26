"""
Business Intelligent Query Tool - Query intelligenti con traduzione automatica.
Analizza e traduce in linguaggio naturale eventi, errori e interazioni business.
"""

from typing import Dict, List, Optional
import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from psycopg2 import pool
from functools import lru_cache
import time

load_dotenv()

# Connection pool globale per riutilizzo connessioni
_connection_pool = None

def get_connection_pool():
    """Get or create connection pool singleton"""
    global _connection_pool
    if _connection_pool is None:
        db_host = os.getenv("DB_HOST", "postgres-dev" if os.path.exists("/.dockerenv") else "localhost")
        _connection_pool = pool.SimpleConnectionPool(
            1, 5,  # min 1, max 5 connections
            host=db_host,
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME", "pilotpros_db"),
            user=os.getenv("DB_USER", "pilotpros_user"),
            password=os.getenv("DB_PASSWORD", "pilotpros_secure_pass_2025")
        )
        logger.info("✅ Connection pool inizializzato (1-5 connections)")
    return _connection_pool

# Import v3.0 anti-hallucination prompts
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from prompts.improved_prompts import VERBALIZER_TEMPLATES
    V3_PROMPTS_AVAILABLE = True
except ImportError:
    V3_PROMPTS_AVAILABLE = False

# Logger più esplicito
logger = logging.getLogger("BusinessQueryTool")
logger.setLevel(logging.INFO)
if V3_PROMPTS_AVAILABLE:
    logger.info("✅ V3.0 anti-hallucination prompts attivi")


class BusinessIntelligentQueryTool:
    """Tool per query intelligenti business-oriented - SENZA CREWAI!"""

    def __init__(self):
        self._cache_timestamp = None
        self._cached_overview = None
        self._cache_ttl = 60  # Cache per 60 secondi

    def _connect_db(self):
        """Ottieni connessione dal pool invece di crearne una nuova"""
        try:
            import psycopg2
        except ImportError:
            raise ImportError("psycopg2 non installato. Installa con: pip install psycopg2-binary")

        pool = get_connection_pool()
        conn = pool.getconn()
        logger.debug("📌 Connessione ottenuta dal pool")
        return conn

    def _return_connection(self, conn):
        """Restituisci connessione al pool invece di chiuderla"""
        if conn:
            pool = get_connection_pool()
            pool.putconn(conn)
            logger.debug("📌 Connessione restituita al pool")

    def run(self, question: str = "Cosa è successo oggi?") -> str:
        """
        Risponde a domande business con linguaggio naturale

        Args:
            question: Domanda in linguaggio naturale

        Returns:
            Risposta in linguaggio business comprensibile
        """
        import time
        start = time.time()
        conn = None
        cursor = None

        try:
            logger.info(f"⏳ START: Analisi domanda '{question[:50]}...'")

            # Connessione database refactored
            conn_start = time.time()
            conn = self._connect_db()
            cursor = conn.cursor()
            conn_time = time.time() - conn_start
            logger.info(f"✅ Connessione DB in {conn_time:.2f}s")

            # Analizza la domanda e rispondi
            analysis_start = time.time()
            response = self._analyze_and_respond(question, cursor)
            analysis_time = time.time() - analysis_start
            logger.info(f"📊 Analisi completata in {analysis_time:.2f}s")

            total_time = time.time() - start
            logger.info(f"🏁 TOTALE: {total_time:.2f}s")

            return response

        except ImportError as e:
            logger.error(f"Dipendenza mancante: {e}")
            return "⚠️ Sistema non configurato correttamente. Contatta l'amministratore."
        except Exception as e:
            logger.exception("Errore durante l'elaborazione della domanda business")
            return "📊 Al momento non riesco ad accedere ai dati. Riprova tra poco."
        finally:
            if cursor:
                cursor.close()
            if conn:
                self._return_connection(conn)  # Restituisce al pool invece di chiudere

    def _analyze_and_respond(self, question: str, cursor) -> str:
        """Analizza domanda e genera risposta appropriata"""
        question_lower = question.lower()

        # V3.0: BLOCCO PREVENTIVO per dati che NON abbiamo
        unsupported_keywords = {
            "fatturato": "dati di fatturato",
            "ricavi": "dati finanziari",
            "vendite": "dati di vendita",
            "revenue": "dati finanziari",
            "entrate": "dati finanziari",
            "clienti": "informazioni clienti",
            "cliente": "informazioni clienti",
            "customer": "informazioni clienti",
            "ordini": "dati ordini",
            "order": "dati ordini",
            "transazioni": "dati transazioni",
            "pagamenti": "dati pagamenti",
            "prodotti": "catalogo prodotti",
            "inventario": "dati inventario"
        }

        for keyword, data_type in unsupported_keywords.items():
            if keyword in question_lower:
                if V3_PROMPTS_AVAILABLE:
                    # Usa template v3.0
                    return "Non ho accesso a dati su {} nel sistema".format(data_type)
                else:
                    return f"❌ Non ho accesso a {data_type} nel sistema attuale. Posso mostrarti solo dati su workflow ed esecuzioni."

        # Routing intelligente basato sulla domanda
        if "oggi" in question_lower or "today" in question_lower:
            return self._get_today_story(cursor)
        elif "email" in question_lower or "mail" in question_lower:
            return self._get_email_story(cursor)
        elif "ultimo" in question_lower or "last" in question_lower:
            return self._get_last_activity(cursor)
        # V3.0: RIMOSSO gestione clienti - già bloccata sopra
        elif "problema" in question_lower or "error" in question_lower or "errore" in question_lower:
            return self._get_error_analysis(cursor)
        else:
            return self._get_smart_overview(cursor)

    def _get_today_story(self, cursor) -> str:
        """Racconta la storia di oggi"""
        query = """
            SELECT
                w.name as workflow_name,
                bed.node_name,
                bed.email_sender,
                bed.email_subject,
                LEFT(COALESCE(bed.email_content, bed.ai_response, ''), 200) as content,
                bed.order_id,
                e."startedAt"
            FROM pilotpros.business_execution_data bed
            JOIN n8n.execution_entity e ON bed.execution_id = e.id
            JOIN n8n.workflow_entity w ON bed.workflow_id = w.id
            WHERE DATE(e."startedAt") = CURRENT_DATE
                AND bed.show_tag IS NOT NULL
                AND (bed.email_subject IS NOT NULL
                     OR bed.ai_response IS NOT NULL
                     OR bed.order_id IS NOT NULL)
            ORDER BY e."startedAt" DESC
        """

        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            return "📅 Oggi non ci sono state ancora attività. Il sistema è pronto per nuove richieste!"

        stories = []
        email_count = 0
        order_count = 0
        ai_interactions = 0

        for row in results:
            workflow = row[0]
            node = row[1]
            sender = row[2]
            subject = row[3]
            content = row[4]
            order = row[5]
            time = row[6]

            if sender and subject:
                email_count += 1
                sender_name = sender.split('@')[0].replace('.', ' ').title()
                time_str = time.strftime("%H:%M") if time else ""

                if "Ricezione" in node:
                    stories.append(f"• {time_str} - {sender_name} ha scritto: '{subject}'")
                elif "Rispondi" in node:
                    stories.append(f"• {time_str} - Ho risposto a {sender_name}")

            if order:
                order_count += 1
                stories.append(f"• Processato ordine #{order}")

            if "AI" in node or "Agent" in node:
                ai_interactions += 1

        # Costruisci risposta narrativa migliorata
        response = f"📅 **Riepilogo di oggi**:\n\n"

        if stories:
            response += f"📩 Email gestite: {email_count} | 🧾 Ordini: {order_count} | 🤖 Interazioni AI: {ai_interactions}\n\n"
            response += "**📋 Dettagli attività:**\n"
            response += "\n".join(stories[:10])  # Max 10 storie

        return response

    def _get_email_story(self, cursor) -> str:
        """Racconta storia delle email"""
        query = """
            SELECT
                node_name,
                email_sender,
                email_subject,
                LEFT(email_content, 300) as content,
                execution_id
            FROM pilotpros.business_execution_data
            WHERE email_subject IS NOT NULL
                AND show_tag IS NOT NULL
            ORDER BY execution_id DESC
            LIMIT 5
        """

        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            return "📧 Non ci sono email recenti nel sistema."

        response = "📧 **Comunicazioni recenti**:\n\n"

        for row in results:
            node = row[0]
            sender = row[1] or "cliente"
            subject = row[2]
            content = row[3][:100] if row[3] else ""

            sender_name = sender.split('@')[0].replace('.', ' ').title() if '@' in sender else sender

            if "Ricezione" in node or "Trigger" in node:
                response += f"📨 **Da {sender_name}**: {subject}\n"
                if content:
                    response += f"   *\"{content}...\"*\n"
            else:
                response += f"📤 **Risposta inviata**: {subject}\n"

            response += "\n"

        return response

    def _get_last_activity(self, cursor) -> str:
        """Ultima attività in assoluto"""
        query = """
            SELECT
                w.name,
                bed.node_name,
                bed.email_subject,
                bed.ai_response,
                e."startedAt"
            FROM pilotpros.business_execution_data bed
            JOIN n8n.execution_entity e ON bed.execution_id = e.id
            JOIN n8n.workflow_entity w ON bed.workflow_id = w.id
            WHERE bed.show_tag IS NOT NULL
            ORDER BY e."startedAt" DESC
            LIMIT 1
        """

        cursor.execute(query)
        result = cursor.fetchone()

        if not result:
            return "Non ci sono attività recenti."

        workflow = result[0]
        node = result[1]
        subject = result[2]
        ai_response = result[3]
        time = result[4]

        time_str = time.strftime("%H:%M del %d/%m") if time else ""

        response = f"⏰ **Ultima attività** ({time_str}):\n\n"

        if subject:
            response += f"'{workflow}' ha gestito un'attività: Email ricevuta → '{subject}'"
        elif ai_response:
            response += f"'{workflow}' ha elaborato una richiesta con l'assistente AI"
        else:
            response += f"'{workflow}' ha completato un'operazione business"

        return response

    def _get_customer_story(self, cursor, question: str) -> str:
        """Storia di un cliente specifico"""
        # Estrai nome cliente dalla domanda se possibile
        # Per ora risposta generica
        return "Per informazioni su un cliente specifico, specifica il nome o l'email."

    def _get_error_analysis(self, cursor) -> str:
        """Analisi problemi/errori"""
        query = """
            SELECT
                w.name,
                COUNT(*) as error_count
            FROM n8n.execution_entity e
            JOIN n8n.workflow_entity w ON e."workflowId" = w.id
            WHERE e.status = 'error'
                AND e."startedAt" >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY w.name
            ORDER BY error_count DESC
        """

        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            return "✅ Ottimo! Non ci sono stati errori negli ultimi 7 giorni."

        response = "⚠️ **Analisi problemi ultima settimana**:\n\n"

        for row in results:
            workflow = row[0]
            errors = row[1]
            response += f"• {workflow}: {errors} errori\n"

        response += "\nConsiglio di verificare questi processi per migliorare l'affidabilità."

        return response

    @lru_cache(maxsize=32)
    def _get_cached_query_result(self, query_hash: str, ttl: int = 60):
        """Cache helper con TTL per query ripetute"""
        # Nota: in produzione usare Redis o memcached
        return None  # Placeholder per cache

    def _get_smart_overview(self, cursor) -> str:
        """Overview intelligente generale - OTTIMIZZATA con CTE e CACHE"""
        import time

        # Controlla cache prima di eseguire query
        current_time = time.time()
        if (self._cache_timestamp and
            self._cached_overview and
            (current_time - self._cache_timestamp) < self._cache_ttl):
            logger.info(f"✨ Cache HIT! Risparmio query DB (TTL: {self._cache_ttl}s)")
            return self._cached_overview

        query_start = time.time()

        # SINGOLA QUERY OTTIMIZZATA con CTE invece di 5 query separate
        optimized_query = """
        WITH summary AS (
            SELECT
                COUNT(*) FILTER (WHERE active = true) AS active_workflows,
                COUNT(*) AS total_workflows
            FROM n8n.workflow_entity
        ),
        executions AS (
            SELECT
                COUNT(*) AS week_executions,
                ROUND(SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS success_rate
            FROM n8n.execution_entity
            WHERE "startedAt" >= CURRENT_DATE - INTERVAL '7 days'
        )
        SELECT
            s.active_workflows,
            s.total_workflows,
            e.week_executions,
            e.success_rate
        FROM summary s, executions e
        """

        cursor.execute(optimized_query)
        result = cursor.fetchone()

        stats = {
            "active_workflows": result[0] if result[0] is not None else 0,
            "total_workflows": result[1] if result[1] is not None else 0,
            "week_executions": result[2] if result[2] is not None else 0,
            "success_rate": result[3] if result[3] is not None else 0
        }

        query_time = time.time() - query_start
        logger.info(f"⚡ Query CTE ottimizzata in {query_time:.3f}s (vs 5 query separate)")

        # V3.0: Usa verbalizer e mostra SOLO dati reali
        if V3_PROMPTS_AVAILABLE:
            response = "Nei dati disponibili posso osservare:\n\n"
        else:
            response = "📊 **Dati reali dal sistema**:\n\n"

        response += f"**Workflow**: {stats['active_workflows']} attivi su {stats['total_workflows']} totali\n"
        response += f"**Esecuzioni (7 giorni)**: {stats['week_executions']} totali, {stats['success_rate']}% successo\n"
        # V3.0: RIMOSSO "Clienti serviti" - NON abbiamo questi dati!\n"

        # Aggiungi top workflow
        cursor.execute("""
            SELECT w.name, COUNT(e.id) as runs
            FROM n8n.workflow_entity w
            LEFT JOIN n8n.execution_entity e ON w.id = e."workflowId"
            WHERE w.active = true
            GROUP BY w.name
            ORDER BY runs DESC
            LIMIT 3
        """)
        top_workflows = cursor.fetchall()

        if top_workflows:
            response += "**Processi più attivi**:\n"
            for wf in top_workflows:
                response += f"• {wf[0]}: {wf[1]} esecuzioni\n"

        # Salva in cache prima di restituire
        self._cached_overview = response
        self._cache_timestamp = time.time()
        logger.info(f"💾 Response salvata in cache per {self._cache_ttl}s")

        return response


class BusinessIntelligentTranslator:
    """Classe helper per traduzioni - importata dal main tool file"""

    NODE_TRANSLATIONS = {
        "n8n-nodes-base.microsoftOutlookTrigger": "email ricevuta",
        "n8n-nodes-base.microsoftOutlook": "email inviata",
        "@n8n/n8n-nodes-langchain.agent": "assistente AI",
        "n8n-nodes-base.telegram": "messaggio Telegram",
        "@n8n/n8n-nodes-langchain.toolWorkflow": "strumento business",
        "@n8n/n8n-nodes-langchain.vectorStoreQdrant": "ricerca intelligente",
        "n8n-nodes-base.googleSheets": "foglio Excel",
        "n8n-nodes-base.postgres": "database aggiornato",
        "n8n-nodes-base.code": "elaborazione dati",
        "n8n-nodes-base.html": "contenuto web processato",
        "n8n-nodes-base.httpRequest": "richiesta web",
        "n8n-nodes-base.function": "funzione personalizzata",
        "n8n-nodes-base.set": "preparazione dati",
        "n8n-nodes-base.executeWorkflow": "processo integrato"
    }

    def humanize_node_name(self, node_type: str, node_name: str) -> str:
        """Traduce node type/name in descrizione umana"""
        if node_type in self.NODE_TRANSLATIONS:
            return self.NODE_TRANSLATIONS[node_type]
        return node_name.replace("_", " ").title()