import sys
from coordenador import Coordenador
from processo import Processo
import threading
import time

def principal():
    if len(sys.argv) > 1 and sys.argv[1] == 'coordenador':
        coordenador = Coordenador()
        coordenador.iniciar()
    else:
        num_processos = 3 if len(sys.argv) < 2 else int(sys.argv[1])
        repeticoes = 5 if len(sys.argv) < 3 else int(sys.argv[2])
        
        open('resultado.txt', 'w').close()  # Limpar arquivo de resultados
        
        processos = []
        for i in range(num_processos):
            p = Processo(i+1, repeticoes=repeticoes)
            t = threading.Thread(target=p.iniciar)
            processos.append(t)
            t.start()
            time.sleep(0.1)
        
        for t in processos:
            t.join()
        
        print("Todos os processos terminaram")
        with open('resultado.txt', 'r') as arquivo:
            print("\nConteúdo de resultado.txt:")
            print(arquivo.read())

if __name__ == "__main__":
    principal()