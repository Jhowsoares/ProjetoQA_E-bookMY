#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRIPT DE TESTES AUTOMATIZADOS - WebEduc
Projeto: Plataforma de Hospedagem de Cursos em E-book
Grupo: VibeCoders Anônimos
Atividade: AC3 - Quality Assurance
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Tuple

# ============================================================================
# ⚙️ CONFIGURAÇÃO - ALTERE CONFORME SEU SISTEMA
# ============================================================================

BASE_URL = "http://localhost:5000"  # 🔧 ALTERE PARA SUA URL
TIMEOUT = 10  # segundos
RELATORIO_FILE = "relatorio_testes.json"

# ============================================================================
# 📊 CLASSES E FUNÇÕES AUXILIARES
# ============================================================================

class TestResult:
    """Armazena resultado de um teste"""
    def __init__(self, test_id, titulo, categoria):
        self.test_id = test_id
        self.titulo = titulo
        self.categoria = categoria
        self.status = None  # "PASS" ou "FAIL"
        self.resultado_esperado = None
        self.resultado_obtido = None
        self.evidencia = None
        self.erro = None
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            "id": self.test_id,
            "titulo": self.titulo,
            "categoria": self.categoria,
            "status": self.status,
            "resultado_esperado": self.resultado_esperado,
            "resultado_obtido": self.resultado_obtido,
            "evidencia": self.evidencia,
            "erro": self.erro,
            "timestamp": self.timestamp
        }

class TestRunner:
    """Executa testes e coleta resultados"""
    def __init__(self, base_url):
        self.base_url = base_url
        self.resultados = []
        self.usuarios_criados = []  # para cleanup
        self.cursos_criados = []
    
    def adicionar_resultado(self, resultado: TestResult):
        self.resultados.append(resultado)
        status_emoji = "✅ PASS" if resultado.status == "PASS" else "❌ FAIL"
        print(f"{status_emoji} | {resultado.test_id} | {resultado.titulo}")
    
    def exibir_resumo(self):
        total = len(self.resultados)
        passed = sum(1 for r in self.resultados if r.status == "PASS")
        failed = sum(1 for r in self.resultados if r.status == "FAIL")
        
        print("\n" + "="*70)
        print("📊 RESUMO DOS TESTES")
        print("="*70)
        print(f"Total de Testes: {total}")
        print(f"✅ Passaram: {passed}")
        print(f"❌ Falharam: {failed}")
        print(f"Taxa de Sucesso: {(passed/total)*100:.1f}%")
        print("="*70 + "\n")
    
    def salvar_relatorio(self, filename):
        """Salva relatório em JSON"""
        relatorio = {
            "data_execucao": datetime.now().isoformat(),
            "base_url": self.base_url,
            "total_testes": len(self.resultados),
            "passou": sum(1 for r in self.resultados if r.status == "PASS"),
            "falhou": sum(1 for r in self.resultados if r.status == "FAIL"),
            "testes": [r.to_dict() for r in self.resultados]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Relatório salvo em: {filename}\n")

# ============================================================================
# 🧪 TESTES DO MÓDULO DE USUÁRIOS
# ============================================================================

def CT_001_Cadastro_Usuario_Valido(runner: TestRunner):
    """CT-001: Cadastro de usuário com dados válidos"""
    resultado = TestResult("CT-001", "Cadastro de usuário com dados válidos", "Validação")
    resultado.resultado_esperado = "Status 201 + mensagem de sucesso"
    
    try:
        payload = {
            "email": "teste1@gmail.com",
            "senha": "senha123",
            "nome": "Usuário Teste"
        }
        
        response = requests.post(
            f"{runner.base_url}/api/cadastro",  # 🔧 ALTERE ENDPOINT
            json=payload,
            timeout=TIMEOUT
        )
        
        resultado.resultado_obtido = f"Status {response.status_code}"
        resultado.evidencia = response.text[:200]
        
        # ✅ Validação
        if response.status_code == 201 or response.status_code == 200:
            resultado.status = "PASS"
            runner.usuarios_criados.append(payload["email"])
        else:
            resultado.status = "FAIL"
            resultado.erro = f"Status inesperado: {response.status_code}"
    
    except Exception as e:
        resultado.status = "FAIL"
        resultado.erro = str(e)
    
    runner.adicionar_resultado(resultado)

def CT_002_Login_Credenciais_Corretas(runner: TestRunner):
    """CT-002: Login com email e senha corretos"""
    resultado = TestResult("CT-002", "Login com credenciais corretas", "Validação")
    resultado.resultado_esperado = "Status 200 + token/sessão"
    
    try:
        # Primeiro cria um usuário
        usuario = {
            "email": "teste1@gmail.com",
            "senha": "senha123"
        }
        
        # Registra
        requests.post(f"{runner.base_url}/api/login", json=usuario, timeout=TIMEOUT)
        
        # Tenta fazer login
        response = requests.post(
            f"{runner.base_url}/api/login",  # 🔧 ALTERE ENDPOINT
            json=usuario,
            timeout=TIMEOUT
        )
        
        resultado.resultado_obtido = f"Status {response.status_code}"
        resultado.evidencia = response.text[:200]
        
        if response.status_code == 200:
            resultado.status = "PASS"
        else:
            resultado.status = "FAIL"
            resultado.erro = f"Status inesperado: {response.status_code}"
    
    except Exception as e:
        resultado.status = "FAIL"
        resultado.erro = str(e)
    
    runner.adicionar_resultado(resultado)

def CT_003_Login_Senha_Incorreta(runner: TestRunner):
    """CT-003: Login com senha incorreta"""
    resultado = TestResult("CT-003", "Login com senha incorreta", "Validação de Erro")
    resultado.resultado_esperado = "Status 401/403 + mensagem de erro"
    
    try:
        # Primeiro cria um usuário
        usuario = {
            "email": "erro_teste@example.com",
            "senha": "senha_correta"
        }
        requests.post(f"{runner.base_url}/api/cadastro", json=usuario, timeout=TIMEOUT)
        
        # Tenta login com senha errada
        response = requests.post(
            f"{runner.base_url}/api/login",
            json={"email": usuario["email"], "senha": "senha_errada"},
            timeout=TIMEOUT
        )
        
        resultado.resultado_obtido = f"Status {response.status_code}"
        resultado.evidencia = response.text[:200]
        
        # Deve retornar erro (401, 403 ou similar)
        if response.status_code >= 400:
            resultado.status = "PASS"
        else:
            resultado.status = "FAIL"
            resultado.erro = f"Sistema aceitou senha incorreta!"
    
    except Exception as e:
        resultado.status = "FAIL"
        resultado.erro = str(e)
    
    runner.adicionar_resultado(resultado)

def CT_004_Login_Email_Inexistente(runner: TestRunner):
    """CT-004: Login com email inexistente"""
    resultado = TestResult("CT-004", "Login com email inexistente", "Validação de Erro")
    resultado.resultado_esperado = "Status 401/403 + mensagem de erro"
    
    try:
        response = requests.post(
            f"{runner.base_url}/api/login",
            json={"email": "naoexiste@example.com", "senha": "qualquer"},
            timeout=TIMEOUT
        )
        
        resultado.resultado_obtido = f"Status {response.status_code}"
        resultado.evidencia = response.text[:200]
        
        if response.status_code >= 400:
            resultado.status = "PASS"
        else:
            resultado.status = "FAIL"
            resultado.erro = f"Email inexistente foi aceito!"
    
    except Exception as e:
        resultado.status = "FAIL"
        resultado.erro = str(e)
    
    runner.adicionar_resultado(resultado)

# ============================================================================
# 🧪 TESTES DO MÓDULO DE CURSOS
# ============================================================================

def CT_005_Cadastro_Curso_Sem_Titulo(runner: TestRunner):
    """CT-005: Cadastro de curso com título obrigatório vazio"""
    resultado = TestResult("CT-005", "Cadastro de curso sem título", "Valor Nulo")
    resultado.resultado_esperado = "Status 400 + erro 'título obrigatório'"
    
    try:
        payload = {
            "titulo": "",  # ❌ VAZIO
            "descricao": "Descrição válida",
            "preco": 99.90,
            "categoria": "Tecnologia"
        }
        
        response = requests.post(
            f"{runner.base_url}/api/cursos",  # 🔧 ALTERE ENDPOINT
            json=payload,
            timeout=TIMEOUT
        )
        
        resultado.resultado_obtido = f"Status {response.status_code}"
        resultado.evidencia = response.text[:200]
        
        if response.status_code == 400 or response.status_code >= 400:
            resultado.status = "PASS"
        else:
            resultado.status = "FAIL"
            resultado.erro = "Sistema aceitou curso sem título!"
    
    except Exception as e:
        resultado.status = "FAIL"
        resultado.erro = str(e)
    
    runner.adicionar_resultado(resultado)

def CT_006_Cadastro_Curso_Preco_Negativo(runner: TestRunner):
    """CT-006: Cadastro de curso com preço negativo"""
    resultado = TestResult("CT-006", "Cadastro de curso com preço negativo", "Valor Negativo")
    resultado.resultado_esperado = "Status 400 + erro 'preço inválido'"
    
    try:
        payload = {
            "titulo": "Python Avançado",
            "descricao": "Descrição válida",
            "preco": -50.00,  # ❌ NEGATIVO
            "categoria": "Tecnologia"
        }
        
        response = requests.post(
            f"{runner.base_url}/api/cursos",
            json=payload,
            timeout=TIMEOUT
        )
        
        resultado.resultado_obtido = f"Status {response.status_code}"
        resultado.evidencia = response.text[:200]
        
        if response.status_code >= 400:
            resultado.status = "PASS"
        else:
            resultado.status = "FAIL"
            resultado.erro = "Sistema aceitou preço negativo!"
    
    except Exception as e:
        resultado.status = "FAIL"
        resultado.erro = str(e)
    
    runner.adicionar_resultado(resultado)

def CT_007_Cadastro_Curso_Descricao_Limite(runner: TestRunner):
    """CT-007: Cadastro com descrição excedendo 5000 caracteres"""
    resultado = TestResult("CT-007", "Descrição excede limite de 5000 caracteres", "Limite")
    resultado.resultado_esperado = "Status 400 + erro 'limite de caracteres'"
    
    try:
        descricao_grande = "x" * 5001  # ❌ MAIS DE 5000
        
        payload = {
            "titulo": "Curso Teste",
            "descricao": descricao_grande,
            "preco": 99.90,
            "categoria": "Tecnologia"
        }
        
        response = requests.post(
            f"{runner.base_url}/api/cursos",
            json=payload,
            timeout=TIMEOUT
        )
        
        resultado.resultado_obtido = f"Status {response.status_code}"
        resultado.evidencia = f"Descrição com {len(descricao_grande)} caracteres"
        
        if response.status_code >= 400:
            resultado.status = "PASS"
        else:
            resultado.status = "FAIL"
            resultado.erro = "Sistema aceitou descrição com mais de 5000 caracteres!"
    
    except Exception as e:
        resultado.status = "FAIL"
        resultado.erro = str(e)
    
    runner.adicionar_resultado(resultado)

# ============================================================================
# 🚀 EXECUÇÃO PRINCIPAL
# ============================================================================

def main():
    print("\n" + "="*70)
    print("🤖 TESTES AUTOMATIZADOS - WEBEDC")
    print("="*70)
    print(f"🌐 URL Base: {BASE_URL}")
    print(f"⏰ Início: {datetime.now().strftime('%H:%M:%S')}")
    print("="*70 + "\n")
    
    runner = TestRunner(BASE_URL)
    
    print("📋 Executando Testes...\n")
    
    # Testes do Módulo de Usuários
    print("--- MÓDULO DE USUÁRIOS ---")
    CT_001_Cadastro_Usuario_Valido(runner)
    CT_002_Login_Credenciais_Corretas(runner)
    CT_003_Login_Senha_Incorreta(runner)
    CT_004_Login_Email_Inexistente(runner)
    
    # Testes do Módulo de Cursos
    print("\n--- MÓDULO DE CURSOS ---")
    CT_005_Cadastro_Curso_Sem_Titulo(runner)
    CT_006_Cadastro_Curso_Preco_Negativo(runner)
    CT_007_Cadastro_Curso_Descricao_Limite(runner)
    
    # Resumo e Relatório
    print("\n")
    runner.exibir_resumo()
    runner.salvar_relatorio(RELATORIO_FILE)
    
    print("✅ Testes concluídos!")
    print(f"📄 Verifique o relatório: {RELATORIO_FILE}\n")

if __name__ == "__main__":
    main()
