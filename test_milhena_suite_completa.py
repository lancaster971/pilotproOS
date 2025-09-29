#!/usr/bin/env python3
"""
🧪 MILHENA TEST SUITE COMPLETA
Test rigorosi con dati reali per validare completamente Milhena

Uso: python3 test_milhena_suite_completa.py
"""

import asyncio
import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import httpx

# Aggiungi path per import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'intelligence-engine'))

# Colori per output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

@dataclass
class TestResult:
    nome: str
    successo: bool
    tempo_ms: int
    dettagli: str
    errore: str = ""

class MilhenaTestSuite:
    """Suite completa di test per Milhena"""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.risultati: List[TestResult] = []
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def stampa_header(self):
        print(f"\n{Colors.CYAN}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.WHITE}🧪 MILHENA - SUITE TEST COMPLETA{Colors.END}")
        print(f"{Colors.WHITE}Test rigorosi con dati REALI per validazione totale{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}\n")

    def stampa_sezione(self, nome: str):
        print(f"{Colors.BLUE}{'─'*80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}📋 {nome}{Colors.END}")
        print(f"{Colors.BLUE}{'─'*80}{Colors.END}")

    async def test_endpoint_health(self) -> TestResult:
        """Test 1: Verifica che l'endpoint di Milhena sia raggiungibile"""
        start_time = time.time()
        nome = "Endpoint Health Check"

        try:
            response = await self.client.get(f"{self.base_url}/health")
            tempo = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                data = response.json()
                if "intelligence-engine" in data.get("service", ""):
                    return TestResult(nome, True, tempo, "Endpoint attivo e risponde correttamente")
                else:
                    return TestResult(nome, False, tempo, "Endpoint risponde ma servizio non riconosciuto", str(data))
            else:
                return TestResult(nome, False, tempo, f"Status code: {response.status_code}", response.text)

        except Exception as e:
            tempo = int((time.time() - start_time) * 1000)
            return TestResult(nome, False, tempo, "Endpoint non raggiungibile", str(e))

    async def test_milhena_api_diretta(self) -> List[TestResult]:
        """Test 2-6: Test API diretti di Milhena"""
        risultati = []

        test_cases = [
            {
                "nome": "Saluto Semplice",
                "message": "Ciao Milhena",
                "dovrebbe_contenere": ["ciao", "aiuto", "assistenza"],
                "non_dovrebbe_contenere": ["n8n", "postgres", "docker", "api"]
            },
            {
                "nome": "Richiesta Stato Sistema",
                "message": "Come va il sistema oggi?",
                "dovrebbe_contenere": ["sistema", "oggi"],
                "non_dovrebbe_contenere": ["workflow", "execution", "node"]
            },
            {
                "nome": "Query Business Data",
                "message": "Quante esecuzioni oggi?",
                "dovrebbe_contenere": ["elaborazioni", "processo"],
                "non_dovrebbe_contenere": ["execution", "n8n", "database"]
            },
            {
                "nome": "Richiesta Help",
                "message": "Aiutami a capire cosa puoi fare",
                "dovrebbe_contenere": ["aiuto", "posso", "fare"],
                "non_dovrebbe_contenere": ["technical", "api", "endpoint"]
            },
            {
                "nome": "Query Tecnica (deve deflettere)",
                "message": "Mostrami i database PostgreSQL",
                "dovrebbe_contenere": ["supporto", "tecnico"],
                "non_dovrebbe_contenere": ["postgres", "database", "sql"]
            }
        ]

        for test_case in test_cases:
            start_time = time.time()
            nome = f"API - {test_case['nome']}"

            try:
                payload = {
                    "message": test_case["message"],
                    "session_id": f"test-{int(time.time())}"
                }

                response = await self.client.post(f"{self.base_url}/api/chat", json=payload)
                tempo = int((time.time() - start_time) * 1000)

                if response.status_code == 200:
                    data = response.json()
                    risposta = data.get("response", "").lower()

                    # Controllo contenuto richiesto
                    contiene_richiesti = any(parola in risposta for parola in test_case["dovrebbe_contenere"])
                    non_contiene_proibiti = not any(parola in risposta for parola in test_case["non_dovrebbe_contenere"])

                    if contiene_richiesti and non_contiene_proibiti:
                        risultati.append(TestResult(nome, True, tempo, f"Risposta corretta: {risposta[:100]}..."))
                    else:
                        dettagli = f"Risposta: {risposta[:200]}..."
                        if not contiene_richiesti:
                            dettagli += f"\nManca contenuto richiesto: {test_case['dovrebbe_contenere']}"
                        if not non_contiene_proibiti:
                            dettagli += f"\nContiene termini proibiti: {test_case['non_dovrebbe_contenere']}"
                        risultati.append(TestResult(nome, False, tempo, dettagli))
                else:
                    risultati.append(TestResult(nome, False, tempo, f"HTTP {response.status_code}", response.text[:200]))

            except Exception as e:
                tempo = int((time.time() - start_time) * 1000)
                risultati.append(TestResult(nome, False, tempo, "Errore durante test", str(e)))

        return risultati

    async def test_n8n_integration(self) -> TestResult:
        """Test 7: Integrazione n8n"""
        start_time = time.time()
        nome = "Integrazione n8n"

        try:
            response = await self.client.get(f"{self.base_url}/api/n8n/agent/customer-support?message=test")
            tempo = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                data = response.json()
                if "response" in data and data.get("status") == "success":
                    risposta = data["response"].lower()
                    # Non deve contenere termini tecnici
                    termini_vietati = ["n8n", "workflow", "execution", "node", "postgres", "docker"]
                    ha_termini_vietati = any(termine in risposta for termine in termini_vietati)

                    if not ha_termini_vietati:
                        return TestResult(nome, True, tempo, "Integrazione n8n funziona con masking corretto")
                    else:
                        return TestResult(nome, False, tempo, "Risposta contiene termini tecnici", risposta)
                else:
                    return TestResult(nome, False, tempo, "Risposta non valida", str(data))
            else:
                return TestResult(nome, False, tempo, f"HTTP {response.status_code}", response.text[:200])

        except Exception as e:
            tempo = int((time.time() - start_time) * 1000)
            return TestResult(nome, False, tempo, "Errore integrazione n8n", str(e))

    async def test_masking_engine(self) -> List[TestResult]:
        """Test 8-10: Engine di masking"""
        risultati = []

        # Test diretto dell'engine di masking se accessibile
        try:
            from app.milhena.masking import TechnicalMaskingEngine
            masking = TechnicalMaskingEngine()

            test_cases = [
                {
                    "nome": "Masking Termini Base",
                    "input": "Il workflow n8n ha avuto un'execution con errore nel node PostgreSQL",
                    "dovrebbe_diventare": ["processo", "elaborazione", "passaggio", "database"]
                },
                {
                    "nome": "Masking URL e Tecnicismi",
                    "input": "API endpoint http://localhost:3001/api/workflows failed with 500 error",
                    "dovrebbe_diventare": ["interfaccia", "integrazione", "problema"]
                },
                {
                    "nome": "Masking JSON Complesso",
                    "input": {"workflow": "test", "execution": {"status": "failed", "node": "postgres"}},
                    "dovrebbe_diventare": ["processo", "elaborazione", "database"]
                }
            ]

            for test_case in test_cases:
                start_time = time.time()
                nome = f"Masking - {test_case['nome']}"

                try:
                    if isinstance(test_case["input"], str):
                        risultato = masking.mask(test_case["input"])
                    else:
                        risultato = masking.mask_json(test_case["input"])
                        risultato = str(risultato)

                    tempo = int((time.time() - start_time) * 1000)
                    risultato_lower = risultato.lower()

                    # Verifica che contenga termini business-friendly
                    ha_termini_business = any(termine in risultato_lower for termine in test_case["dovrebbe_diventare"])

                    # Verifica che non contenga più termini tecnici
                    termini_tecnici = ["n8n", "workflow", "execution", "node", "postgres", "api", "endpoint"]
                    ha_termini_tecnici = any(termine in risultato_lower for termine in termini_tecnici)

                    if ha_termini_business and not ha_termini_tecnici:
                        risultati.append(TestResult(nome, True, tempo, f"Masking corretto: {risultato[:100]}..."))
                    else:
                        dettagli = f"Input: {test_case['input']}\nOutput: {risultato}"
                        if not ha_termini_business:
                            dettagli += f"\nManca terminologia business"
                        if ha_termini_tecnici:
                            dettagli += f"\nContiene ancora termini tecnici"
                        risultati.append(TestResult(nome, False, tempo, dettagli))

                except Exception as e:
                    tempo = int((time.time() - start_time) * 1000)
                    risultati.append(TestResult(nome, False, tempo, "Errore nel masking", str(e)))

        except ImportError as e:
            risultati.append(TestResult("Masking Engine", False, 0, "Impossibile importare masking engine", str(e)))

        return risultati

    async def test_session_memory(self) -> TestResult:
        """Test 11: Memoria di sessione"""
        start_time = time.time()
        nome = "Memoria Sessione"
        session_id = f"test-memory-{int(time.time())}"

        try:
            # Prima richiesta con nome
            payload1 = {
                "message": "Mi chiamo Marco",
                "session_id": session_id
            }

            response1 = await self.client.post(f"{self.base_url}/api/chat", json=payload1)

            if response1.status_code != 200:
                return TestResult(nome, False, 0, "Prima richiesta fallita", response1.text)

            # Aspetta un attimo
            await asyncio.sleep(1)

            # Seconda richiesta per verificare memoria
            payload2 = {
                "message": "Come mi chiamo?",
                "session_id": session_id
            }

            response2 = await self.client.post(f"{self.base_url}/api/chat", json=payload2)
            tempo = int((time.time() - start_time) * 1000)

            if response2.status_code == 200:
                data = response2.json()
                risposta = data.get("response", "").lower()

                # Dovrebbe ricordare il nome Marco
                if "marco" in risposta:
                    return TestResult(nome, True, tempo, "Memoria di sessione funziona correttamente")
                else:
                    return TestResult(nome, False, tempo, f"Non ricorda il nome. Risposta: {risposta}")
            else:
                return TestResult(nome, False, tempo, f"HTTP {response2.status_code}", response2.text[:200])

        except Exception as e:
            tempo = int((time.time() - start_time) * 1000)
            return TestResult(nome, False, tempo, "Errore test memoria", str(e))

    async def test_performance_load(self) -> TestResult:
        """Test 12: Performance sotto carico"""
        start_time = time.time()
        nome = "Performance Load Test"

        try:
            # Esegue 5 richieste contemporaneamente
            tasks = []
            for i in range(5):
                payload = {
                    "message": f"Test carico {i}",
                    "session_id": f"load-test-{i}"
                }
                task = self.client.post(f"{self.base_url}/api/chat", json=payload)
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)
            tempo = int((time.time() - start_time) * 1000)

            successi = 0
            errori = 0

            for response in responses:
                if isinstance(response, Exception):
                    errori += 1
                elif hasattr(response, 'status_code') and response.status_code == 200:
                    successi += 1
                else:
                    errori += 1

            if successi >= 4:  # Almeno 4 su 5 devono funzionare
                return TestResult(nome, True, tempo, f"Load test OK: {successi}/5 successi in {tempo}ms")
            else:
                return TestResult(nome, False, tempo, f"Load test fallito: solo {successi}/5 successi", f"{errori} errori")

        except Exception as e:
            tempo = int((time.time() - start_time) * 1000)
            return TestResult(nome, False, tempo, "Errore load test", str(e))

    def stampa_risultato(self, risultato: TestResult):
        """Stampa il risultato di un singolo test"""
        icona = "✅" if risultato.successo else "❌"
        colore = Colors.GREEN if risultato.successo else Colors.RED

        print(f"{colore}{icona} {risultato.nome:<30} ({risultato.tempo_ms:>4}ms){Colors.END}")
        if risultato.dettagli:
            print(f"   {Colors.CYAN}→{Colors.END} {risultato.dettagli}")
        if risultato.errore:
            print(f"   {Colors.RED}⚠{Colors.END} {risultato.errore}")
        print()

    def stampa_sommario(self):
        """Stampa il sommario finale dei risultati"""
        print(f"\n{Colors.CYAN}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.WHITE}📊 SOMMARIO FINALE{Colors.END}")
        print(f"{Colors.CYAN}{'='*80}{Colors.END}\n")

        totali = len(self.risultati)
        successi = len([r for r in self.risultati if r.successo])
        fallimenti = totali - successi
        percentuale = (successi / totali * 100) if totali > 0 else 0

        tempo_totale = sum(r.tempo_ms for r in self.risultati)
        tempo_medio = tempo_totale / totali if totali > 0 else 0

        print(f"{Colors.GREEN}✅ Test Superati:  {successi:>3}/{totali}{Colors.END}")
        print(f"{Colors.RED}❌ Test Falliti:   {fallimenti:>3}/{totali}{Colors.END}")
        print(f"{Colors.YELLOW}📊 Percentuale:    {percentuale:>5.1f}%{Colors.END}")
        print(f"{Colors.BLUE}⏱️  Tempo Totale:   {tempo_totale:>5}ms{Colors.END}")
        print(f"{Colors.BLUE}⏱️  Tempo Medio:    {tempo_medio:>5.1f}ms{Colors.END}")

        # Stato finale
        if percentuale >= 90:
            stato = f"{Colors.GREEN}🎉 MILHENA COMPLETAMENTE FUNZIONALE{Colors.END}"
        elif percentuale >= 75:
            stato = f"{Colors.YELLOW}⚠️  MILHENA FUNZIONALE CON PROBLEMI MINORI{Colors.END}"
        else:
            stato = f"{Colors.RED}🚨 MILHENA HA PROBLEMI SIGNIFICATIVI{Colors.END}"

        print(f"\n{stato}\n")

        # Lista problemi se ce ne sono
        if fallimenti > 0:
            print(f"{Colors.RED}🔍 PROBLEMI RILEVATI:{Colors.END}")
            for risultato in self.risultati:
                if not risultato.successo:
                    print(f"   • {risultato.nome}: {risultato.dettagli}")
            print()

    async def esegui_tutti_i_test(self):
        """Esegue l'intera suite di test"""
        self.stampa_header()

        # Test 1: Health Check
        self.stampa_sezione("Test Infrastruttura")
        risultato = await self.test_endpoint_health()
        self.risultati.append(risultato)
        self.stampa_risultato(risultato)

        if not risultato.successo:
            print(f"{Colors.RED}⛔ Endpoint non raggiungibile. Interrompo i test.{Colors.END}")
            self.stampa_sommario()
            return

        # Test 2-6: API Diretti
        self.stampa_sezione("Test API Milhena")
        risultati_api = await self.test_milhena_api_diretta()
        self.risultati.extend(risultati_api)
        for risultato in risultati_api:
            self.stampa_risultato(risultato)

        # Test 7: Integrazione n8n
        self.stampa_sezione("Test Integrazione n8n")
        risultato_n8n = await self.test_n8n_integration()
        self.risultati.append(risultato_n8n)
        self.stampa_risultato(risultato_n8n)

        # Test 8-10: Masking Engine
        self.stampa_sezione("Test Masking Engine")
        risultati_masking = await self.test_masking_engine()
        self.risultati.extend(risultati_masking)
        for risultato in risultati_masking:
            self.stampa_risultato(risultato)

        # Test 11: Memoria Sessione
        self.stampa_sezione("Test Memoria e Sessioni")
        risultato_memoria = await self.test_session_memory()
        self.risultati.append(risultato_memoria)
        self.stampa_risultato(risultato_memoria)

        # Test 12: Performance
        self.stampa_sezione("Test Performance")
        risultato_performance = await self.test_performance_load()
        self.risultati.append(risultato_performance)
        self.stampa_risultato(risultato_performance)

        # Sommario finale
        self.stampa_sommario()

async def main():
    """Funzione principale"""
    print(f"{Colors.BOLD}Avvio suite test completa Milhena...{Colors.END}")

    async with MilhenaTestSuite() as suite:
        await suite.esegui_tutti_i_test()

if __name__ == "__main__":
    asyncio.run(main())