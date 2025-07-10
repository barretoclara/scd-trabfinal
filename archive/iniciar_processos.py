import subprocess
import sys
import time
from processo import Processo
import threading

def iniciar_processos_manual(num_processos=3, repeticoes=5):
    """
    Inicia os processos manualmente usando threads (mesmo arquivo)
    """
    open('resultado.txt', 'w').close()  # Limpa o arquivo de resultados
    
    processos = []
    for i in range(num_processos):
        p = Processo(i+1, repeticoes=repeticoes)
        t = threading.Thread(target=p.iniciar)
        processos.append(t)
        t.start()
        time.sleep(0.1)  # Pequeno atraso entre inícios
    
    for t in processos:
        t.join()
    
    print("\nTodos os processos terminaram")
    with open('resultado.txt', 'r') as arquivo:
        print("\nConteúdo de resultado.txt:")
        print(arquivo.read())

def iniciar_processos_em_terminal(num_processos=3, repeticoes=5):
    """
    Inicia os processos em terminais separados (visualização independente)
    """
    open('resultado.txt', 'w').close()  # Limpa o arquivo de resultados
    
    comandos = []
    for i in range(num_processos):
        cmd = f"python -c \"from processo import Processo; Processo({i+1}, repeticoes={repeticoes}).iniciar()\""
        
        # Para Windows
        if sys.platform == 'win32':
            subprocess.Popen(['start', 'cmd', '/k', cmd], shell=True)
        # Para Linux/MacOS
        else:
            subprocess.Popen(['x-terminal-emulator', '-e', cmd])
        
        time.sleep(0.3)  # Atraso maior para abrir terminais

if __name__ == "__main__":
    print("1 - Iniciar processos em threads (mesmo terminal)")
    print("2 - Iniciar processos em terminais separados")
    opcao = input("Escolha uma opção: ")
    
    num_p = int(input("Número de processos: ") or 3)
    rep = int(input("Número de repetições: ") or 5)
    
    if opcao == '1':
        iniciar_processos_manual(num_p, rep)
    elif opcao == '2':
        iniciar_processos_em_terminal(num_p, rep)
    else:
        print("Opção inválida")