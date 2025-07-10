import subprocess
import random
import time

n = 3  # numero de processos
r = 5  # repetições
k = 2  # segundos em região crítica
F = 10 # message size
ip = '127.0.0.1'
port = 5000

ids = random.sample(range(1, 100), n)
procs = []

try:
    procs.append(subprocess.Popen([
        'python', 'invocador.py',
        '--role', 'coordenador',
        '--F', str(F),
        '--port', str(port),
        '--n', str(n)
    ]))
    time.sleep(1) # Aguardar coordenador iniciar

    # Iniciar processos
    for process_id in ids:
        procs.append(subprocess.Popen([
            'python', 'main.py',
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