from datetime import datetime
import time
import queue
import threading
import socket
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Algoritmo Centralizado de Exclusão Mútua Distribuída")
    parser.add_argument(
        '--role', choices=['coordenador', 'processo'], required=True, help='Tipo de processo')
    parser.add_argument('--F', type=int, required=True,
                        help='Tamanho fixo da mensagem')
    parser.add_argument(
        '--ip', type=str, help='IP do coordenador (para processo)')
    parser.add_argument('--port', type=int, required=True,
                        help='Porta do coordenador')
    parser.add_argument(
        '--n', type=int, help='Número de processos (para coordenador)')
    parser.add_argument(
        '--r', type=int, help='Repetições por processo (para processo)')
    parser.add_argument(
        '--k', type=int, help='Tempo de espera na região crítica (para processo)')
    parser.add_argument('--process_id', type=int,
                        help='Identificador do processo (para processo)')
    args = parser.parse_args()

    if args.role == 'coordenador':
        print("Executando como coordenador...")
        run_coordenador(args.F, args.port, args.n)
    elif args.role == 'processo':
        print("Executando como processo...")
        run_processo(args.F, args.ip, args.port,
                     args.r, args.k, args.process_id)


# ================= COORDENADOR ===================


def log_message(logfile, msg_type, process_id, info):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    with open(logfile, 'a') as f:
        f.write(f"{now} | {msg_type} | {process_id} | {info}\n")


class Coordinator:
    def __init__(self, F, port, n):
        self.F = F
        self.port = port
        self.n = n
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', port))
        self.server_socket.listen(n)
        self.connections = {}
        self.request_queue = queue.Queue()
        self.attended_count = {}
        self.lock = threading.Lock()
        self.running = True
        self.logfile = 'coordenador_log.txt'
        with open(self.logfile, 'w', encoding="utf-8") as f:
            f.write("Log do Coordenador\n")
            f.write(
                "Formato: Timestamp | Tipo | ID do Processo | Informação: id tipo de mensagem|id processo|mensagem\n")
        open('resultado.txt', 'w')

    def accept_connections(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_process,
                                 args=(conn,)).start()
            except Exception as e:
                if self.running:
                    print(f"[accept_connections] Erro: {e}")
                break

    def handle_process(self, conn):
        import random
        process_id = None
        while self.running:
            try:
                data = conn.recv(self.F)
                if not data:
                    break
                msg = data.decode().strip()
                parts = msg.split('|')
                msg_type = parts[0]
                process_id = parts[1] if len(parts) > 1 else 'unknown'
                if msg_type == '1':  # REQUEST
                    with self.lock:
                        log_message(self.logfile, msg_type,
                                    process_id, f"RECEBIDO: {msg}")
                        if self.request_queue.empty():
                            self.request_queue.put((process_id, conn))
                            print(self.request_queue.queue)
                            base = f"2|{process_id}|"
                            fill_len = self.F - len(base)
                            filler = ''.join(random.choices('0123456789', k=fill_len))
                            grant_msg = base + filler
                            try:
                                conn.sendall(grant_msg.encode())
                                log_message(self.logfile, '2', process_id,
                                            f"ENVIADO: {grant_msg}")
                            except Exception as e:
                                print(f"[handle_process] Erro ao enviar grant: {e}")
                        else:
                            self.request_queue.put((process_id, conn))
                            print(self.request_queue.queue)
                    time.sleep(0.05)
                elif msg_type == '3':  # RELEASE
                    with self.lock: 
                        self.request_queue.get() #remove da fila
                        print(self.request_queue.queue)
                        log_message(self.logfile, msg_type,
                                    process_id, f"RECEBIDO: {msg}")
                        self.attended_count[process_id] = self.attended_count.get(
                            process_id, 0) + 1
                        if not self.request_queue.empty():
                            process_id, conn = self.request_queue.queue[0]
                            base = f"2|{process_id}|"
                            fill_len = self.F - len(base)
                            filler = ''.join(random.choices('0123456789', k=fill_len))
                            grant_msg = base + filler
                            try:
                                conn.sendall(grant_msg.encode())
                                log_message(self.logfile, '2', process_id,
                                            f"ENVIADO: {grant_msg}")
                            except Exception as e:
                                print(f"[handle_process] Erro ao enviar grant: {e}")
                    time.sleep(0.05)
            except Exception as e:
                if self.running:
                    print(f"[handle_process] Erro: {e}")
                break

    def interface(self):
        try:
            while self.running:
                try:
                    cmd = input(
                        "[coordenador] Comandos: \n[1]fila\n[2]contagem\n[3]sair\n").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nEncerrando interface do coordenador...")
                    self.running = False
                    self.server_socket.close()
                    break

                if cmd == '1':
                    with self.lock:
                        fila = list(self.request_queue.queue)
                        print("Fila de pedidos:", [pid for pid, _ in fila])
                elif cmd == '2':
                    with self.lock:
                        print("Atendimentos por processo:", self.attended_count)
                elif cmd == '3':
                    self.running = False
                    self.server_socket.close()
                    print("Encerrando coordenador...")
                    break
                else:
                    print("Comando não reconhecido")
        except Exception as e:
            print(f"[interface] Finalizando por exceção: {e}")


def run_coordenador(F, port, n):
    coord = Coordinator(F, port, n)
    threads = [
        threading.Thread(target=coord.accept_connections),
        threading.Thread(target=coord.interface)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

# ================= PROCESSO ===================


def run_processo(F, ip, port, r, k, process_id):
    import os
    import time
    import random
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))
    for i in range(r):
        base = f"1|{process_id}|"
        fill_len = F - len(base)
        filler = ''.join(random.choices('0123456789', k=fill_len))
        req_msg = base + filler
        s.sendall(req_msg.encode())
        # Aguarda GRANT
        data = s.recv(F)
        grant = data.decode().strip()
        # Região crítica
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        with open('resultado.txt', 'a') as f:
            f.write(f"{process_id} {now}\n")
        dorme = random.randint(1,k)+random.random()
        print(f"{process_id}| dormindo por: {dorme}")
        time.sleep(dorme)
        base = f"3|{process_id}|"

        fill_len = F - len(base)
        filler = ''.join(random.choices('0123456789', k=fill_len))
        rel_msg = base + filler
        s.sendall(rel_msg.encode())
    s.close()


if __name__ == '__main__':
    main()