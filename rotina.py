import subprocess
import random
import time

n = 3  # número de processos
r = 5  # repetições por processo
k = 2  # segundos na região crítica
F = 10  # tamanho fixo da mensagem
ip = '127.0.0.1'
port = 5000

ids = random.sample(range(1, 100), n)
procs = []

try:
    # Inicia o coordenador
    procs.append(subprocess.Popen([
        'python', 'invocador.py',
        '--role', 'coordenador',
        '--F', str(F),
        '--port', str(port),
        '--n', str(n)
    ]))
    time.sleep(1)  # Aguardar coordenador iniciar

    # Inicia os processos
    for process_id in ids:
        procs.append(subprocess.Popen([
            'python', 'invocador.py',
            '--role', 'processo',
            '--F', str(F),
            '--ip', ip,
            '--port', str(port),
            '--r', str(r),
            '--k', str(k),
            '--process_id', str(process_id)
        ]))

    for p in procs:
        p.wait()

except KeyboardInterrupt:
    print("\nParando todos os processos...")
    for p in procs:
        p.terminate()
    print("Todos os processos foram parados.")