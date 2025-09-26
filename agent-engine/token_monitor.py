#!/usr/bin/env python3
"""
Token Monitor - Conteggio PRECISO dei token per non sforare MAI i limiti
Monitora GPT-4o (1M limit) e Groq fallback
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import tiktoken

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TokenMonitor")

class TokenMonitor:
    """Monitor PRECISO dei token per OpenAI e Groq"""
    
    def __init__(self):
        # LIMITI REALI MULTI-TIER (conservativi per sicurezza)
        self.limits = {
            "openai_premium": {
                "monthly_limit": 900000,  # 900K invece di 1M per sicurezza - GPT-4o
                "daily_limit": 30000,     # ~30K/giorno per distribuire bene
                "hourly_limit": 2000,     # ~2K/ora per evitare spike
                "model": "gpt-4o-2024-11-20",
                "use_case": "direct_responses"
            },
            "openai_mini": {
                "monthly_limit": 9000000,  # 9M invece di 10M per sicurezza - GPT-4o-mini
                "daily_limit": 300000,     # ~300K/giorno - ENORMISSIMO!
                "hourly_limit": 15000,     # ~15K/ora per multi-agente
                "model": "gpt-4o-mini-2024-07-18",
                "use_case": "multi_agent_complex"
            },
            "groq": {
                "daily_limit": 14000,     # Groq: 14K/giorno tipico
                "hourly_limit": 1000,     # ~1K/ora
                "model": "llama-3.3-70b-versatile",
                "use_case": "emergency_fallback"
            }
        }
        
        # Encoder per conteggio preciso token
        try:
            self.encoder = tiktoken.encoding_for_model("gpt-4o")
        except:
            self.encoder = tiktoken.get_encoding("cl100k_base")  # Fallback
        
        # Storage contatori (persistente in produzione)
        self.usage_file = "/tmp/token_usage.json"
        self.usage = self._load_usage()
        
        logger.info("✅ Token Monitor attivo - Limiti conservativi per sicurezza")

    def _load_usage(self) -> Dict[str, Any]:
        """Carica usage salvato (in produzione usare DB)"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    usage = json.load(f)
                    
                # Reset se è un nuovo giorno
                today = datetime.now().strftime("%Y-%m-%d")
                if usage.get("date") != today:
                    usage = self._reset_daily_usage()
                    
                return usage
        except Exception as e:
            logger.warning(f"Errore caricamento usage: {e}")
            
        return self._reset_daily_usage()

    def _reset_daily_usage(self) -> Dict[str, Any]:
        """Reset contatori giornalieri"""
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            "date": today,
            "openai_premium": {
                "daily_tokens": 0,
                "monthly_tokens": 0,
                "hourly_tokens": 0,
                "last_hour": datetime.now().hour,
                "requests": 0
            },
            "openai_mini": {
                "daily_tokens": 0,
                "monthly_tokens": 0,
                "hourly_tokens": 0,
                "last_hour": datetime.now().hour,
                "requests": 0
            },
            "groq": {
                "daily_tokens": 0,
                "hourly_tokens": 0,
                "last_hour": datetime.now().hour,
                "requests": 0
            }
        }

    def _save_usage(self):
        """Salva usage (in produzione usare DB)"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage, f, indent=2)
        except Exception as e:
            logger.error(f"Errore salvataggio usage: {e}")

    def count_tokens(self, text: str) -> int:
        """Conta token PRECISI"""
        try:
            return len(self.encoder.encode(text))
        except Exception as e:
            # Fallback: stima approssimativa (1 token ~= 4 chars)
            return len(text) // 4

    def can_use_provider(self, provider: str, estimated_tokens: int) -> Dict[str, Any]:
        """Verifica se si può usare il provider senza sforare"""
        
        current_hour = datetime.now().hour
        
        # Reset orario se necessario
        if self.usage[provider]["last_hour"] != current_hour:
            self.usage[provider]["hourly_tokens"] = 0
            self.usage[provider]["last_hour"] = current_hour

        limits = self.limits[provider]
        usage = self.usage[provider]
        
        # Verifica limiti
        checks = {
            "hourly_ok": usage["hourly_tokens"] + estimated_tokens <= limits["hourly_limit"],
            "daily_ok": usage["daily_tokens"] + estimated_tokens <= limits["daily_limit"]
        }
        
        if provider == "openai":
            checks["monthly_ok"] = usage["monthly_tokens"] + estimated_tokens <= limits["monthly_limit"]
            can_use = all(checks.values())
        else:
            can_use = checks["hourly_ok"] and checks["daily_ok"]

        # Calcola percentuali
        hourly_pct = (usage["hourly_tokens"] / limits["hourly_limit"]) * 100
        daily_pct = (usage["daily_tokens"] / limits["daily_limit"]) * 100
        
        result = {
            "can_use": can_use,
            "estimated_tokens": estimated_tokens,
            "hourly_usage": f"{usage['hourly_tokens']}/{limits['hourly_limit']} ({hourly_pct:.1f}%)",
            "daily_usage": f"{usage['daily_tokens']}/{limits['daily_limit']} ({daily_pct:.1f}%)",
            "checks": checks
        }
        
        if provider == "openai":
            monthly_pct = (usage["monthly_tokens"] / limits["monthly_limit"]) * 100
            result["monthly_usage"] = f"{usage['monthly_tokens']}/{limits['monthly_limit']} ({monthly_pct:.1f}%)"

        return result

    def record_usage(self, provider: str, input_tokens: int, output_tokens: int, success: bool = True):
        """Registra uso REALE dei token"""
        
        total_tokens = input_tokens + output_tokens
        
        if success:
            self.usage[provider]["hourly_tokens"] += total_tokens
            self.usage[provider]["daily_tokens"] += total_tokens
            self.usage[provider]["requests"] += 1
            
            if provider == "openai":
                self.usage[provider]["monthly_tokens"] += total_tokens
                
        self._save_usage()
        
        logger.info(f"📊 {provider.upper()}: +{total_tokens} token (in:{input_tokens}, out:{output_tokens})")

    def get_best_provider(self, estimated_tokens: int, task_type: str = "simple") -> str:
        """Sceglie il MIGLIOR provider per il tipo di task"""

        if task_type == "multi_agent" or estimated_tokens > 2000:
            # 1. TASK COMPLESSI: Prova GPT-4o-mini (10M token!)
            mini_check = self.can_use_provider("openai_mini", estimated_tokens)
            if mini_check["can_use"]:
                logger.info(f"🚀 GPT-4o-mini (10M) per multi-agente - Usage: {mini_check['daily_usage']}")
                return "openai_mini"

            # 2. Fallback GPT-4o premium se mini esaurito
            premium_check = self.can_use_provider("openai_premium", estimated_tokens)
            if premium_check["can_use"]:
                logger.warning(f"⚠️ Mini esaurito - Uso Premium per task complesso: {premium_check['daily_usage']}")
                return "openai_premium"
        else:
            # 1. TASK SEMPLICI: Prova GPT-4o premium (qualità suprema)
            premium_check = self.can_use_provider("openai_premium", estimated_tokens)
            if premium_check["can_use"]:
                logger.info(f"✅ GPT-4o Premium - Usage: {premium_check['daily_usage']}")
                return "openai_premium"

            # 2. Fallback GPT-4o-mini se premium esaurito
            mini_check = self.can_use_provider("openai_mini", estimated_tokens)
            if mini_check["can_use"]:
                logger.warning(f"⚠️ Premium esaurito - Uso Mini: {mini_check['daily_usage']}")
                return "openai_mini"

        # 3. EMERGENZA: Groq per tutto
        groq_check = self.can_use_provider("groq", estimated_tokens)
        if groq_check["can_use"]:
            logger.error(f"🚨 OpenAI esaurito - Groq emergency: {groq_check['daily_usage']}")
            return "groq"

        # 4. MASSIMA EMERGENZA: forza Groq
        logger.critical(f"🆘 TUTTI I LIMITI RAGGIUNTI! Forzo Groq")
        return "groq"

    def get_usage_report(self) -> Dict[str, Any]:
        """Report dettagliato usage"""
        
        report = {
            "date": self.usage["date"],
            "providers": {}
        }
        
        for provider in ["openai_premium", "openai_mini", "groq"]:
            check = self.can_use_provider(provider, 0)  # Check senza token aggiuntivi
            
            report["providers"][provider] = {
                "model": self.limits[provider]["model"],
                "requests_today": self.usage[provider]["requests"],
                "hourly_usage": check["hourly_usage"],
                "daily_usage": check["daily_usage"],
                "status": "🟢 OK" if check["can_use"] else "🔴 LIMIT",
                "limits": self.limits[provider]
            }
            
            if provider == "openai":
                report["providers"][provider]["monthly_usage"] = check["monthly_usage"]
                
        return report

# Singleton instance
_token_monitor = None

def get_token_monitor() -> TokenMonitor:
    """Ottieni istanza singleton"""
    global _token_monitor
    if _token_monitor is None:
        _token_monitor = TokenMonitor()
    return _token_monitor

# Test
if __name__ == "__main__":
    monitor = TokenMonitor()
    
    print("🧪 TEST TOKEN MONITOR")
    print("=" * 40)
    
    # Test conteggio token
    test_text = "Ciao! Come stai? Che tecnologie usate?"
    token_count = monitor.count_tokens(test_text)
    print(f"Text: '{test_text}'")
    print(f"Token count: {token_count}")
    
    # Test provider selection
    best = monitor.get_best_provider(token_count)
    print(f"Best provider: {best}")
    
    # Test usage recording
    monitor.record_usage(best, token_count, 50, True)
    
    # Report
    report = monitor.get_usage_report()
    print(f"\nUsage Report:")
    print(json.dumps(report, indent=2))
