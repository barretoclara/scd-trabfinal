import socket
import threading
import time
from queue import Queue
from collections import defaultdict

class Coordenador:
    def __init__(self, host='localhost', porta=5001):
        self.host = host
        self.porta = porta
        self.fila_requisicoes = Queue()
        self.sockets_processos = {}
        self.contagem_acessos = defaultdict(int)
        self.trava = threading.Lock()
        self.executando = True
        
    def iniciar(self):
        thread_conexoes = threading.Thread(target=self.aceitar_conexoes)
        thread_processamento = threading.Thread(target=self.processar_requisicoes)
        thread_interface = threading.Thread(target=self.executar_interface)
        
        thread_conexoes.start()
        thread_processamento.start()
        thread_interface.start()
        
        thread_conexoes.join()
        thread_processamento.join()
        thread_interface.join()
    
    def aceitar_conexoes(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.porta))
            s.listen()
            print(f"Coordenador ouvindo em {self.host}:{self.porta}")
            
            while self.executando:
                try:
                    conexao, endereco = s.accept()
                    mensagem = conexao.recv(10).decode()
                    tipo_msg, id_processo, _ = mensagem.split('|')
                    
                    if tipo_msg == '0':  # Mensagem de identificação
                        with self.trava:
                            self.sockets_processos[id_processo] = conexao
                            print(f"Processo {id_processo} conectado de {endereco}")
                        
                        # Inicia thread para receber mensagens deste processo
                        threading.Thread(
                            target=self.receber_mensagens_processo,
                            args=(id_processo,),
                            daemon=True
                        ).start()
                            
                except Exception as e:
                    if self.executando:  # Só mostra erros se não for desligamento normal
                        print(f"Erro ao aceitar conexão: {str(e)}")
    
    def receber_mensagens_processo(self, id_processo):
        """Thread para receber mensagens de um processo específico"""
        while self.executando:
            try:
                with self.trava:
                    conexao = self.sockets_processos.get(id_processo)
                    if not conexao:
                        break
                        
                    mensagem = conexao.recv(10).decode()
                    if not mensagem:  # Conexão fechada
                        break
                        
                    try:
                        tipo_msg, remetente, _ = mensagem.split('|')
                    except ValueError:
                        self.registrar_log(f"Mensagem malformada do processo {id_processo}: {mensagem}")
                        continue
                        
                    if tipo_msg == '1':  # REQUISICAO
                        self.fila_requisicoes.put(remetente)
                        self.registrar_log(f"REQUISICAO recebida do processo {remetente}")
                    elif tipo_msg == '4':  # DESCONEXAO
                        self.registrar_log(f"Processo {remetente} solicitando desconexão")
                        if remetente in self.sockets_processos:
                            try:
                                self.sockets_processos[remetente].close()
                            except:
                                pass
                            del self.sockets_processos[remetente]
                        break
                        
            except Exception as e:
                if self.executando:
                    print(f"Erro na conexão com processo {id_processo}: {str(e)}")
                break
    
    def processar_requisicoes(self):
        while self.executando:
            try:
                if not self.fila_requisicoes.empty():
                    id_processo = self.fila_requisicoes.get()
                    with self.trava:
                        if id_processo not in self.sockets_processos:
                            continue
                            
                        conexao = self.sockets_processos[id_processo]
                        try:
                            # Testa se a conexão ainda está ativa
                            try:
                                conexao.sendall(b'')  # Teste de conexão
                            except:
                                self.registrar_log(f"Conexão com processo {id_processo} inativa")
                                del self.sockets_processos[id_processo]
                                continue
                                
                            # Envia CONCEDE
                            conexao.settimeout(5.0)
                            conexao.sendall(self.criar_mensagem(2, id_processo))
                            self.contagem_acessos[id_processo] += 1
                            self.registrar_log(f"CONCEDE enviado para processo {id_processo}")
                            
                            # Aguarda LIBERA
                            conexao.settimeout(5.0)
                            mensagem_libera = conexao.recv(10).decode()
                            
                            if mensagem_libera.startswith('3|'):
                                self.registrar_log(f"LIBERA recebido de processo {id_processo}")
                            elif mensagem_libera.startswith('4|'):
                                self.registrar_log(f"Processo {id_processo} solicitando desconexão")
                                del self.sockets_processos[id_processo]
                                
                        except socket.timeout:
                            self.registrar_log(f"Processo {id_processo} não respondeu")
                            continue
                        except ConnectionError:
                            self.registrar_log(f"Conexão com processo {id_processo} perdida")
                            if id_processo in self.sockets_processos:
                                try:
                                    conexao.close()
                                except:
                                    pass
                                del self.sockets_processos[id_processo]
                            continue
                else:
                    time.sleep(0.5)
            except Exception as e:
                self.registrar_log(f"Erro geral no processamento: {e}")
                continue
        
    def executar_interface(self):
        while self.executando:
            try:
                comando = input("\nComandos:\n1 - Fila de requisições\n2 - Contagem de acessos\n3 - Encerrar\n> ")
                
                if comando == '1':
                    print("Fila de requisições:", list(self.fila_requisicoes.queue))
                elif comando == '2':
                    print("Contagem de acessos por processo:", dict(self.contagem_acessos))
                elif comando == '3':
                    self.executando = False
                    print("Encerrando coordenador...")
                    # Fecha todas as conexões
                    with self.trava:
                        for conexao in self.sockets_processos.values():
                            conexao.close()
                        self.sockets_processos.clear()
            except:
                pass
    
    def criar_mensagem(self, tipo_msg, id_processo):
        """Cria mensagem no formato tipo|id|padding (10 bytes)"""
        return f"{tipo_msg}|{id_processo}|".ljust(10, '0').encode()
    
    def registrar_log(self, mensagem):
        print(f"[LOG {time.time()}] {mensagem}")