#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Tradução Protegido para Mount & Blade
Versão que protege variáveis de formatação e detecta tokens não reconhecidos
"""

import os
import csv
import re
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

try:
    from googletrans import Translator
    from langdetect import detect
    from langdetect.lang_detect_exception import LangDetectException
    from tqdm import tqdm
except ImportError as e:
    print(f"Erro: Biblioteca necessária não encontrada: {e}")
    print("Execute: pip install googletrans==4.0.0rc1 langdetect tqdm")
    exit(1)

class ProtectedTranslator:
    def __init__(self, input_dir: str, output_dir: str, cache_file: str = "translation_cache_protected.json"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.cache_file = Path(cache_file)
        self.translator = Translator()
        self.cache = self._load_cache()
        self.cache_lock = Lock()
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('translation_protected.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Padrões para proteger variáveis de formatação
        self.protection_patterns = [
            # Variáveis simples: {S1}, {s54}, {reg1}
            (r'\{[Ss]\d+\}', 'PROTECTED_VAR_S'),
            (r'\{[Rr]eg\d+\}', 'PROTECTED_VAR_REG'),
            (r'\{[Pp]layername\}', 'PROTECTED_PLAYERNAME'),
            
            # Variáveis condicionais: {reg63? Senhor: Madame}
            (r'\{[^}]*\?[^}]*:[^}]*\}', 'PROTECTED_CONDITIONAL'),
            
            # Outras variáveis especiais
            (r'\{[^}]+\}', 'PROTECTED_OTHER_VAR'),
            
            # Símbolos especiais
            (r'\^\^', 'PROTECTED_DOUBLE_CARET'),
            (r'\{/[^}]*\}', 'PROTECTED_SLASH_VAR'),
        ]
        
        # Estatísticas
        self.stats = {
            'files_processed': 0,
            'lines_translated': 0,
            'cache_hits': 0,
            'translation_requests': 0,
            'protected_variables': 0,
            'errors': 0
        }
    
    def _load_cache(self) -> Dict[str, str]:
        """Carrega cache de traduções anteriores"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Erro ao carregar cache: {e}")
        return {}
    
    def _save_cache(self):
        """Salva cache de traduções"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Erro ao salvar cache: {e}")
    
    def _protect_variables(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Protege variáveis de formatação substituindo por placeholders"""
        protected_text = text
        replacements = {}
        
        for pattern, placeholder_base in self.protection_patterns:
            matches = re.finditer(pattern, protected_text)
            for i, match in enumerate(matches):
                original = match.group(0)
                placeholder = f"{placeholder_base}_{i}"
                replacements[placeholder] = original
                protected_text = protected_text.replace(original, placeholder, 1)
                self.stats['protected_variables'] += 1
        
        return protected_text, replacements
    
    def _restore_variables(self, text: str, replacements: Dict[str, str]) -> str:
        """Restaura variáveis protegidas"""
        restored_text = text
        for placeholder, original in replacements.items():
            restored_text = restored_text.replace(placeholder, original)
        return restored_text
    
    def _detect_language(self, text: str) -> str:
        """Detecta idioma do texto"""
        try:
            # Remove variáveis para melhor detecção
            clean_text = re.sub(r'\{[^}]*\}', '', text)
            clean_text = re.sub(r'\^+', '', clean_text)
            clean_text = clean_text.strip()
            
            if len(clean_text) < 3:
                return 'unknown'
            
            detected = detect(clean_text)
            return detected
        except (LangDetectException, Exception):
            return 'unknown'
    
    def _should_translate(self, text: str) -> bool:
        """Verifica se o texto deve ser traduzido"""
        if not text or len(text.strip()) < 2:
            return False
        
        # Não traduzir se for apenas variáveis
        clean_text = re.sub(r'\{[^}]*\}', '', text)
        clean_text = re.sub(r'\^+', '', clean_text)
        clean_text = clean_text.strip()
        
        if len(clean_text) < 2:
            return False
        
        # Detectar idioma
        lang = self._detect_language(text)
        
        # Traduzir se não for português
        return lang != 'pt' and lang != 'unknown'
    
    def _translate_text(self, text: str) -> str:
        """Traduz texto protegendo variáveis"""
        if not self._should_translate(text):
            return text
        
        # Verificar cache
        cache_key = text.strip()
        with self.cache_lock:
            if cache_key in self.cache:
                self.stats['cache_hits'] += 1
                return self.cache[cache_key]
        
        try:
            # Proteger variáveis
            protected_text, replacements = self._protect_variables(text)
            
            # Traduzir texto protegido
            self.stats['translation_requests'] += 1
            result = self.translator.translate(protected_text, src='auto', dest='pt')
            translated = result.text
            
            # Restaurar variáveis
            final_text = self._restore_variables(translated, replacements)
            
            # Validar se todas as variáveis foram preservadas
            original_vars = re.findall(r'\{[^}]*\}', text)
            final_vars = re.findall(r'\{[^}]*\}', final_text)
            
            if len(original_vars) != len(final_vars):
                self.logger.warning(f"Variáveis perdidas na tradução: '{text}' -> '{final_text}'")
                # Em caso de perda de variáveis, retornar texto original
                final_text = text
            
            # Salvar no cache
            with self.cache_lock:
                self.cache[cache_key] = final_text
            
            return final_text
            
        except Exception as e:
            self.logger.error(f"Erro na tradução de '{text}': {e}")
            self.stats['errors'] += 1
            return text
    
    def _detect_unrecognized_tokens(self, text: str) -> List[str]:
        """Detecta possíveis tokens não reconhecidos"""
        suspicious_patterns = [
            r'UNRECOGNIZED[\s_]*TOKEN',
            r'\{[^}]*UNRECOGNIZED[^}]*\}',
            r'\{[^}]*ERROR[^}]*\}',
            r'\{[^}]*INVALID[^}]*\}',
        ]
        
        found_issues = []
        for pattern in suspicious_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_issues.extend(matches)
        
        return found_issues
    
    def translate_csv_file(self, input_file: Path, output_file: Path, max_workers: int = 4):
        """Traduz arquivo CSV com proteção de variáveis"""
        self.logger.info(f"Iniciando tradução: {input_file.name}")
        
        try:
            with open(input_file, 'r', encoding='utf-8') as infile:
                reader = csv.reader(infile, delimiter='|')
                rows = list(reader)
            
            if not rows:
                self.logger.warning(f"Arquivo vazio: {input_file}")
                return
            
            # Preparar dados para tradução paralela
            translation_tasks = []
            for i, row in enumerate(rows):
                if len(row) >= 2:
                    original_text = row[1]
                    translation_tasks.append((i, original_text))
            
            # Traduzir em paralelo com barra de progresso
            translated_rows = rows.copy()
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submeter tarefas
                future_to_task = {
                    executor.submit(self._translate_text, task[1]): task 
                    for task in translation_tasks
                }
                
                # Processar resultados com barra de progresso
                with tqdm(total=len(translation_tasks), 
                         desc=f"Traduzindo {input_file.name}", 
                         unit="linhas") as pbar:
                    
                    for future in as_completed(future_to_task):
                        task = future_to_task[future]
                        row_index, original_text = task
                        
                        try:
                            translated_text = future.result()
                            translated_rows[row_index][1] = translated_text
                            
                            # Verificar tokens não reconhecidos
                            issues = self._detect_unrecognized_tokens(translated_text)
                            if issues:
                                self.logger.warning(
                                    f"Possíveis tokens não reconhecidos em {input_file.name}, "
                                    f"linha {row_index + 1}: {issues}"
                                )
                            
                            self.stats['lines_translated'] += 1
                            
                        except Exception as e:
                            self.logger.error(f"Erro na linha {row_index + 1}: {e}")
                            self.stats['errors'] += 1
                        
                        pbar.update(1)
                        
                        # Salvar cache periodicamente
                        if pbar.n % 100 == 0:
                            self._save_cache()
            
            # Salvar arquivo traduzido
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                writer = csv.writer(outfile, delimiter='|')
                writer.writerows(translated_rows)
            
            self.stats['files_processed'] += 1
            self.logger.info(f"Concluído: {input_file.name} -> {output_file.name}")
            
        except Exception as e:
            self.logger.error(f"Erro ao processar {input_file}: {e}")
            self.stats['errors'] += 1
    
    def translate_all_files(self, max_workers: int = 4):
        """Traduz todos os arquivos CSV"""
        csv_files = list(self.input_dir.glob("*.csv"))
        
        if not csv_files:
            self.logger.error(f"Nenhum arquivo CSV encontrado em {self.input_dir}")
            return
        
        self.logger.info(f"Encontrados {len(csv_files)} arquivos CSV para traduzir")
        
        # Traduzir cada arquivo
        for csv_file in csv_files:
            output_file = self.output_dir / csv_file.name
            self.translate_csv_file(csv_file, output_file, max_workers)
            
            # Pequena pausa entre arquivos
            time.sleep(1)
        
        # Salvar cache final
        self._save_cache()
        
        # Exibir estatísticas
        self._print_statistics()
    
    def _print_statistics(self):
        """Exibe estatísticas da tradução"""
        self.logger.info("=== ESTATÍSTICAS DA TRADUÇÃO ===")
        self.logger.info(f"Arquivos processados: {self.stats['files_processed']}")
        self.logger.info(f"Linhas traduzidas: {self.stats['lines_translated']}")
        self.logger.info(f"Variáveis protegidas: {self.stats['protected_variables']}")
        self.logger.info(f"Cache hits: {self.stats['cache_hits']}")
        self.logger.info(f"Requisições de tradução: {self.stats['translation_requests']}")
        self.logger.info(f"Erros: {self.stats['errors']}")
        
        if self.stats['translation_requests'] > 0:
            cache_rate = (self.stats['cache_hits'] / 
                         (self.stats['cache_hits'] + self.stats['translation_requests'])) * 100
            self.logger.info(f"Taxa de cache: {cache_rate:.1f}%")

def main():
    # Configurações
    input_directory = "input"
    output_directory = "output"
    max_workers = 6  # Número de threads paralelas
    
    # Verificar se diretório de entrada existe
    if not os.path.exists(input_directory):
        print(f"Erro: Diretório '{input_directory}' não encontrado!")
        return
    
    # Criar tradutor
    translator = ProtectedTranslator(input_directory, output_directory)
    
    print("🛡️ Iniciando tradução com proteção de variáveis...")
    print(f"📁 Entrada: {input_directory}")
    print(f"📁 Saída: {output_directory}")
    print(f"🔧 Threads: {max_workers}")
    print("\n🔄 Processando...")
    
    # Executar tradução
    start_time = time.time()
    translator.translate_all_files(max_workers)
    end_time = time.time()
    
    print(f"\n✅ Tradução concluída em {end_time - start_time:.1f} segundos!")
    print("\n📋 Recursos implementados:")
    print("   • Proteção de variáveis de formatação {S1}, {reg63}, etc.")
    print("   • Detecção de tokens não reconhecidos")
    print("   • Validação de preservação de variáveis")
    print("   • Cache inteligente")
    print("   • Processamento paralelo")
    print("   • Logs detalhados")

if __name__ == "__main__":
    main()