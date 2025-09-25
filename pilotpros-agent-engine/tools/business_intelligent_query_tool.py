"""
Business Intelligent Query Tool - Query intelligenti con traduzione automatica.
Analizza e traduce in linguaggio naturale eventi, errori e interazioni business.
"""

from typing import Dict, List, Optional
from crewai.tools import BaseTool
import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Logger più esplicito
logger = logging.getLogger("BusinessQueryTool")
logger.setLevel(logging.INFO)


class BusinessIntelligentQueryTool(BaseTool):
    """Tool per query intelligenti business-oriented con traduzione automatica"""

    name: str = "Business Query Intelligente"
    description: str = "Interroga i dati business e li traduce in linguaggio comprensibile"

    def __init__(self):
        super().__init__()
        try:
            self.translator = BusinessIntelligentTranslator()
        except Exception as e:
            logger.error(f"Impossibile inizializzare il translator: {e}")
            raise

    def _connect_db(self):
        """Connessione sicura al database con parametri da environment"""
        db_host = os.getenv("DB_HOST", "postgres-dev" if os.path.exists("/.dockerenv") else "localhost")

        try:
            import psycopg2
        except ImportError:
            raise ImportError("psycopg2 non installato. Installa con: pip install psycopg2-binary")

        return psycopg2.connect(
            host=db_host,
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME", "pilotpros_db"),
            user=os.getenv("DB_USER", "pilotpros_user"),
            password=os.getenv("DB_PASSWORD", "pilotpros_secure_pass_2025")
        )

    def _run(self, question: str = "Cosa è successo oggi?") -> str:
        """
        Risponde a domande business con linguaggio naturale

        Args:
            question: Domanda in linguaggio naturale

        Returns:
            Risposta in linguaggio business comprensibile
        """
        conn = None
        cursor = None

        try:
            # Connessione database refactored
            conn = self._connect_db()
            cursor = conn.cursor()

            # Analizza la domanda e rispondi
            response = self._analyze_and_respond(question, cursor)

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
                conn.close()

    def _analyze_and_respond(self, question: str, cursor) -> str:
        """Analizza domanda e genera risposta appropriata"""
        question_lower = question.lower()

        # Routing intelligente basato sulla domanda
        if "oggi" in question_lower or "today" in question_lower:
            return self._get_today_story(cursor)
        elif "email" in question_lower or "mail" in question_lower:
            return self._get_email_story(cursor)
        elif "ultimo" in question_lower or "last" in question_lower:
            return self._get_last_activity(cursor)
        elif "cliente" in question_lower or "customer" in question_lower:
            return self._get_customer_story(cursor, question)
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

    def _get_smart_overview(self, cursor) -> str:
        """Overview intelligente generale"""
        queries = {
            "active_workflows": "SELECT COUNT(*) FROM n8n.workflow_entity WHERE active = true",
            "total_workflows": "SELECT COUNT(*) FROM n8n.workflow_entity",
            "week_executions": "SELECT COUNT(*) FROM n8n.execution_entity WHERE \"startedAt\" >= CURRENT_DATE - INTERVAL '7 days'",
            "success_rate": """
                SELECT ROUND(
                    COUNT(CASE WHEN status = 'success' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 1
                ) FROM n8n.execution_entity WHERE \"startedAt\" >= CURRENT_DATE - INTERVAL '7 days'
            """,
            "unique_customers": """
                SELECT COUNT(DISTINCT email_sender)
                FROM pilotpros.business_execution_data
                WHERE email_sender IS NOT NULL
            """
        }

        stats = {}
        for key, query in queries.items():
            cursor.execute(query)
            result = cursor.fetchone()
            stats[key] = result[0] if result and result[0] is not None else 0

        response = "📊 **Dashboard Operativo**:\n\n"
        response += f"**Automazioni**: {stats['active_workflows']} attive su {stats['total_workflows']} totali\n"
        response += f"**Performance settimana**: {stats['week_executions']} operazioni, {stats['success_rate']}% successo\n"
        response += f"**Clienti serviti**: {stats['unique_customers']} totali\n\n"

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