#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script OTIMIZADO para traduzir arquivos CSV do Mount and Blade Warband
com autodetecção de idioma e tradução acelerada

Recursos:
- Autodetecção de idioma (traduz qualquer idioma para PT-BR)
- Tradução paralela (multithreading)
- Cache inteligente
- Processamento em lotes
- Modo turbo opcional

Autor: Bypass
Data: 2025
"""

import os
import time
import json
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from googletrans import Translator
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
import logging
from tqdm import tqdm
from queue import Queue
import hashlib

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('translation_optimized.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OptimizedMountBladeTranslator:
    def __init__(self, input_dir: str, output_dir: str, turbo_mode: bool = False):
        """
        Inicializa o tradutor otimizado
        
        Args:
            input_dir: Diretório com arquivos CSV de entrada
            output_dir: Diretório para arquivos CSV traduzidos
            turbo_mode: Ativa modo turbo (mais rápido, mais recursos)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.turbo_mode = turbo_mode
        
        # Configurações baseadas no modo
        if turbo_mode:
            self.max_workers = min(32, os.cpu_count() * 4)  # Mais threads
            self.batch_size = 50  # Lotes maiores
            self.delay = 0.05  # Delay menor
            logger.info("🚀 MODO TURBO ATIVADO - Máxima velocidade!")
        else:
            self.max_workers = min(8, os.cpu_count() * 2)  # Threads moderadas
            self.batch_size = 20  # Lotes menores
            self.delay = 0.1  # Delay padrão
            logger.info("⚡ Modo padrão ativado")
        
        # Pool de tradutores para evitar rate limiting
        self.translators = [Translator() for _ in range(self.max_workers)]
        self.translator_queue = Queue()
        for translator in self.translators:
            self.translator_queue.put(translator)
        
        # Cache de traduções
        self.cache_file = self.output_dir / 'translation_cache_optimized.json'
        self.cache = self.load_cache()
        
        # Criar diretório de saída
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Estatísticas
        self.stats = {
            'files_processed': 0,
            'lines_translated': 0,
            'lines_skipped': 0,
            'lines_cached': 0,
            'errors': 0,
            'languages_detected': set()
        }
        
        logger.info(f"Tradutor otimizado inicializado: {input_dir} -> {output_dir}")
        logger.info(f"Workers: {self.max_workers}, Batch: {self.batch_size}, Delay: {self.delay}s")
    
    def load_cache(self) -> dict:
        """
        Carrega cache de traduções
        
        Returns:
            Dicionário com cache
        """
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                logger.info(f"📦 Cache carregado: {len(cache)} traduções")
                return cache
        except Exception as e:
            logger.warning(f"Erro ao carregar cache: {e}")
        return {}
    
    def save_cache(self) -> None:
        """
        Salva cache de traduções
        """
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Erro ao salvar cache: {e}")
    
    def get_cache_key(self, text: str, src_lang: str) -> str:
        """
        Gera chave única para cache
        
        Args:
            text: Texto original
            src_lang: Idioma de origem
            
        Returns:
            Chave do cache
        """
        return hashlib.md5(f"{src_lang}:{text}".encode()).hexdigest()
    
    def detect_language(self, text: str) -> str:
        """
        Detecta o idioma do texto automaticamente
        
        Args:
            text: Texto para detectar idioma
            
        Returns:
            Código do idioma detectado
        """
        try:
            # Limpar texto para detecção
            clean_text = text.strip()
            if len(clean_text) < 3:
                return 'unknown'
            
            detected = detect(clean_text)
            self.stats['languages_detected'].add(detected)
            return detected
            
        except LangDetectException:
            return 'unknown'
        except Exception as e:
            logger.debug(f"Erro na detecção de idioma: {e}")
            return 'unknown'
    
    def should_translate(self, text: str) -> bool:
        """
        Verifica se um texto deve ser traduzido
        
        Args:
            text: Texto a verificar
            
        Returns:
            True se deve traduzir, False caso contrário
        """
        text = text.strip()
        
        # Ignorar textos muito curtos
        if len(text) < 2:
            return False
        
        # Ignorar textos que são apenas números
        if text.isdigit():
            return False
        
        # Ignorar textos que são códigos
        if text.isupper() and ('_' in text or text.isalnum()):
            return False
        
        # Ignorar textos específicos
        ignore_texts = {
            'INVALID ITEM', 'NO ITEM', 'NONE', 'NULL', 'N/A',
            'Correctif bug langage', 'PLACEHOLDER', 'TODO'
        }
        if text.upper() in ignore_texts:
            return False
        
        # Detectar idioma
        detected_lang = self.detect_language(text)
        
        # Não traduzir se já está em português
        if detected_lang == 'pt':
            return False
        
        # Traduzir se detectou um idioma válido (exceto português)
        return detected_lang != 'unknown'
    
    def translate_text_cached(self, text: str, src_lang: str = 'auto') -> str:
        """
        Traduz texto usando cache
        
        Args:
            text: Texto a ser traduzido
            src_lang: Idioma de origem
            
        Returns:
            Texto traduzido
        """
        # Verificar cache primeiro
        cache_key = self.get_cache_key(text, src_lang)
        if cache_key in self.cache:
            self.stats['lines_cached'] += 1
            return self.cache[cache_key]
        
        # Traduzir se não estiver no cache
        try:
            # Pegar tradutor da pool
            translator = self.translator_queue.get()
            
            try:
                result = translator.translate(text, src=src_lang, dest='pt')
                translated = result.text
                
                # Salvar no cache
                self.cache[cache_key] = translated
                
                # Delay para evitar rate limiting
                time.sleep(self.delay)
                
                return translated
                
            finally:
                # Devolver tradutor para a pool
                self.translator_queue.put(translator)
                
        except Exception as e:
            logger.debug(f"Erro na tradução: {e}")
            self.stats['errors'] += 1
            return text
    
    def translate_batch(self, texts_batch: list) -> list:
        """
        Traduz um lote de textos em paralelo
        
        Args:
            texts_batch: Lista de tuplas (texto, idioma_origem)
            
        Returns:
            Lista de textos traduzidos
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=min(len(texts_batch), self.max_workers)) as executor:
            # Submeter tarefas
            future_to_text = {
                executor.submit(self.translate_text_cached, text, src_lang): (i, text)
                for i, (text, src_lang) in enumerate(texts_batch)
            }
            
            # Coletar resultados
            results = [None] * len(texts_batch)
            for future in as_completed(future_to_text):
                i, original_text = future_to_text[future]
                try:
                    translated = future.result()
                    results[i] = translated
                except Exception as e:
                    logger.error(f"Erro na tradução paralela: {e}")
                    results[i] = original_text
                    self.stats['errors'] += 1
        
        return results
    
    def process_line(self, line: str) -> str:
        """
        Processa uma linha do CSV
        
        Args:
            line: Linha do CSV
            
        Returns:
            Linha processada
        """
        line = line.strip()
        
        # Verificar se tem o separador
        if '|' not in line:
            return line
        
        # Dividir em parâmetro e texto
        parts = line.split('|', 1)
        if len(parts) != 2:
            return line
        
        parameter = parts[0]
        text = parts[1]
        
        # Verificar se deve traduzir
        if self.should_translate(text):
            # Detectar idioma
            src_lang = self.detect_language(text)
            if src_lang == 'unknown':
                src_lang = 'auto'
            
            translated_text = self.translate_text_cached(text, src_lang)
            self.stats['lines_translated'] += 1
            return f"{parameter}|{translated_text}"
        else:
            self.stats['lines_skipped'] += 1
            return line
    
    def process_file_optimized(self, input_file: Path) -> bool:
        """
        Processa um arquivo CSV de forma otimizada
        
        Args:
            input_file: Arquivo de entrada
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            output_file = self.output_dir / input_file.name
            
            # Ler todas as linhas
            with open(input_file, 'r', encoding='utf-8') as infile:
                lines = [line.rstrip('\n\r') for line in infile]
            
            total_lines = len(lines)
            logger.info(f"Processando: {input_file.name} ({total_lines} linhas)")
            
            # Processar em lotes para otimização
            processed_lines = []
            
            with tqdm(total=total_lines, desc=f"📄 {input_file.name}", 
                     unit="linhas", ncols=120, colour='green') as pbar:
                
                for i in range(0, total_lines, self.batch_size):
                    batch = lines[i:i + self.batch_size]
                    
                    # Processar lote
                    for line in batch:
                        processed_line = self.process_line(line)
                        processed_lines.append(processed_line)
                        
                        # Atualizar barra
                        pbar.update(1)
                        
                        # Atualizar estatísticas
                        if len(processed_lines) % 50 == 0:
                            pbar.set_postfix({
                                'Traduzidas': self.stats['lines_translated'],
                                'Cache': self.stats['lines_cached'],
                                'Idiomas': len(self.stats['languages_detected'])
                            })
                    
                    # Salvar cache periodicamente
                    if i % (self.batch_size * 10) == 0:
                        self.save_cache()
            
            # Escrever arquivo final
            with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                for line in processed_lines:
                    outfile.write(line + '\n')
            
            logger.info(f"✅ Concluído: {input_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar {input_file}: {e}")
            return False
    
    def translate_all(self) -> None:
        """
        Traduz todos os arquivos CSV de forma otimizada
        """
        mode_text = "🚀 TURBO" if self.turbo_mode else "⚡ PADRÃO"
        print(f"{mode_text} - TRADUÇÃO OTIMIZADA COM AUTODETECÇÃO")
        print("=" * 60)
        
        # Encontrar arquivos CSV
        csv_files = list(self.input_dir.glob('*.csv'))
        
        if not csv_files:
            logger.warning(f"❌ Nenhum arquivo CSV encontrado em {self.input_dir}")
            return
        
        logger.info(f"📁 Encontrados {len(csv_files)} arquivos CSV")
        logger.info(f"🔧 Configuração: {self.max_workers} workers, lotes de {self.batch_size}")
        
        # Processar arquivos
        start_time = time.time()
        
        with tqdm(csv_files, desc="🗂️  Arquivos", unit="arquivo", colour='blue') as file_pbar:
            for csv_file in file_pbar:
                try:
                    file_pbar.set_description(f"🗂️  {csv_file.name}")
                    
                    success = self.process_file_optimized(csv_file)
                    if success:
                        self.stats['files_processed'] += 1
                    
                    # Atualizar estatísticas
                    file_pbar.set_postfix({
                        'Processados': self.stats['files_processed'],
                        'Traduzidas': self.stats['lines_translated'],
                        'Cache': self.stats['lines_cached']
                    })
                    
                    # Salvar cache
                    self.save_cache()
                    
                except KeyboardInterrupt:
                    print("\n⏹️  Tradução interrompida pelo usuário")
                    break
                except Exception as e:
                    logger.error(f"❌ Erro inesperado: {e}")
        
        # Salvar cache final
        self.save_cache()
        
        # Estatísticas finais
        end_time = time.time()
        total_time = end_time - start_time
        self.print_stats(total_time)
    
    def print_stats(self, total_time: float) -> None:
        """
        Exibe estatísticas finais
        
        Args:
            total_time: Tempo total de processamento
        """
        print("\n" + "=" * 60)
        print("📊 ESTATÍSTICAS FINAIS")
        print("=" * 60)
        print(f"📁 Arquivos processados: {self.stats['files_processed']}")
        print(f"✅ Linhas traduzidas: {self.stats['lines_translated']}")
        print(f"📦 Linhas do cache: {self.stats['lines_cached']}")
        print(f"⏭️  Linhas ignoradas: {self.stats['lines_skipped']}")
        print(f"❌ Erros: {self.stats['errors']}")
        print(f"🌍 Idiomas detectados: {', '.join(sorted(self.stats['languages_detected']))}")
        print(f"⏱️  Tempo total: {total_time:.2f}s")
        
        if self.stats['lines_translated'] > 0:
            rate = self.stats['lines_translated'] / total_time
            print(f"🚀 Velocidade: {rate:.2f} traduções/segundo")
        
        print("=" * 60)

def main():
    """
    Função principal com opção de modo turbo
    """
    input_dir = "c:/Users/Usuario/Downloads/MountAndBlade - TranslatePTBR/input/"
    output_dir = "c:/Users/Usuario/Downloads/MountAndBlade - TranslatePTBR/output/"
    
    # Perguntar sobre modo turbo
    print("🔧 CONFIGURAÇÃO DE TRADUÇÃO")
    print("=" * 40)
    print("Escolha o modo de tradução:")
    print("1. ⚡ Padrão (equilibrado)")
    print("2. 🚀 Turbo (máxima velocidade)")
    
    try:
        choice = input("\nEscolha (1 ou 2): ").strip()
        turbo_mode = choice == '2'
        
        if not os.path.exists(input_dir):
            logger.error(f"❌ Diretório não encontrado: {input_dir}")
            return
        
        # Criar e executar tradutor
        translator = OptimizedMountBladeTranslator(input_dir, output_dir, turbo_mode)
        translator.translate_all()
        
        print("\n🎉 TRADUÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"📁 Arquivos salvos em: {output_dir}")
        print("💡 Dica: O cache foi salvo para acelerar futuras traduções!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Operação cancelada pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        raise

if __name__ == "__main__":
    main()