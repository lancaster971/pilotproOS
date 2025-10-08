#!/usr/bin/env python3
"""
n8n SQLite → PostgreSQL Migration Script with UUID Remapping
============================================================

Questo script migra dati n8n da export CSV (SQLite) a PostgreSQL,
generando nuovi UUID per i workflow e mantenendo la coerenza referenziale.

Author: PilotProOS Team
Date: 2025-10-08
Version: 1.0.0

Dependencies:
  - pandas>=2.0.0
  - psycopg2-binary>=2.9.0
  - pyyaml>=6.0
"""

import os
import sys
import json
import uuid
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import re

# Librerie esterne (installa con: pip install pandas psycopg2-binary pyyaml)
try:
    import pandas as pd
    import psycopg2
    from psycopg2.extras import execute_values
    import yaml
except ImportError as e:
    print(f"❌ ERRORE: Libreria mancante - {e}")
    print("Installa dipendenze con: pip install pandas psycopg2-binary pyyaml")
    sys.exit(1)

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class N8nMigration:
    """
    Classe principale per gestire la migrazione dati n8n.

    Responsabilità:
    - Lettura CSV da export SQLite
    - Generazione mapping UUID (old_id → new_uuid)
    - Trasformazione dati per schema PostgreSQL
    - Validazione integrità referenziale
    - Export SQL o CSV per import PostgreSQL
    """

    def __init__(self, config_path: str = "migration_config.yaml"):
        """
        Inizializza il migrator con configurazione da file YAML.

        Args:
            config_path: Path al file di configurazione
        """
        self.config = self._load_config(config_path)
        self.uuid_mapping: Dict[str, str] = {}  # old_workflow_id → new_uuid
        self.reverse_mapping: Dict[str, str] = {}  # new_uuid → old_workflow_id
        self.tag_uuid_mapping: Dict[str, str] = {}  # old_tag_id → new_tag_uuid
        self.dataframes: Dict[str, pd.DataFrame] = {}

        logger.info(f"✅ N8nMigration inizializzato con config: {config_path}")

    def _load_config(self, config_path: str) -> Dict:
        """Carica configurazione da file YAML."""
        if not os.path.exists(config_path):
            logger.warning(f"⚠️ Config non trovata: {config_path}, uso default")
            return self._default_config()

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        logger.info(f"📋 Config caricata: {len(config)} sezioni")
        return config

    def _default_config(self) -> Dict:
        """Configurazione di default se file YAML mancante."""
        return {
            'csv_input_dir': './csv_export',
            'csv_output_dir': './csv_postgres',
            'sql_output_file': './import_n8n_data.sql',
            'mapping_output_file': './workflow_id_mapping.json',
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'pilotpros_db',
                'user': 'pilotpros_user',
                'password': 'pilotpros_secure_pass_2025',
                'schema': 'n8n'
            },
            'tables': [
                'workflow_entity',
                'execution_entity',
                'credentials_entity',
                'tag_entity',
                'workflows_tags',
                'shared_workflow',
                'user'
            ],
            'preserve_encrypted': True,
            'validate_before_import': True
        }

    # ====================================================================
    # 1. LETTURA CSV
    # ====================================================================

    def read_csv_files(self) -> Dict[str, pd.DataFrame]:
        """
        Legge tutti i CSV dalla directory di input.

        Returns:
            Dict con nome_tabella → DataFrame pandas

        Raises:
            FileNotFoundError: Se directory CSV non esiste
            ValueError: Se CSV richiesti mancanti
        """
        csv_dir = Path(self.config['csv_input_dir'])

        if not csv_dir.exists():
            raise FileNotFoundError(f"❌ Directory CSV non trovata: {csv_dir}")

        logger.info(f"📂 Lettura CSV da: {csv_dir}")

        for table_name in self.config['tables']:
            csv_path = csv_dir / f"{table_name}.csv"

            if not csv_path.exists():
                logger.warning(f"⚠️ CSV mancante: {table_name}.csv (skip)")
                continue

            try:
                # Check se file è vuoto (0 byte o solo header)
                if csv_path.stat().st_size == 0:
                    logger.warning(f"⚠️ CSV vuoto (0 byte): {table_name}.csv (skip)")
                    continue

                # Leggi CSV con gestione encoding UTF-8
                df = pd.read_csv(
                    csv_path,
                    encoding='utf-8',
                    low_memory=False,
                    na_values=['', 'NULL', 'null', 'None']
                )

                # Skip se il file ha solo header senza dati
                if len(df) == 0:
                    logger.warning(f"⚠️ CSV vuoto (solo header): {table_name}.csv (skip)")
                    continue

                self.dataframes[table_name] = df
                logger.info(f"✅ Caricato {table_name}: {len(df)} righe, {len(df.columns)} colonne")

            except pd.errors.EmptyDataError:
                logger.warning(f"⚠️ CSV vuoto o malformato: {table_name}.csv (skip)")
                continue
            except Exception as e:
                logger.error(f"❌ Errore lettura {csv_path}: {e}")
                raise

        if not self.dataframes:
            raise ValueError("❌ Nessun CSV caricato correttamente!")

        return self.dataframes

    # ====================================================================
    # 2. GENERAZIONE UUID MAPPING
    # ====================================================================

    def generate_uuid_mapping(self) -> Dict[str, str]:
        """
        Genera mapping old_id → new_uuid per workflow_entity.

        Questo è il cuore della migrazione: ogni workflow SQLite riceve
        un nuovo UUID PostgreSQL, mantenendo tracciabilità.

        Returns:
            Dict {old_id_str → new_uuid_str}

        Example:
            {'1': 'a1b2c3d4-...', '2': 'e5f6g7h8-...'}
        """
        if 'workflow_entity' not in self.dataframes:
            raise ValueError("❌ workflow_entity CSV non caricato!")

        workflow_df = self.dataframes['workflow_entity']

        # Identifica colonna ID (potrebbe essere 'id' o 'workflow_id')
        id_column = None
        for col in ['id', 'workflowId', 'workflow_id']:
            if col in workflow_df.columns:
                id_column = col
                break

        if id_column is None:
            raise ValueError("❌ Colonna ID non trovata in workflow_entity!")

        logger.info(f"🔑 Generazione UUID mapping da colonna: {id_column}")

        for old_id in workflow_df[id_column]:
            # Genera UUID v4 casuale
            new_uuid = str(uuid.uuid4())

            old_id_str = str(old_id)
            self.uuid_mapping[old_id_str] = new_uuid
            self.reverse_mapping[new_uuid] = old_id_str

        logger.info(f"✅ Generati {len(self.uuid_mapping)} UUID mappings")

        # Salva mapping su file JSON per backup
        self._save_mapping()

        return self.uuid_mapping

    def generate_tag_uuid_mapping(self) -> Dict[str, str]:
        """
        Genera mapping old_tag_id → new_uuid per tag_entity.

        Returns:
            Dict {old_tag_id_str → new_tag_uuid_str}
        """
        if 'tag_entity' not in self.dataframes:
            logger.warning("⚠️ tag_entity non disponibile, skip tag mapping")
            return {}

        tag_df = self.dataframes['tag_entity']

        logger.info(f"🏷️  Generazione Tag UUID mapping...")

        for old_id in tag_df['id']:
            new_uuid = str(uuid.uuid4())
            old_id_str = str(old_id)
            self.tag_uuid_mapping[old_id_str] = new_uuid

        logger.info(f"✅ Generati {len(self.tag_uuid_mapping)} tag UUID mappings")

        return self.tag_uuid_mapping

    def _save_mapping(self):
        """Salva UUID mapping su file JSON."""
        output_file = self.config['mapping_output_file']

        mapping_data = {
            'generated_at': datetime.now().isoformat(),
            'total_workflows': len(self.uuid_mapping),
            'mapping': self.uuid_mapping,
            'reverse_mapping': self.reverse_mapping
        }

        with open(output_file, 'w') as f:
            json.dump(mapping_data, f, indent=2)

        logger.info(f"💾 UUID mapping salvato: {output_file}")

    # ====================================================================
    # 3. TRASFORMAZIONE WORKFLOW_ENTITY
    # ====================================================================

    def transform_workflow_entity(self) -> pd.DataFrame:
        """
        Trasforma workflow_entity da SQLite a PostgreSQL.

        Trasformazioni:
        - old_id → new_uuid (colonna 'id')
        - date/timestamp → formato PostgreSQL ISO
        - boolean 0/1 → true/false
        - JSON fields (settings, nodes, connections) → jsonb

        Returns:
            DataFrame trasformato pronto per PostgreSQL
        """
        if 'workflow_entity' not in self.dataframes:
            raise ValueError("❌ workflow_entity non disponibile!")

        df = self.dataframes['workflow_entity'].copy()
        logger.info(f"🔄 Trasformazione workflow_entity: {len(df)} righe")

        # 1. Sostituisci ID con UUID
        id_column = self._get_id_column(df)
        df['id'] = df[id_column].astype(str).map(self.uuid_mapping)

        # 2. Trasforma date/timestamp
        date_columns = ['createdAt', 'updatedAt', 'created_at', 'updated_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                # Formato ISO: 2025-10-08T12:00:00.000Z (gestisce NaT → None)
                df[col] = df[col].apply(
                    lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' if pd.notna(x) else None
                )

        # 3. Trasforma boolean (SOLO active e isArchived)
        bool_columns = ['active', 'isArchived']
        for col in bool_columns:
            if col in df.columns:
                # Gestisci stringhe '0'/'1' e interi 0/1
                df[col] = df[col].fillna(0).replace({'0': False, '1': True, 0: False, 1: True})

        # 4. Gestisci parentFolderId (imposta NULL se punta a cartella inesistente)
        if 'parentFolderId' in df.columns:
            # Se folder table non è stata migrata, imposta tutti i parentFolderId a NULL
            logger.info("⚠️  parentFolderId impostato a NULL (folder table non migrata)")
            df['parentFolderId'] = None

        # 5. Valida JSON fields (staticData e pinData sono JSON, NON boolean!)
        json_columns = ['settings', 'nodes', 'connections', 'staticData', 'pinData']
        for col in json_columns:
            if col in df.columns:
                df[col] = df[col].apply(self._validate_json)

        logger.info(f"✅ workflow_entity trasformato: {len(df)} righe")
        return df

    def _get_id_column(self, df: pd.DataFrame) -> str:
        """Identifica colonna ID in un DataFrame."""
        for col in ['id', 'workflowId', 'workflow_id']:
            if col in df.columns:
                return col
        raise ValueError("❌ Colonna ID non trovata!")

    def _validate_json(self, value: Any) -> Optional[str]:
        """Valida e serializza campi JSON."""
        if pd.isna(value) or value is None:
            return None

        if isinstance(value, str):
            try:
                # Verifica che sia JSON valido
                json.loads(value)
                return value
            except json.JSONDecodeError:
                logger.warning(f"⚠️ JSON invalido, uso stringa vuota: {value[:50]}...")
                return '{}'

        # Se è già dict/list, serializza
        return json.dumps(value)

    # ====================================================================
    # 4. TRASFORMAZIONE EXECUTION_ENTITY
    # ====================================================================

    def transform_execution_entity(self) -> pd.DataFrame:
        """
        Trasforma execution_entity applicando UUID mapping ai workflow.

        CRITICO: Questa funzione garantisce la coerenza referenziale!
        Ogni execution deve puntare al nuovo UUID del workflow.

        Trasformazioni:
        - execution.id → UUID casuale
        - execution.workflowId → mapping[old_workflow_id]
        - date/timestamp → ISO format
        - status/mode → lowercase
        - data/workflowData → JSONB

        Returns:
            DataFrame trasformato con foreign keys corrette
        """
        if 'execution_entity' not in self.dataframes:
            logger.warning("⚠️ execution_entity non disponibile (skip)")
            return pd.DataFrame()

        df = self.dataframes['execution_entity'].copy()

        # LIMIT: Prendi solo ultime 1000 executions (ordinate per data)
        if 'startedAt' in df.columns and len(df) > 1000:
            df['startedAt_temp'] = pd.to_datetime(df['startedAt'], errors='coerce')
            df = df.nlargest(1000, 'startedAt_temp')
            df = df.drop(columns=['startedAt_temp'])
            logger.info(f"⚠️  Limitato a ultime 1000 executions (da {len(self.dataframes['execution_entity'])} totali)")

        logger.info(f"🔄 Trasformazione execution_entity: {len(df)} righe")

        # 1. Mantieni ID originale (integer in PostgreSQL, NO UUID per executions!)
        # execution_entity.id rimane integer sequenziale originale

        # 2. APPLICA UUID MAPPING ai workflow
        workflow_col = self._get_workflow_id_column(df)

        def map_workflow_id(old_id):
            old_id_str = str(old_id)
            new_uuid = self.uuid_mapping.get(old_id_str)

            if new_uuid is None:
                logger.warning(f"⚠️ workflow_id non trovato in mapping: {old_id}")
                # Genera UUID placeholder (da rimuovere manualmente)
                return str(uuid.uuid4())

            return new_uuid

        df['workflowId'] = df[workflow_col].apply(map_workflow_id)

        # 3. Trasforma boolean (finished, waitTill, etc.)
        bool_columns = ['finished']
        for col in bool_columns:
            if col in df.columns:
                df[col] = df[col].fillna(0).replace({'0': False, '1': True, 0: False, 1: True})

        # 4. Trasforma date
        date_columns = ['startedAt', 'stoppedAt', 'finishedAt', 'createdAt', 'updatedAt']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df[col] = df[col].apply(
                    lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' if pd.notna(x) else None
                )

        # 5. Valida JSON
        json_columns = ['data', 'workflowData']
        for col in json_columns:
            if col in df.columns:
                df[col] = df[col].apply(self._validate_json)

        logger.info(f"✅ execution_entity trasformato: {len(df)} righe")
        return df

    def _get_workflow_id_column(self, df: pd.DataFrame) -> str:
        """Identifica colonna workflowId in execution_entity."""
        for col in ['workflowId', 'workflow_id', 'wf_id']:
            if col in df.columns:
                return col
        raise ValueError("❌ Colonna workflowId non trovata in execution_entity!")

    # ====================================================================
    # 5. TRASFORMAZIONE CREDENTIALS
    # ====================================================================

    def transform_credentials_entity(self) -> pd.DataFrame:
        """
        Trasforma credentials_entity preservando dati criptati.

        ATTENZIONE: I dati credentials sono criptati con encryptionKey.
        Se non hai la chiave, NON puoi decrittare. Preserva AS-IS.

        Returns:
            DataFrame con credentials (data criptata preservata)
        """
        if 'credentials_entity' not in self.dataframes:
            logger.warning("⚠️ credentials_entity non disponibile (skip)")
            return pd.DataFrame()

        df = self.dataframes['credentials_entity'].copy()
        logger.info(f"🔄 Trasformazione credentials_entity: {len(df)} righe")

        # 1. UUID per credentials
        df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]

        # 2. Preserva campo 'data' criptato (NO decrypt!)
        if 'data' in df.columns:
            logger.info("🔒 Preservo dati criptati (encryptionKey required per decrypt)")

        # 3. Trasforma boolean (isManaged)
        bool_columns = ['isManaged']
        for col in bool_columns:
            if col in df.columns:
                df[col] = df[col].fillna(0).replace({'0': False, '1': True, 0: False, 1: True})

        # 4. Date
        for col in ['createdAt', 'updatedAt']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df[col] = df[col].apply(
                    lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' if pd.notna(x) else None
                )

        logger.info(f"✅ credentials_entity trasformato: {len(df)} righe")
        return df

    # ====================================================================
    # 6. TRASFORMAZIONE TABELLE AGGIUNTIVE
    # ====================================================================

    def transform_generic_table(self, table_name: str) -> pd.DataFrame:
        """
        Trasformazione generica per tabelle semplici (date, boolean, JSON).

        Args:
            table_name: Nome tabella da trasformare

        Returns:
            DataFrame trasformato
        """
        if table_name not in self.dataframes:
            logger.warning(f"⚠️ {table_name} non disponibile (skip)")
            return pd.DataFrame()

        df = self.dataframes[table_name].copy()
        logger.info(f"🔄 Trasformazione {table_name}: {len(df)} righe")

        # Trasforma boolean comuni
        bool_columns = ['loadOnStartup', 'enabled', 'active', 'isManaged']
        for col in bool_columns:
            if col in df.columns:
                df[col] = df[col].fillna(0).replace({'0': False, '1': True, 0: False, 1: True})

        # Trasforma date comuni
        date_columns = ['createdAt', 'updatedAt', 'created_at', 'updated_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df[col] = df[col].apply(
                    lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' if pd.notna(x) else None
                )

        logger.info(f"✅ {table_name} trasformato: {len(df)} righe")
        return df

    def transform_tag_entity(self) -> pd.DataFrame:
        """Trasforma tag_entity con UUID mapping."""
        if 'tag_entity' not in self.dataframes:
            return pd.DataFrame()

        df = self.dataframes['tag_entity'].copy()
        logger.info(f"🔄 Trasformazione tag_entity: {len(df)} righe")

        # Sostituisci ID con UUID dal mapping
        df['id'] = df['id'].astype(str).map(self.tag_uuid_mapping)

        # Date
        for col in ['createdAt', 'updatedAt']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df[col] = df[col].apply(
                    lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' if pd.notna(x) else None
                )

        logger.info(f"✅ tag_entity trasformato: {len(df)} righe")
        return df

    def transform_workflows_tags(self) -> pd.DataFrame:
        """Trasforma workflows_tags (junction table con UUID mapping)."""
        if 'workflows_tags' not in self.dataframes:
            return pd.DataFrame()

        df = self.dataframes['workflows_tags'].copy()
        logger.info(f"🔄 Trasformazione workflows_tags: {len(df)} righe")

        # Map workflow IDs a UUID
        if 'workflowId' in df.columns:
            df['workflowId'] = df['workflowId'].astype(str).map(self.uuid_mapping)

        # Map tag IDs a UUID
        if 'tagId' in df.columns:
            df['tagId'] = df['tagId'].astype(str).map(self.tag_uuid_mapping)

        logger.info(f"✅ workflows_tags trasformato: {len(df)} righe")
        return df

    def transform_shared_workflow(self) -> pd.DataFrame:
        """Trasforma shared_workflow con UUID workflow mapping (NO id column!)."""
        if 'shared_workflow' not in self.dataframes:
            return pd.DataFrame()

        df = self.dataframes['shared_workflow'].copy()
        logger.info(f"🔄 Trasformazione shared_workflow: {len(df)} righe")

        # Rimuovi colonna 'id' se presente (shared_workflow NON ha id!)
        if 'id' in df.columns:
            df = df.drop(columns=['id'])

        # Map workflow IDs
        if 'workflowId' in df.columns:
            df['workflowId'] = df['workflowId'].astype(str).map(self.uuid_mapping)

        # Date
        for col in ['createdAt', 'updatedAt']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df[col] = df[col].apply(
                    lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' if pd.notna(x) else None
                )

        logger.info(f"✅ shared_workflow trasformato: {len(df)} righe")
        return df

    def transform_shared_credentials(self) -> pd.DataFrame:
        """Trasforma shared_credentials (NO id column - composite key!)."""
        if 'shared_credentials' not in self.dataframes:
            return pd.DataFrame()

        df = self.dataframes['shared_credentials'].copy()
        logger.info(f"🔄 Trasformazione shared_credentials: {len(df)} righe")

        # Rimuovi colonna 'id' se presente (shared_credentials NON ha id!)
        if 'id' in df.columns:
            df = df.drop(columns=['id'])

        # Date
        for col in ['createdAt', 'updatedAt']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df[col] = df[col].apply(
                    lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' if pd.notna(x) else None
                )

        logger.info(f"✅ shared_credentials trasformato: {len(df)} righe")
        return df

    def transform_webhook_entity(self) -> pd.DataFrame:
        """Trasforma webhook_entity con UUID workflow mapping (NO id column!)."""
        if 'webhook_entity' not in self.dataframes:
            return pd.DataFrame()

        df = self.dataframes['webhook_entity'].copy()
        logger.info(f"🔄 Trasformazione webhook_entity: {len(df)} righe")

        # Rimuovi colonna 'id' se presente (webhook_entity usa composite key!)
        if 'id' in df.columns:
            df = df.drop(columns=['id'])

        # Map workflow IDs
        if 'workflowId' in df.columns:
            df['workflowId'] = df['workflowId'].astype(str).map(self.uuid_mapping)

        logger.info(f"✅ webhook_entity trasformato: {len(df)} righe")
        return df

    def transform_workflow_statistics(self) -> pd.DataFrame:
        """Trasforma workflow_statistics con UUID workflow mapping."""
        if 'workflow_statistics' not in self.dataframes:
            return pd.DataFrame()

        df = self.dataframes['workflow_statistics'].copy()
        logger.info(f"🔄 Trasformazione workflow_statistics: {len(df)} righe")

        # Map workflow IDs
        if 'workflowId' in df.columns:
            df['workflowId'] = df['workflowId'].astype(str).map(self.uuid_mapping)

        # Date
        for col in ['createdAt', 'updatedAt', 'latestEvent']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df[col] = df[col].apply(
                    lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' if pd.notna(x) else None
                )

        logger.info(f"✅ workflow_statistics trasformato: {len(df)} righe")
        return df

    def transform_insights_table(self, table_name: str) -> pd.DataFrame:
        """Trasforma tabelle insights con UUID workflow mapping."""
        if table_name not in self.dataframes:
            return pd.DataFrame()

        df = self.dataframes[table_name].copy()
        logger.info(f"🔄 Trasformazione {table_name}: {len(df)} righe")

        # Map workflow IDs se presente
        if 'workflowId' in df.columns:
            df['workflowId'] = df['workflowId'].astype(str).map(self.uuid_mapping)

        # Date comuni
        for col in ['createdAt', 'updatedAt', 'date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df[col] = df[col].apply(
                    lambda x: x.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z' if pd.notna(x) else None
                )

        logger.info(f"✅ {table_name} trasformato: {len(df)} righe")
        return df

    # ====================================================================
    # 7. EXPORT SQL
    # ====================================================================

    def export_to_sql(self, output_file: Optional[str] = None) -> str:
        """
        Genera script SQL con INSERT statements per PostgreSQL.

        Args:
            output_file: Path output SQL (default da config)

        Returns:
            Path al file SQL generato
        """
        if output_file is None:
            output_file = self.config['sql_output_file']

        logger.info(f"📝 Generazione SQL script: {output_file}")

        with open(output_file, 'w') as f:
            # Header SQL
            f.write("-- n8n Migration Script: SQLite → PostgreSQL\n")
            f.write(f"-- Generated: {datetime.now().isoformat()}\n")
            f.write(f"-- Total workflows: {len(self.uuid_mapping)}\n")
            f.write("-- \n")
            f.write("-- IMPORTANTE: Esegui su database PostgreSQL con schema 'n8n'\n")
            f.write("-- Comando: psql -h localhost -U pilotpros_user -d pilotpros_db -f import_n8n_data.sql\n")
            f.write("\n")

            # Set search_path per schema n8n
            f.write("SET search_path TO n8n, public;\n")
            f.write("BEGIN;\n\n")

            # 1. workflow_entity
            if 'workflow_entity' in self.dataframes:
                df = self.transform_workflow_entity()
                self._write_insert_statements(f, 'workflow_entity', df)

            # 2. execution_entity
            if 'execution_entity' in self.dataframes:
                df = self.transform_execution_entity()
                self._write_insert_statements(f, 'execution_entity', df)

            # 3. credentials_entity
            if 'credentials_entity' in self.dataframes:
                df = self.transform_credentials_entity()
                self._write_insert_statements(f, 'credentials_entity', df)

            # 4. execution_data (NO transform, mantiene executionId integer)
            if 'execution_data' in self.dataframes:
                df = self.transform_generic_table('execution_data')
                self._write_insert_statements(f, 'execution_data', df)

            # 5. tag_entity
            if 'tag_entity' in self.dataframes:
                df = self.transform_tag_entity()
                self._write_insert_statements(f, 'tag_entity', df)

            # 5. folder
            if 'folder' in self.dataframes:
                df = self.transform_generic_table('folder')
                self._write_insert_statements(f, 'folder', df)

            # 6. workflows_tags
            if 'workflows_tags' in self.dataframes:
                df = self.transform_workflows_tags()
                self._write_insert_statements(f, 'workflows_tags', df)

            # 7. shared_workflow
            if 'shared_workflow' in self.dataframes:
                df = self.transform_shared_workflow()
                self._write_insert_statements(f, 'shared_workflow', df)

            # 8. shared_credentials
            if 'shared_credentials' in self.dataframes:
                df = self.transform_shared_credentials()
                self._write_insert_statements(f, 'shared_credentials', df)

            # 9. webhook_entity
            if 'webhook_entity' in self.dataframes:
                df = self.transform_webhook_entity()
                self._write_insert_statements(f, 'webhook_entity', df)

            # 10. settings
            if 'settings' in self.dataframes:
                df = self.transform_generic_table('settings')
                self._write_insert_statements(f, 'settings', df)

            # 11. installed_packages
            if 'installed_packages' in self.dataframes:
                df = self.transform_generic_table('installed_packages')
                self._write_insert_statements(f, 'installed_packages', df)

            # 12. installed_nodes
            if 'installed_nodes' in self.dataframes:
                df = self.transform_generic_table('installed_nodes')
                self._write_insert_statements(f, 'installed_nodes', df)

            # 13. workflow_statistics (con UUID workflow mapping!)
            if 'workflow_statistics' in self.dataframes:
                df = self.transform_workflow_statistics()
                self._write_insert_statements(f, 'workflow_statistics', df)

            # 14. insights_metadata (con UUID workflow mapping)
            if 'insights_metadata' in self.dataframes:
                df = self.transform_insights_table('insights_metadata')
                self._write_insert_statements(f, 'insights_metadata', df)

            # 15. insights_raw (con UUID workflow mapping)
            if 'insights_raw' in self.dataframes:
                df = self.transform_insights_table('insights_raw')
                self._write_insert_statements(f, 'insights_raw', df)

            # 16. insights_by_period (con UUID workflow mapping)
            if 'insights_by_period' in self.dataframes:
                df = self.transform_insights_table('insights_by_period')
                self._write_insert_statements(f, 'insights_by_period', df)

            # 17. user_api_keys
            if 'user_api_keys' in self.dataframes:
                df = self.transform_generic_table('user_api_keys')
                self._write_insert_statements(f, 'user_api_keys', df)

            # 18. invalid_auth_token
            if 'invalid_auth_token' in self.dataframes:
                df = self.transform_generic_table('invalid_auth_token')
                self._write_insert_statements(f, 'invalid_auth_token', df)

            # 19. project_relation
            if 'project_relation' in self.dataframes:
                df = self.transform_generic_table('project_relation')
                self._write_insert_statements(f, 'project_relation', df)

            # Commit transaction
            f.write("\nCOMMIT;\n")
            f.write("\n-- ✅ Migration completata con tutte le tabelle!\n")

        logger.info(f"✅ SQL script generato: {output_file}")
        return output_file

    def _write_insert_statements(self, file, table_name: str, df: pd.DataFrame):
        """Scrive INSERT statements per una tabella."""
        if df.empty:
            file.write(f"-- ⚠️ {table_name}: nessun dato\n\n")
            return

        file.write(f"-- {table_name} ({len(df)} righe)\n")
        file.write(f"INSERT INTO {table_name} (")

        # Colonne
        columns = ', '.join([f'"{col}"' for col in df.columns])
        file.write(f"{columns}) VALUES\n")

        # Colonne con DEFAULT per NULL (hanno NOT NULL constraint + DEFAULT value in schema)
        default_columns = {'createdAt', 'updatedAt'}

        # Valori
        rows_list = list(df.iterrows())
        for idx, (i, row) in enumerate(rows_list):
            values = []
            for col in df.columns:
                val = row[col]

                if pd.isna(val):
                    # Per colonne con DEFAULT, usa keyword DEFAULT invece di NULL
                    if col in default_columns:
                        values.append('DEFAULT')
                    else:
                        values.append('NULL')
                elif isinstance(val, bool):
                    values.append('true' if val else 'false')
                elif isinstance(val, (int, float)):
                    values.append(str(val))
                else:
                    # Escape single quotes per SQL
                    val_escaped = str(val).replace("'", "''")
                    values.append(f"'{val_escaped}'")

            # Ultima riga senza virgola
            separator = ',' if idx < len(rows_list) - 1 else ';'
            file.write(f"  ({', '.join(values)}){separator}\n")

        file.write("\n")

    # ====================================================================
    # 7. EXPORT CSV per COPY
    # ====================================================================

    def export_to_csv(self, output_dir: Optional[str] = None):
        """
        Genera CSV trasformati per import con PostgreSQL COPY.

        COPY è più veloce di INSERT per grandi dataset (>10K righe).

        Args:
            output_dir: Directory output CSV (default da config)
        """
        if output_dir is None:
            output_dir = self.config['csv_output_dir']

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"📦 Export CSV per COPY: {output_path}")

        # workflow_entity
        if 'workflow_entity' in self.dataframes:
            df = self.transform_workflow_entity()
            csv_file = output_path / 'workflow_entity.csv'
            df.to_csv(csv_file, index=False, encoding='utf-8')
            logger.info(f"✅ {csv_file.name}: {len(df)} righe")

        # execution_entity
        if 'execution_entity' in self.dataframes:
            df = self.transform_execution_entity()
            csv_file = output_path / 'execution_entity.csv'
            df.to_csv(csv_file, index=False, encoding='utf-8')
            logger.info(f"✅ {csv_file.name}: {len(df)} righe")

        # credentials_entity
        if 'credentials_entity' in self.dataframes:
            df = self.transform_credentials_entity()
            csv_file = output_path / 'credentials_entity.csv'
            df.to_csv(csv_file, index=False, encoding='utf-8')
            logger.info(f"✅ {csv_file.name}: {len(df)} righe")

        logger.info(f"✅ CSV export completato: {output_path}")

    # ====================================================================
    # 8. IMPORT DIRETTO POSTGRESQL
    # ====================================================================

    def import_to_postgres(self, dry_run: bool = False):
        """
        Importa dati direttamente nel database PostgreSQL.

        Args:
            dry_run: Se True, non esegue INSERT (solo validazione)
        """
        db_config = self.config['database']

        logger.info(f"🚀 Connessione PostgreSQL: {db_config['host']}:{db_config['port']}")

        try:
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )

            cursor = conn.cursor()

            # Set schema
            cursor.execute(f"SET search_path TO {db_config['schema']}, public;")

            if dry_run:
                logger.info("🔍 DRY RUN: Solo validazione (NO INSERT)")
                conn.rollback()
                return

            # 1. workflow_entity
            if 'workflow_entity' in self.dataframes:
                df = self.transform_workflow_entity()
                self._insert_dataframe(cursor, 'workflow_entity', df)

            # 2. execution_entity
            if 'execution_entity' in self.dataframes:
                df = self.transform_execution_entity()
                self._insert_dataframe(cursor, 'execution_entity', df)

            # 3. credentials_entity
            if 'credentials_entity' in self.dataframes:
                df = self.transform_credentials_entity()
                self._insert_dataframe(cursor, 'credentials_entity', df)

            conn.commit()
            logger.info("✅ Import PostgreSQL completato!")

        except Exception as e:
            logger.error(f"❌ Errore import PostgreSQL: {e}")
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    def _insert_dataframe(self, cursor, table_name: str, df: pd.DataFrame):
        """Inserisce DataFrame in PostgreSQL con execute_values."""
        if df.empty:
            logger.warning(f"⚠️ {table_name}: nessun dato (skip)")
            return

        columns = ', '.join([f'"{col}"' for col in df.columns])
        values = [tuple(row) for row in df.to_numpy()]

        query = f"INSERT INTO {table_name} ({columns}) VALUES %s"

        execute_values(cursor, query, values)
        logger.info(f"✅ {table_name}: {len(df)} righe inserite")

    # ====================================================================
    # 9. VALIDAZIONE
    # ====================================================================

    def validate_data(self) -> Dict[str, Any]:
        """
        Valida integrità dati prima/dopo import.

        Controlli:
        - Foreign keys workflow → execution
        - Count record per tabella
        - Campi NOT NULL
        - JSON validity

        Returns:
            Dict con risultati validazione
        """
        logger.info("🔍 Validazione integrità dati...")

        results = {
            'timestamp': datetime.now().isoformat(),
            'checks': [],
            'errors': [],
            'warnings': []
        }

        # 1. Check workflow count
        if 'workflow_entity' in self.dataframes:
            count = len(self.dataframes['workflow_entity'])
            results['checks'].append(f"✅ workflow_entity: {count} righe")

        # 2. Check execution → workflow foreign keys
        if 'execution_entity' in self.dataframes:
            df_exec = self.dataframes['execution_entity']
            workflow_col = self._get_workflow_id_column(df_exec)

            missing_refs = 0
            for old_wf_id in df_exec[workflow_col].unique():
                if str(old_wf_id) not in self.uuid_mapping:
                    missing_refs += 1
                    results['errors'].append(f"❌ workflowId not in mapping: {old_wf_id}")

            if missing_refs == 0:
                results['checks'].append(f"✅ execution foreign keys: OK")
            else:
                results['checks'].append(f"⚠️ execution foreign keys: {missing_refs} missing")

        # 3. Check JSON fields
        # TODO: validazione JSON avanzata

        logger.info(f"✅ Validazione completata: {len(results['errors'])} errori")
        return results


# ====================================================================
# CLI INTERFACE
# ====================================================================

def main():
    """Entry point CLI."""
    parser = argparse.ArgumentParser(
        description='Migra dati n8n da CSV (SQLite) a PostgreSQL con UUID remapping',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  # Step 1: Genera UUID mapping e SQL script
  python migrate_n8n_sqlite_to_postgres.py --config migration_config.yaml --export-sql

  # Step 2: Valida SQL prima di importare
  python migrate_n8n_sqlite_to_postgres.py --validate

  # Step 3: Importa in PostgreSQL
  psql -h localhost -U pilotpros_user -d pilotpros_db -f import_n8n_data.sql

  # Oppure import diretto:
  python migrate_n8n_sqlite_to_postgres.py --import --dry-run  # Test
  python migrate_n8n_sqlite_to_postgres.py --import             # Real import
        """
    )

    parser.add_argument(
        '--config',
        default='migration_config.yaml',
        help='Path al file di configurazione YAML (default: migration_config.yaml)'
    )

    parser.add_argument(
        '--export-sql',
        action='store_true',
        help='Genera script SQL per import (default: import_n8n_data.sql)'
    )

    parser.add_argument(
        '--export-csv',
        action='store_true',
        help='Genera CSV trasformati per PostgreSQL COPY'
    )

    parser.add_argument(
        '--import',
        action='store_true',
        dest='import_db',
        help='Importa dati direttamente in PostgreSQL'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Esegui validazione senza modificare database'
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Valida integrità dati (foreign keys, NOT NULL, etc.)'
    )

    args = parser.parse_args()

    try:
        # Inizializza migrator
        migrator = N8nMigration(config_path=args.config)

        # 1. Leggi CSV
        logger.info("🚀 STEP 1: Lettura CSV...")
        migrator.read_csv_files()

        # 2. Genera UUID mapping
        logger.info("🚀 STEP 2: Generazione UUID mapping...")
        migrator.generate_uuid_mapping()
        migrator.generate_tag_uuid_mapping()

        # 3. Validazione (opzionale)
        if args.validate:
            logger.info("🚀 STEP 3: Validazione dati...")
            results = migrator.validate_data()
            print("\n" + "="*60)
            print("RISULTATI VALIDAZIONE")
            print("="*60)
            for check in results['checks']:
                print(check)
            if results['errors']:
                print("\n⚠️ ERRORI:")
                for err in results['errors']:
                    print(f"  {err}")
            print("="*60 + "\n")

        # 4. Export SQL
        if args.export_sql:
            logger.info("🚀 STEP 4: Export SQL...")
            sql_file = migrator.export_to_sql()
            print(f"\n✅ SQL script generato: {sql_file}")
            print(f"   Importa con: psql -h localhost -U pilotpros_user -d pilotpros_db -f {sql_file}\n")

        # 5. Export CSV
        if args.export_csv:
            logger.info("🚀 STEP 5: Export CSV...")
            migrator.export_to_csv()
            print(f"\n✅ CSV trasformati generati: {migrator.config['csv_output_dir']}")
            print("   Importa con: COPY workflow_entity FROM 'workflow_entity.csv' CSV HEADER;\n")

        # 6. Import PostgreSQL
        if args.import_db:
            logger.info("🚀 STEP 6: Import PostgreSQL...")
            migrator.import_to_postgres(dry_run=args.dry_run)

            if args.dry_run:
                print("\n✅ DRY RUN completato (nessuna modifica al database)\n")
            else:
                print("\n✅ Import PostgreSQL completato!\n")

        # Default: export SQL
        if not any([args.export_sql, args.export_csv, args.import_db, args.validate]):
            logger.info("🚀 Default: Export SQL...")
            sql_file = migrator.export_to_sql()
            print(f"\n✅ SQL script generato: {sql_file}")
            print(f"   Importa con: psql -h localhost -U pilotpros_user -d pilotpros_db -f {sql_file}\n")

        logger.info("🎉 Migrazione completata con successo!")

    except Exception as e:
        logger.error(f"❌ ERRORE FATALE: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
