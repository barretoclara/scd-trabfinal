n = 3  # numero de processos
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
    # Start coordinator
    procs.append(subprocess.Popen([
        'python', 'main.py',
        '--role', 'coordenador',
        '--F', str(F),
        '--port', str(port),
        '--n', str(n)
    ]))
    time.sleep(1)  # Give coordinator a moment to start

    # Start processes
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