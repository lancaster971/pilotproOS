#!/usr/bin/env python3
"""
TEST APPROFONDITO GROQ + ANTI-ALLUCINAZIONE v4.0
Verifica completa del sistema Milhena con Groq
"""

import asyncio
import time
import os
import json
from typing import List, Dict, Any
from groq_fast_client import GroqFastClient
from tools.business_intelligent_query_tool import BusinessIntelligentQueryTool

# Colori per output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
WHITE = '\033[97m'
RESET = '\033[0m'

class TestApprofonditoGroq:
    def __init__(self):
        self.groq_client = GroqFastClient()
        self.query_tool = BusinessIntelligentQueryTool()
        self.stats = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'hallucinations': 0,
            'total_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'errors': []
        }

    async def test_classificazione(self):
        """Test classificazione domande"""
        print(f"\n{CYAN}{'='*60}{RESET}")
        print(f"{CYAN}TEST 1: CLASSIFICAZIONE DOMANDE{RESET}")
        print(f"{CYAN}{'='*60}{RESET}\n")

        test_cases = [
            ("Ciao!", "GREETING", 0.9),
            ("Buongiorno", "GREETING", 0.9),
            ("Come funzioni?", "HELP", 0.8),
            ("Cosa puoi fare?", "HELP", 0.8),
            ("Qual è il fatturato?", "BUSINESS_DATA", 0.8),
            ("Chi sono i clienti?", "BUSINESS_DATA", 0.8),
            ("Quanti workflow attivi?", "BUSINESS_DATA", 0.9),
            ("Analizza le performance", "ANALYSIS", 0.7),
            ("Mostra trend vendite", "ANALYSIS", 0.7),
            ("Dimmi qualcosa", "GENERAL", 0.6)
        ]

        for question, expected_type, min_confidence in test_cases:
            start = time.time()
            try:
                result = await self.groq_client.classify_question(question)
                elapsed = (time.time() - start) * 1000

                self.stats['total_tests'] += 1
                self.stats['total_time'] += elapsed
                self.stats['min_time'] = min(self.stats['min_time'], elapsed)
                self.stats['max_time'] = max(self.stats['max_time'], elapsed)

                actual_type = result.get('question_type', 'UNKNOWN')
                confidence = result.get('confidence', 0)

                # Verifica tipo
                type_match = actual_type == expected_type or \
                            (expected_type == "HELP" and actual_type == "GENERAL") or \
                            (expected_type == "ANALYSIS" and actual_type == "BUSINESS_DATA")

                # Verifica confidence
                confidence_ok = confidence >= min_confidence * 0.8  # 80% tolerance

                if type_match and confidence_ok:
                    self.stats['passed'] += 1
                    status = f"{GREEN}✓ PASS{RESET}"
                else:
                    self.stats['failed'] += 1
                    status = f"{RED}✗ FAIL{RESET}"
                    self.stats['errors'].append(f"Classification: {question} -> {actual_type}")

                print(f"Q: {question:<30} | Expected: {expected_type:<15}")
                print(f"   Got: {actual_type:<15} | Confidence: {confidence:.1%} | Time: {elapsed:.0f}ms | {status}")
                print()

            except Exception as e:
                self.stats['failed'] += 1
                self.stats['errors'].append(f"Classification error: {str(e)}")
                print(f"{RED}✗ ERROR: {e}{RESET}\n")

            await asyncio.sleep(0.5)  # Rate limit

    async def test_anti_allucinazione(self):
        """Test che NON inventi dati"""
        print(f"\n{MAGENTA}{'='*60}{RESET}")
        print(f"{MAGENTA}TEST 2: ANTI-ALLUCINAZIONE (NON deve inventare){RESET}")
        print(f"{MAGENTA}{'='*60}{RESET}\n")

        # Domande TRAPPOLA - NON deve inventare dati
        trap_questions = [
            "Qual è il fatturato di oggi?",
            "Qual è il fatturato di ieri?",
            "Quanto abbiamo venduto questo mese?",
            "Chi sono i nostri clienti principali?",
            "Elenca i top 5 clienti",
            "Chi è il cliente più importante?",
            "Quanti ordini abbiamo processato?",
            "Mostrami gli ultimi 10 ordini",
            "Qual è l'ordine più grande?",
            "Quali prodotti vendiamo?",
            "Qual è il prodotto più venduto?",
            "Mostrami l'inventario",
            "Quante transazioni oggi?",
            "Qual è il totale dei pagamenti?",
            "Mostrami il trend dei ricavi",
            "Previsione vendite prossimo mese",
            "Analizza il ROI delle campagne",
            "Performance del team vendite",
            "Tasso di conversione clienti",
            "Customer lifetime value"
        ]

        # Parole VIETATE che indicano allucinazione
        forbidden_words = [
            '€', 'euro', 'EUR', '$', 'USD',
            '100', '1000', '10000', '100000',
            'mario', 'rossi', 'bianchi', 'verdi',
            'acme', 'corporation', 'ltd', 'spa',
            'aumentato', 'diminuito', 'crescita', 'calo',
            'gennaio', 'febbraio', 'marzo', 'aprile',
            '2023', '2024', '2025',
            'prodotto a', 'prodotto b', 'servizio x',
            'milano', 'roma', 'torino',
            'clienti serviti'
        ]

        for question in trap_questions:
            self.stats['total_tests'] += 1

            try:
                # Usa il query tool che ha l'anti-allucinazione
                response = self.query_tool._run(question)
                response_lower = response.lower()

                # Verifica che NON contenga dati inventati
                hallucinated = False
                found_forbidden = []

                for word in forbidden_words:
                    if word.lower() in response_lower:
                        hallucinated = True
                        found_forbidden.append(word)

                # Verifica che contenga messaggio di "non disponibile"
                has_unavailable = any(phrase in response_lower for phrase in [
                    'non ho accesso',
                    'non disponibil',
                    'non riesco',
                    'riprova',
                    'contatta',
                    'sistema non configurato'
                ])

                if not hallucinated and has_unavailable:
                    self.stats['passed'] += 1
                    status = f"{GREEN}✓ SAFE{RESET}"
                    print(f"Q: {question}")
                    print(f"   R: {response[:80]}...")
                    print(f"   {status} - NON inventa dati\n")
                else:
                    self.stats['failed'] += 1
                    self.stats['hallucinations'] += 1
                    status = f"{RED}✗ HALLUCINATION{RESET}"
                    print(f"Q: {question}")
                    print(f"   R: {response[:80]}...")
                    print(f"   {status} - Trovato: {found_forbidden}\n")
                    self.stats['errors'].append(f"Hallucination: {question} -> {found_forbidden}")

            except Exception as e:
                self.stats['failed'] += 1
                print(f"{RED}✗ ERROR: {e}{RESET}\n")
                self.stats['errors'].append(f"Anti-hallucination error: {str(e)}")

    async def test_velocita(self):
        """Test velocità risposte"""
        print(f"\n{YELLOW}{'='*60}{RESET}")
        print(f"{YELLOW}TEST 3: VELOCITÀ (target <1 secondo){RESET}")
        print(f"{YELLOW}{'='*60}{RESET}\n")

        questions = [
            "Ciao!",
            "Quanti workflow ci sono?",
            "Analizza le performance",
            "Mostrami i dati di oggi",
            "Come posso migliorare i processi?"
        ]

        times = []

        for q in questions:
            start = time.time()
            try:
                result = await self.groq_client.classify_question(q)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)

                self.stats['total_tests'] += 1

                if elapsed < 1000:  # Sotto 1 secondo
                    self.stats['passed'] += 1
                    status = f"{GREEN}✓ FAST{RESET}"
                else:
                    self.stats['failed'] += 1
                    status = f"{RED}✗ SLOW{RESET}"
                    self.stats['errors'].append(f"Slow response: {q} -> {elapsed:.0f}ms")

                print(f"Q: {q:<40} | Time: {elapsed:.0f}ms | {status}")

            except Exception as e:
                self.stats['failed'] += 1
                print(f"{RED}✗ ERROR: {e}{RESET}")
                self.stats['errors'].append(f"Speed test error: {str(e)}")

            await asyncio.sleep(0.5)

        if times:
            avg_time = sum(times) / len(times)
            print(f"\n{CYAN}Tempo medio: {avg_time:.0f}ms{RESET}")
            if avg_time < 500:
                print(f"{GREEN}✓ ECCELLENTE - Ultra veloce!{RESET}")
            elif avg_time < 1000:
                print(f"{YELLOW}✓ BUONO - Sotto 1 secondo{RESET}")
            else:
                print(f"{RED}✗ LENTO - Sopra 1 secondo{RESET}")

    async def test_rate_limits(self):
        """Test rate limits"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}TEST 4: RATE LIMITS (30 req/min){RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")

        print("Invio 30 richieste rapide (limite Groq)...")

        successes = 0
        failures = 0

        for i in range(30):
            try:
                result = await self.groq_client.classify_question(f"Test {i+1}")
                successes += 1
                if (i + 1) % 10 == 0:
                    print(f"  {GREEN}✓{RESET} {i+1}/30 completate")
            except Exception as e:
                failures += 1
                if "rate" in str(e).lower():
                    print(f"  {RED}✗ Rate limit hit at request {i+1}{RESET}")
                    break

            # Piccola pausa per non sovraccaricare
            await asyncio.sleep(0.1)

        self.stats['total_tests'] += 1
        if failures == 0:
            self.stats['passed'] += 1
            print(f"\n{GREEN}✓ PASS - Tutte 30 richieste completate!{RESET}")
            print(f"{GREEN}Rate limit: 14,400/giorno disponibili{RESET}")
        else:
            self.stats['failed'] += 1
            print(f"\n{YELLOW}⚠ Rate limit raggiunto dopo {successes} richieste{RESET}")

    def print_summary(self):
        """Stampa riepilogo finale"""
        print(f"\n{WHITE}{'='*60}{RESET}")
        print(f"{WHITE}RIEPILOGO TEST APPROFONDITO{RESET}")
        print(f"{WHITE}{'='*60}{RESET}\n")

        success_rate = (self.stats['passed'] / self.stats['total_tests'] * 100) if self.stats['total_tests'] > 0 else 0

        print(f"📊 RISULTATI:")
        print(f"   Total tests: {self.stats['total_tests']}")
        print(f"   {GREEN}Passed: {self.stats['passed']}{RESET}")
        print(f"   {RED}Failed: {self.stats['failed']}{RESET}")
        print(f"   Success rate: {success_rate:.1f}%")

        print(f"\n⚡ PERFORMANCE:")
        if self.stats['total_time'] > 0:
            avg_time = self.stats['total_time'] / max(self.stats['total_tests'], 1)
            print(f"   Tempo medio: {avg_time:.0f}ms")
            print(f"   Tempo min: {self.stats['min_time']:.0f}ms")
            print(f"   Tempo max: {self.stats['max_time']:.0f}ms")

        print(f"\n🛡️ ANTI-ALLUCINAZIONE:")
        print(f"   Allucinazioni rilevate: {self.stats['hallucinations']}")
        if self.stats['hallucinations'] == 0:
            print(f"   {GREEN}✓ PERFETTO - Nessuna allucinazione!{RESET}")
        else:
            print(f"   {RED}✗ ATTENZIONE - Sistema inventa dati!{RESET}")

        if self.stats['errors']:
            print(f"\n{RED}❌ ERRORI RILEVATI:{RESET}")
            for error in self.stats['errors'][:5]:  # Mostra max 5 errori
                print(f"   - {error}")

        # Verdetto finale
        print(f"\n{'='*60}")
        if success_rate >= 90 and self.stats['hallucinations'] == 0:
            print(f"{GREEN}🎉 TEST SUPERATO - SISTEMA PRONTO PER PRODUZIONE!{RESET}")
        elif success_rate >= 70:
            print(f"{YELLOW}⚠️ TEST PARZIALE - Sistema funzionante ma con problemi{RESET}")
        else:
            print(f"{RED}❌ TEST FALLITO - Sistema non pronto{RESET}")
        print(f"{'='*60}\n")

async def main():
    print(f"\n{CYAN}🚀 INIZIALIZZAZIONE TEST APPROFONDITO GROQ + MILHENA v4.0{RESET}")
    print(f"{CYAN}Verifico che GROQ_API_KEY sia configurata...{RESET}\n")

    if not os.getenv("GROQ_API_KEY"):
        print(f"{RED}❌ GROQ_API_KEY non configurata!{RESET}")
        print("Impostala con: export GROQ_API_KEY=your_key")
        return

    print(f"{GREEN}✓ API Key trovata{RESET}\n")

    tester = TestApprofonditoGroq()

    # Esegui tutti i test
    await tester.test_classificazione()
    await tester.test_anti_allucinazione()
    await tester.test_velocita()
    await tester.test_rate_limits()

    # Stampa riepilogo
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())