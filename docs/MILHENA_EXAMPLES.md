# 💡 MILHENA - Practical Examples & Use Cases

**Esempi pratici reali di utilizzo del sistema Milhena Multi-Agent AI**

---

## 📋 **INDICE ESEMPI**

1. [Conversazioni Business Tipiche](#conversazioni-business-tipiche)
2. [Integrazione API](#integrazione-api)
3. [Sviluppo Custom](#sviluppo-custom)
4. [Automazioni Enterprise](#automazioni-enterprise)
5. [Dashboard & Reporting](#dashboard--reporting)
6. [Use Cases Avanzati](#use-cases-avanzati)

---

## 💬 **CONVERSAZIONI BUSINESS TIPICHE**

### **Scenario: Manager che controlla performance giornaliere**

```
👤 Manager: Buongiorno Milhena, come è andata ieri?

🤖 Milhena: Buongiorno! 📅 **Riepilogo di ieri**:

📩 Email gestite: 24 | 🧾 Ordini: 7 | 🤖 Interazioni AI: 45

**📋 Dettagli attività:**
• 08:30 - Mario Rossi ha scritto: 'Richiesta preventivo prodotto X'
• 09:15 - Ho risposto a Sara Bianchi
• 10:00 - Processato ordine #ORD-2025-001
• 11:30 - Cliente Premium ha richiesto supporto tecnico
• 14:45 - Completata analisi trend vendite automatica

Performance: 96% operazioni completate con successo ✅

👤 Manager: Ci sono stati problemi?

🤖 Milhena: ⚠️ **Analisi problemi ultima settimana**:

• Workflow "Gestione Ordini Premium": 2 errori
• Workflow "Email Marketing": 1 errore

Problemi risolti automaticamente. Consiglio di verificare la configurazione del workflow Premium per migliorare l'affidabilità.

👤 Manager: Mostrami il trend delle vendite

🤖 Milhena: 📈 **Analisi Trend Vendite**:

Basandomi sui dati degli ultimi workflow:
• Ordini questa settimana: +15% vs settimana precedente
• Valore medio ordine: €247 (+8%)
• Clienti attivi: 34 (+3 nuovi)

**Insight rilevanti**:
- Picco ordini nei giorni martedì-giovedì
- Prodotti categoria "Premium" in forte crescita
- Tasso conversione email: 12.3% (sopra media settore)

**Suggerimenti**:
- Aumentare campagne nei giorni di picco
- Focus su prodotti Premium nel marketing
- Ottimizzare follow-up automatici
```

### **Scenario: Team Support che diagnostica problemi**

```
👤 Support: Milhena, abbiamo segnalazioni di rallentamenti. Cosa sta succedendo?

🤖 Milhena: 🔍 **Analisi Performance Sistema**:

**⏱️ Tempi Risposta Attuali**:
• Workflow Email: 2.3s (normale: 1.8s) ⚠️
• Workflow Ordini: 4.1s (normale: 2.5s) ⚠️
• Workflow AI Agent: 1.2s (normale: 1.0s) ✅

**🔍 Cause Identificate**:
1. Database: Query lente su tabella ordini (indice mancante)
2. API Esterne: Timeout occasionali servizio pagamenti
3. Carico: +40% richieste vs media giornaliera

**🛠️ Azioni Suggerite**:
- Ottimizzare query database
- Implementare retry logic per API pagamenti
- Considerare scaling orizzontale nelle ore di picco

👤 Support: Quali workflow stanno fallendo di più?

🤖 Milhena: ❌ **Top Errori Ultima Settimana**:

1. **"Processamento Pagamenti"**: 12 errori
   - Causa: Timeout API Stripe
   - Soluzione: Aumentare timeout da 30s a 60s

2. **"Invio Email Marketing"**: 8 errori
   - Causa: Rate limit SMTP server
   - Soluzione: Implementare queue con delay

3. **"Sincronizzazione CRM"**: 5 errori
   - Causa: API key scaduta HubSpot
   - Soluzione: Rinnovare API key

**Priority**: Fix API Stripe (impatta revenue) 🔴
```

### **Scenario: CEO che vuole insights strategici**

```
👤 CEO: Milhena, dammi un quadro generale del business

🤖 Milhena: 📊 **Executive Dashboard**:

**🎯 KPI Chiave (Ultimo Mese)**:
• Revenue processi automatizzati: €24,350 (+18% MoM)
• Operazioni completate: 1,247 (94% success rate)
• Tempo risposta medio clienti: 12 minuti (-35% MoM)
• Costi operativi automation: €89 (-67% vs processo manuale)

**📈 Trend Positivi**:
• Automazione email: 89% messaggi gestiti automaticamente
• Customer satisfaction: 4.7/5 (era 4.2 pre-automation)
• Team productivity: +45% tempo liberato per attività strategiche

**🔮 Insights Predittivi**:
• Crescita ordini proiettata: +25% prossimo trimestre
• ROI automation attuale: 312%
• Break-even nuovo cliente: 2.3 mesi (era 4.1)

**💡 Raccomandazioni Strategiche**:
1. Espandere automation su processo "Customer Onboarding"
2. Investire in AI training per supporto L2
3. Implementare predictive analytics per inventory management

👤 CEO: Quali sono i rischi operativi maggiori?

🤖 Milhena: ⚠️ **Risk Assessment Operativo**:

**🔴 Rischi Alti**:
• **Single Point of Failure**: API Stripe (100% pagamenti)
  - Impact: €800/h revenue loss se down
  - Mitigation: Implementare failover PayPal

• **Data Dependency**: Database PostgreSQL unico
  - Impact: Stop completo operations
  - Mitigation: Setup replica + backup automatici

**🟡 Rischi Medi**:
• Dependency n8n Cloud: 15% workflows critici
• Rate limits API Google/Microsoft: picchi ore 10-12

**✅ Rischi Mitigati**:
• Multi-LLM strategy (Gemini+Groq) implementata
• Monitoring automatico con alerts
• Backup giornalieri + disaster recovery plan
```

---

## 🔌 **INTEGRAZIONE API**

### **Dashboard Real-time con React**

```typescript
// MilhenaChat.tsx
import React, { useState, useEffect } from 'react';

interface MilhenaResponse {
  success: boolean;
  response: string;
  question_type: string;
  response_time_ms: number;
  cached: boolean;
}

const MilhenaChat: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const askMilhena = async (question: string): Promise<MilhenaResponse> => {
    const response = await fetch('/api/assistant/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        user_id: 'dashboard_user',
        language: 'it'
      })
    });

    return response.json();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setMessages(prev => [...prev, { type: 'user', text: question }]);

    try {
      const result = await askMilhena(question);

      setMessages(prev => [...prev, {
        type: 'bot',
        text: result.response,
        metadata: {
          type: result.question_type,
          time: result.response_time_ms,
          cached: result.cached
        }
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        type: 'error',
        text: 'Errore di connessione. Riprova.'
      }]);
    }

    setQuestion('');
    setLoading(false);
  };

  // Auto-refresh business metrics ogni 30 secondi
  useEffect(() => {
    const interval = setInterval(async () => {
      const result = await askMilhena('Mostra KPI in tempo reale');
      // Aggiorna dashboard
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="milhena-chat">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.type}`}>
            <div className="content">{msg.text}</div>
            {msg.metadata && (
              <div className="metadata">
                {msg.metadata.type} • {msg.metadata.time}ms
                {msg.metadata.cached && ' • 💾 Cached'}
              </div>
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Chiedi a Milhena..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? '⏳' : '📤'}
        </button>
      </form>
    </div>
  );
};

export default MilhenaChat;
```

### **Webhook Integration per Alerts**

```python
# webhook_milhena_alerts.py
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import asyncio
from typing import Dict, Any

app = FastAPI()

class AlertRequest(BaseModel):
    alert_type: str
    threshold: str
    webhook_url: str

@app.post("/setup-alert")
async def setup_milhena_alert(alert: AlertRequest):
    """
    Setup di alert automatici basati su Milhena

    Esempi:
    - "Avvisami se gli ordini scendono sotto 10 al giorno"
    - "Alert se il success rate va sotto 90%"
    - "Notifica se ci sono più di 5 errori in un'ora"
    """

    # Configura monitoring
    monitoring_config = {
        'check_interval': 300,  # 5 minuti
        'alert_type': alert.alert_type,
        'threshold': alert.threshold,
        'webhook_url': alert.webhook_url
    }

    # Avvia background monitoring
    asyncio.create_task(monitor_milhena_metrics(monitoring_config))

    return {"status": "Alert configurato", "config": monitoring_config}

async def monitor_milhena_metrics(config: Dict):
    """Background task per monitoring continuo"""

    from agents.crews.milhena_orchestrator_enterprise import MilhenaEnterpriseOrchestrator
    milhena = MilhenaEnterpriseOrchestrator()

    while True:
        try:
            # Query Milhena per metriche specifiche
            if "ordini" in config['alert_type'].lower():
                result = await milhena.process_question(
                    "Quanti ordini abbiamo ricevuto oggi?",
                    user_id="monitoring_system"
                )

                # Parse risultato e verifica threshold
                orders_count = extract_orders_count(result['response'])
                threshold = int(config['threshold'].split()[0])

                if orders_count < threshold:
                    await send_webhook_alert(config['webhook_url'], {
                        'alert': f'Ordini giornalieri sotto soglia: {orders_count} < {threshold}',
                        'data': result['response'],
                        'timestamp': datetime.now().isoformat()
                    })

            elif "success rate" in config['alert_type'].lower():
                result = await milhena.process_question(
                    "Qual è il tasso di successo dei processi oggi?",
                    user_id="monitoring_system"
                )
                # ... logica similar per altri alert types

            await asyncio.sleep(config['check_interval'])

        except Exception as e:
            logger.error(f"Errore monitoring: {e}")
            await asyncio.sleep(60)  # Retry dopo 1 minuto

def extract_orders_count(response: str) -> int:
    """Estrai numero ordini dalla risposta Milhena"""
    import re
    match = re.search(r'(\d+)\s*ordini?', response.lower())
    return int(match.group(1)) if match else 0

async def send_webhook_alert(webhook_url: str, alert_data: Dict):
    """Invia alert via webhook"""
    import httpx

    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=alert_data)
```

### **Slack Bot Integration**

```python
# slack_milhena_bot.py
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
import os

app = AsyncApp(token=os.environ.get("SLACK_BOT_TOKEN"))

@app.message("milhena")
async def message_milhena(message, say):
    """
    Integrazione Slack: @milhena domanda business
    """

    # Estrai domanda dal messaggio
    text = message['text'].replace('milhena', '').strip()
    user_id = message['user']

    # Query Milhena
    from agents.crews.milhena_orchestrator_enterprise import MilhenaEnterpriseOrchestrator
    milhena = MilhenaEnterpriseOrchestrator()

    # Indica che sta "pensando"
    await say("🤔 Sto analizzando...")

    try:
        result = await milhena.process_question(
            question=text,
            user_id=f"slack_{user_id}",
            language="it"
        )

        # Formatta risposta per Slack
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🤖 *Milhena*: {result['response']}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"⏱️ {result['response_time_ms']:.0f}ms • 🏷️ {result['question_type']}"
                        + (" • 💾 Cache" if result.get('cached') else "")
                    }
                ]
            }
        ]

        await say(blocks=blocks)

    except Exception as e:
        await say(f"❌ Errore: {str(e)}")

@app.command("/business-summary")
async def business_summary_command(ack, respond):
    """Comando Slack per summary business giornaliero"""

    await ack()

    # Query multiple per dashboard completo
    milhena = MilhenaEnterpriseOrchestrator()

    queries = [
        "Cosa è successo oggi?",
        "Ci sono stati errori?",
        "Mostra le performance generali"
    ]

    responses = []
    for query in queries:
        result = await milhena.process_question(query, "slack_summary")
        responses.append(f"**{query}**\n{result['response']}\n")

    summary = "\n".join(responses)

    await respond({
        "response_type": "ephemeral",
        "text": f"📊 **Business Summary**\n\n{summary}"
    })

# Avvio bot
if __name__ == "__main__":
    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
```

---

## 🛠️ **SVILUPPO CUSTOM**

### **Custom Business Query Tool**

```python
# custom_sales_tool.py
from tools.business_intelligent_query_tool import BusinessIntelligentQueryTool

class CustomSalesQueryTool(BusinessIntelligentQueryTool):
    """
    Tool personalizzato per analytics vendite avanzate
    """

    name: str = "Advanced Sales Analytics"
    description: str = "Analisi vendite avanzate con KPI personalizzati"

    def _run(self, question: str) -> str:
        # Routing personalizzato per domande vendite
        if "conversion rate" in question.lower():
            return self._get_conversion_analytics()
        elif "customer lifetime value" in question.lower():
            return self._get_clv_analysis()
        elif "sales funnel" in question.lower():
            return self._get_funnel_analysis()
        else:
            # Fallback al comportamento standard
            return super()._run(question)

    def _get_conversion_analytics(self) -> str:
        """Analisi tassi conversione personalizzata"""

        query = """
        WITH conversion_funnel AS (
            SELECT
                DATE(created_at) as date,
                COUNT(CASE WHEN email_subject LIKE '%preventivo%' THEN 1 END) as quote_requests,
                COUNT(CASE WHEN order_id IS NOT NULL THEN 1 END) as orders,
                COUNT(CASE WHEN ai_response LIKE '%accettato%' THEN 1 END) as acceptances
            FROM pilotpros.business_execution_data
            WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(created_at)
        )
        SELECT
            date,
            quote_requests,
            orders,
            ROUND((orders::numeric / NULLIF(quote_requests, 0) * 100), 2) as conversion_rate
        FROM conversion_funnel
        WHERE quote_requests > 0
        ORDER BY date DESC
        """

        conn = self._connect_db()
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            return "📊 Dati conversione non disponibili per il periodo richiesto."

        response = "📈 **Analisi Conversion Rate (30 giorni)**:\n\n"

        total_quotes = sum(row[1] for row in results)
        total_orders = sum(row[2] for row in results)
        avg_conversion = (total_orders / total_quotes * 100) if total_quotes > 0 else 0

        response += f"**📊 Summary**:\n"
        response += f"• Richieste preventivi: {total_quotes}\n"
        response += f"• Ordini convertiti: {total_orders}\n"
        response += f"• Conversion rate medio: {avg_conversion:.1f}%\n\n"

        response += "**📅 Trend giornaliero**:\n"
        for row in results[:7]:  # Ultimi 7 giorni
            date, quotes, orders, conv_rate = row
            response += f"• {date}: {conv_rate:.1f}% ({orders}/{quotes})\n"

        # Insights automatici
        recent_conv = sum(row[3] for row in results[:7]) / 7
        older_conv = sum(row[3] for row in results[7:14]) / 7 if len(results) >= 14 else recent_conv

        if recent_conv > older_conv * 1.1:
            response += "\n✅ **Trend positivo**: Conversion rate in miglioramento!"
        elif recent_conv < older_conv * 0.9:
            response += "\n⚠️ **Alert**: Conversion rate in calo, analizza cause."

        conn.close()
        return response

    def _get_clv_analysis(self) -> str:
        """Customer Lifetime Value analysis"""

        query = """
        WITH customer_metrics AS (
            SELECT
                email_sender,
                COUNT(DISTINCT order_id) as total_orders,
                COALESCE(AVG(CAST(regexp_replace(ai_response, '[^0-9.]', '', 'g') AS NUMERIC)), 0) as avg_order_value,
                MIN(created_at) as first_order,
                MAX(created_at) as last_order,
                EXTRACT(DAYS FROM MAX(created_at) - MIN(created_at)) as customer_lifespan_days
            FROM pilotpros.business_execution_data
            WHERE order_id IS NOT NULL
              AND email_sender IS NOT NULL
            GROUP BY email_sender
            HAVING COUNT(DISTINCT order_id) > 0
        )
        SELECT
            email_sender,
            total_orders,
            ROUND(avg_order_value, 2) as avg_order_value,
            customer_lifespan_days,
            ROUND((avg_order_value * total_orders), 2) as total_clv
        FROM customer_metrics
        WHERE avg_order_value > 0
        ORDER BY total_clv DESC
        LIMIT 20
        """

        # ... implementazione simile
        return "📊 Customer Lifetime Value analysis results..."

# Integrazione nel sistema principale
def register_custom_tools():
    """Registra tools personalizzati nell'orchestrator"""

    from agents.crews.milhena_orchestrator_enterprise import MilhenaEnterpriseOrchestrator

    # Aggiungi tool personalizzato
    custom_tool = CustomSalesQueryTool()

    # Override del metodo di creazione tools
    original_create_tools = MilhenaEnterpriseOrchestrator._create_business_tools

    def _create_enhanced_tools(self):
        tools = original_create_tools(self)
        tools.append(custom_tool)
        return tools

    MilhenaEnterpriseOrchestrator._create_business_tools = _create_enhanced_tools
```

### **Custom Response Formatter**

```python
# custom_formatter.py
from typing import Dict, Any

class BusinessResponseFormatter:
    """
    Formatter personalizzato per risposte business
    """

    def __init__(self):
        self.templates = {
            'EXECUTIVE_SUMMARY': self._format_executive,
            'TECHNICAL_REPORT': self._format_technical,
            'CUSTOMER_FACING': self._format_customer
        }

    def format_response(self, response: str, format_type: str = 'STANDARD') -> str:
        """Formatta risposta secondo template richiesto"""

        formatter = self.templates.get(format_type)
        if formatter:
            return formatter(response)
        return response

    def _format_executive(self, response: str) -> str:
        """Template per executive summary"""

        # Estrai metriche chiave
        metrics = self._extract_metrics(response)

        formatted = "🎯 **EXECUTIVE SUMMARY**\n\n"

        # KPI Section
        if metrics:
            formatted += "📊 **KPI Chiave**:\n"
            for metric, value in metrics.items():
                formatted += f"• {metric}: {value}\n"
            formatted += "\n"

        # Main content
        formatted += "📋 **Dettagli**:\n"
        formatted += response

        # Action items
        actions = self._extract_action_items(response)
        if actions:
            formatted += "\n\n🎯 **Action Items**:\n"
            for i, action in enumerate(actions, 1):
                formatted += f"{i}. {action}\n"

        return formatted

    def _format_technical(self, response: str) -> str:
        """Template per report tecnici"""

        formatted = "🔧 **TECHNICAL REPORT**\n\n"
        formatted += f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        formatted += f"**Source**: Milhena AI Analytics\n\n"

        # Struttura tecnica
        formatted += "## Data Analysis\n"
        formatted += response

        # Aggiungi metadati tecnici
        formatted += "\n\n## Metadata\n"
        formatted += f"- Query execution time: {self._get_execution_time()}ms\n"
        formatted += f"- Data freshness: {self._get_data_freshness()}\n"
        formatted += f"- Confidence score: {self._calculate_confidence_score(response):.1%}\n"

        return formatted

    def _extract_metrics(self, text: str) -> Dict[str, str]:
        """Estrai metriche numeriche dal testo"""
        import re

        patterns = {
            'Email': r'(\d+)\s*email',
            'Ordini': r'(\d+)\s*ordini?',
            'Success Rate': r'(\d+(?:\.\d+)?)\s*%',
            'Revenue': r'[€$](\d+(?:,\d{3})*(?:\.\d{2})?)'
        }

        metrics = {}
        for label, pattern in patterns.items():
            match = re.search(pattern, text.lower())
            if match:
                metrics[label] = match.group(1)

        return metrics

# Integrazione nell'orchestrator
class EnhancedMilhenaOrchestrator(MilhenaEnterpriseOrchestrator):
    """Orchestrator con formatting personalizzato"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.formatter = BusinessResponseFormatter()

    async def process_question(self, question: str, **kwargs) -> Dict[str, Any]:
        # Processo standard
        result = await super().process_question(question, **kwargs)

        # Applica formatting personalizzato
        format_type = kwargs.get('format_type', 'STANDARD')
        if format_type != 'STANDARD':
            result['response'] = self.formatter.format_response(
                result['response'], format_type
            )
            result['formatted'] = True

        return result
```

---

## 🏢 **AUTOMAZIONI ENTERPRISE**

### **Automated Business Reports**

```python
# automated_reports.py
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

class MilhenaReportGenerator:
    """
    Generatore automatico di report business usando Milhena
    """

    def __init__(self):
        self.milhena = MilhenaEnterpriseOrchestrator()
        self.report_templates = {
            'daily': self._generate_daily_report,
            'weekly': self._generate_weekly_report,
            'monthly': self._generate_monthly_report,
            'incident': self._generate_incident_report
        }

    async def generate_scheduled_reports(self):
        """Genera e invia report automatici"""

        now = datetime.now()

        # Report giornaliero (alle 8:00)
        if now.hour == 8 and now.minute == 0:
            await self.send_daily_report()

        # Report settimanale (lunedì alle 9:00)
        if now.weekday() == 0 and now.hour == 9 and now.minute == 0:
            await self.send_weekly_report()

        # Report mensile (primo del mese alle 9:00)
        if now.day == 1 and now.hour == 9 and now.minute == 0:
            await self.send_monthly_report()

    async def _generate_daily_report(self) -> str:
        """Genera report giornaliero automatico"""

        queries = [
            "Cosa è successo ieri?",
            "Ci sono stati errori ieri?",
            "Quali sono state le performance di ieri?",
            "Quanti ordini abbiamo processato ieri?"
        ]

        report_sections = []

        for query in queries:
            try:
                result = await self.milhena.process_question(
                    question=query,
                    user_id="automated_reports",
                    format_type="EXECUTIVE_SUMMARY"
                )

                report_sections.append({
                    'title': self._query_to_title(query),
                    'content': result['response'],
                    'performance': result['response_time_ms']
                })

            except Exception as e:
                report_sections.append({
                    'title': 'Error',
                    'content': f'Errore generazione sezione: {str(e)}',
                    'performance': 0
                })

        # Compila report finale
        report = self._compile_report_html('Daily Business Report', report_sections)
        return report

    async def send_daily_report(self):
        """Invia report giornaliero via email"""

        report_html = await self._generate_daily_report()

        recipients = [
            'ceo@company.com',
            'manager@company.com',
            'sales@company.com'
        ]

        await self._send_email(
            subject=f"📊 Daily Business Report - {datetime.now().strftime('%Y-%m-%d')}",
            html_content=report_html,
            recipients=recipients
        )

    def _compile_report_html(self, title: str, sections: List[Dict]) -> str:
        """Compila report in formato HTML professionale"""

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #2196F3; color: white; padding: 20px; border-radius: 8px; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #2196F3; }}
                .performance {{ color: #666; font-size: 12px; }}
                .metrics {{ background: #f5f5f5; padding: 10px; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 {title}</h1>
                <p>Generated by Milhena AI • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """

        for section in sections:
            html += f"""
            <div class="section">
                <h2>{section['title']}</h2>
                <div class="metrics">
                    {self._format_html_content(section['content'])}
                </div>
                <p class="performance">⏱️ Generated in {section['performance']:.0f}ms</p>
            </div>
            """

        html += """
            <div class="footer">
                <p><em>This report was automatically generated by Milhena Multi-Agent AI System</em></p>
            </div>
        </body>
        </html>
        """

        return html

# Scheduler per automazioni
class BusinessAutomationScheduler:
    """Scheduler per automazioni business"""

    def __init__(self):
        self.report_generator = MilhenaReportGenerator()
        self.alert_system = MilhenaAlertSystem()
        self.running = False

    async def start_scheduler(self):
        """Avvia scheduler automazioni"""
        self.running = True

        while self.running:
            try:
                # Check report schedules
                await self.report_generator.generate_scheduled_reports()

                # Check alert conditions
                await self.alert_system.check_alert_conditions()

                # Check ogni minuto
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)

    def stop_scheduler(self):
        """Stop scheduler"""
        self.running = False

# Avvio automazioni
if __name__ == "__main__":
    scheduler = BusinessAutomationScheduler()
    asyncio.run(scheduler.start_scheduler())
```

### **Smart Alert System**

```python
# smart_alerts.py
from typing import List, Dict, Callable
from dataclasses import dataclass
from enum import Enum

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AlertRule:
    name: str
    query: str
    condition: Callable[[str], bool]
    severity: AlertSeverity
    cooldown_minutes: int = 60
    escalation_rules: List[str] = None

class MilhenaAlertSystem:
    """Sistema di alert intelligente basato su Milhena"""

    def __init__(self):
        self.milhena = MilhenaEnterpriseOrchestrator()
        self.alert_rules = self._setup_default_rules()
        self.alert_history = {}

    def _setup_default_rules(self) -> List[AlertRule]:
        """Setup regole alert predefinite"""

        return [
            AlertRule(
                name="Low Order Volume",
                query="Quanti ordini abbiamo ricevuto oggi?",
                condition=lambda response: self._extract_number(response, "ordini") < 5,
                severity=AlertSeverity.MEDIUM,
                cooldown_minutes=240,  # 4 ore
                escalation_rules=["sales_team", "management"]
            ),

            AlertRule(
                name="High Error Rate",
                query="Ci sono stati errori nelle ultime 2 ore?",
                condition=lambda response: "errori" in response.lower() and self._extract_number(response, "errori") > 10,
                severity=AlertSeverity.HIGH,
                cooldown_minutes=30,
                escalation_rules=["tech_team", "devops", "management"]
            ),

            AlertRule(
                name="System Performance Degradation",
                query="Come sono le performance del sistema oggi?",
                condition=lambda response: any(word in response.lower() for word in ["lento", "timeout", "rallentamento"]),
                severity=AlertSeverity.HIGH,
                cooldown_minutes=60,
                escalation_rules=["devops", "tech_lead"]
            ),

            AlertRule(
                name="Zero Revenue Day",
                query="Quanto abbiamo fatturato oggi?",
                condition=lambda response: self._extract_revenue(response) == 0 and datetime.now().hour > 10,
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=120,
                escalation_rules=["sales_team", "management", "ceo"]
            )
        ]

    async def check_alert_conditions(self):
        """Verifica tutte le condizioni di alert"""

        for rule in self.alert_rules:
            # Check cooldown
            if not self._is_cooldown_expired(rule.name, rule.cooldown_minutes):
                continue

            try:
                # Query Milhena
                result = await self.milhena.process_question(
                    question=rule.query,
                    user_id="alert_system"
                )

                # Valuta condizione
                if rule.condition(result['response']):
                    await self._trigger_alert(rule, result['response'])

            except Exception as e:
                logger.error(f"Alert check failed for {rule.name}: {e}")

    async def _trigger_alert(self, rule: AlertRule, response: str):
        """Trigger alert con escalation"""

        alert_data = {
            'rule_name': rule.name,
            'severity': rule.severity.value,
            'message': response,
            'timestamp': datetime.now().isoformat(),
            'escalation_level': 0
        }

        # Record alert
        self.alert_history[rule.name] = {
            'last_triggered': datetime.now(),
            'count': self.alert_history.get(rule.name, {}).get('count', 0) + 1
        }

        # Send initial alert
        await self._send_alert_notification(alert_data, rule.escalation_rules[0])

        # Schedule escalation if needed
        if len(rule.escalation_rules) > 1:
            asyncio.create_task(
                self._handle_escalation(alert_data, rule.escalation_rules)
            )

    async def _handle_escalation(self, alert_data: Dict, escalation_rules: List[str]):
        """Gestisce escalation automatica"""

        # Wait 15 minutes then escalate
        await asyncio.sleep(15 * 60)

        # Check if alert was resolved
        if not await self._is_alert_still_active(alert_data):
            return

        # Escalate to next level
        for i, escalation_target in enumerate(escalation_rules[1:], 1):
            alert_data['escalation_level'] = i
            await self._send_alert_notification(alert_data, escalation_target)

            # Wait between escalations
            if i < len(escalation_rules) - 1:
                await asyncio.sleep(30 * 60)  # 30 minutes

    def _extract_number(self, text: str, keyword: str) -> int:
        """Estrai numero dal testo associato a keyword"""
        import re

        pattern = rf'(\d+)\s*{keyword}'
        match = re.search(pattern, text.lower())
        return int(match.group(1)) if match else 0

    def _extract_revenue(self, text: str) -> float:
        """Estrai revenue dal testo"""
        import re

        patterns = [
            r'[€$](\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*[€$]'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1).replace(',', ''))

        return 0.0

# Sistema di notifiche
class NotificationSystem:
    """Sistema unificato per notifiche multi-canale"""

    CHANNELS = {
        'email': 'EmailChannel',
        'slack': 'SlackChannel',
        'teams': 'TeamsChannel',
        'sms': 'SMSChannel',
        'webhook': 'WebhookChannel'
    }

    async def send_notification(self, message: str, channel: str, target: str):
        """Invia notifica attraverso canale specificato"""

        channel_class = self.CHANNELS.get(channel)
        if not channel_class:
            raise ValueError(f"Unknown channel: {channel}")

        # Dynamically load and use channel
        channel_instance = globals()[channel_class]()
        await channel_instance.send(message, target)
```

---

## 📊 **DASHBOARD & REPORTING**

### **React Dashboard Component**

```typescript
// MilhenaDashboard.tsx
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface MilhenaMetrics {
  daily_orders: number;
  success_rate: number;
  response_time_avg: number;
  error_count: number;
  revenue: number;
}

const MilhenaDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<MilhenaMetrics | null>(null);
  const [historicalData, setHistoricalData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Real-time data fetching
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Query Milhena per metriche real-time
        const queries = [
          'Quanti ordini oggi?',
          'Qual è il success rate?',
          'Ci sono stati errori?',
          'Quanto abbiamo fatturato?'
        ];

        const responses = await Promise.all(
          queries.map(q => fetch('/api/assistant/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: q, user_id: 'dashboard' })
          }).then(r => r.json()))
        );

        // Parse responses
        const newMetrics: MilhenaMetrics = {
          daily_orders: extractNumber(responses[0].response, 'ordini'),
          success_rate: extractPercentage(responses[1].response),
          response_time_avg: 850, // From last API call
          error_count: extractNumber(responses[2].response, 'errori'),
          revenue: extractRevenue(responses[3].response)
        };

        setMetrics(newMetrics);

        // Update historical data
        const timestamp = new Date().toISOString().slice(0, 16);
        setHistoricalData(prev => [
          ...prev.slice(-23), // Keep last 24 hours
          { time: timestamp, ...newMetrics }
        ]);

      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchData();

    // Update every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="dashboard-loading">🤖 Milhena sta caricando i dati...</div>;
  }

  return (
    <div className="milhena-dashboard">
      <header className="dashboard-header">
        <h1>🤖 Milhena Business Intelligence</h1>
        <p>Real-time business insights • Ultimo aggiornamento: {new Date().toLocaleTimeString()}</p>
      </header>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <KPICard
          title="Ordini Oggi"
          value={metrics?.daily_orders || 0}
          trend={calculateTrend(historicalData, 'daily_orders')}
          color="#4CAF50"
          icon="🛒"
        />

        <KPICard
          title="Success Rate"
          value={`${metrics?.success_rate || 0}%`}
          trend={calculateTrend(historicalData, 'success_rate')}
          color="#2196F3"
          icon="✅"
        />

        <KPICard
          title="Response Time"
          value={`${metrics?.response_time_avg || 0}ms`}
          trend={calculateTrend(historicalData, 'response_time_avg', 'lower_is_better')}
          color="#FF9800"
          icon="⚡"
        />

        <KPICard
          title="Revenue"
          value={`€${metrics?.revenue || 0}`}
          trend={calculateTrend(historicalData, 'revenue')}
          color="#9C27B0"
          icon="💰"
        />
      </div>

      {/* Charts */}
      <div className="charts-container">
        <div className="chart-panel">
          <h3>📈 Trend Ordini (24h)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="daily_orders" stroke="#4CAF50" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-panel">
          <h3>⚡ Performance Sistema (24h)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Line yAxisId="left" type="monotone" dataKey="success_rate" stroke="#2196F3" />
              <Line yAxisId="right" type="monotone" dataKey="response_time_avg" stroke="#FF9800" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Live Chat */}
      <div className="live-chat-section">
        <h3>💬 Chatta con Milhena</h3>
        <MilhenaChat />
      </div>
    </div>
  );
};

// KPI Card Component
const KPICard: React.FC<{
  title: string;
  value: string | number;
  trend: 'up' | 'down' | 'stable';
  color: string;
  icon: string;
}> = ({ title, value, trend, color, icon }) => {
  const trendIcon = trend === 'up' ? '📈' : trend === 'down' ? '📉' : '➡️';
  const trendColor = trend === 'up' ? '#4CAF50' : trend === 'down' ? '#F44336' : '#757575';

  return (
    <div className="kpi-card" style={{ borderLeft: `4px solid ${color}` }}>
      <div className="kpi-header">
        <span className="kpi-icon">{icon}</span>
        <span className="kpi-title">{title}</span>
      </div>
      <div className="kpi-value" style={{ color }}>{value}</div>
      <div className="kpi-trend" style={{ color: trendColor }}>
        {trendIcon} {trend}
      </div>
    </div>
  );
};

// Utility functions
const extractNumber = (text: string, keyword: string): number => {
  const match = text.match(new RegExp(`(\\d+)\\s*${keyword}`, 'i'));
  return match ? parseInt(match[1]) : 0;
};

const extractPercentage = (text: string): number => {
  const match = text.match(/(\d+(?:\.\d+)?)\s*%/);
  return match ? parseFloat(match[1]) : 0;
};

const extractRevenue = (text: string): number => {
  const match = text.match(/[€$](\d+(?:,\d{3})*(?:\.\d{2})?)/);
  return match ? parseFloat(match[1].replace(',', '')) : 0;
};

const calculateTrend = (data: any[], key: string, direction: 'higher_is_better' | 'lower_is_better' = 'higher_is_better'): 'up' | 'down' | 'stable' => {
  if (data.length < 2) return 'stable';

  const recent = data.slice(-3).reduce((sum, item) => sum + item[key], 0) / 3;
  const older = data.slice(-6, -3).reduce((sum, item) => sum + item[key], 0) / 3;

  const threshold = 0.05; // 5% change threshold
  const change = (recent - older) / older;

  if (Math.abs(change) < threshold) return 'stable';

  const isImprovement = direction === 'higher_is_better' ? change > 0 : change < 0;
  return isImprovement ? 'up' : 'down';
};

export default MilhenaDashboard;
```

---

**💡 Milhena Examples & Use Cases - Powered by PilotProOS**
*Esempi pratici per massimizzare il valore del sistema AI*