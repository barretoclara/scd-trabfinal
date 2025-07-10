import socket
import time
import random
import os
from threading import Thread

class Processo:
    def __init__(self, id_processo, host_coordenador='localhost', porta_coordenador=5001, repeticoes=5, atraso=2):
        self.id_processo = str(id_processo)
        self.host_coordenador = host_coordenador
        self.porta_coordenador = porta_coordenador
        self.repeticoes = repeticoes
        self.atraso = atraso
        
    def criar_mensagem(self, tipo_msg, id_processo):
        """Cria mensagem no formato tipo|id|padding (10 bytes)"""
        return f"{tipo_msg}|{id_processo}|".ljust(10, '0').encode()
        
    def acessar_regiao_critica(self):
        """Acessa a região crítica e registra no arquivo compartilhado"""
        try:
            # Garante que o arquivo existe
            if not os.path.exists('resultado.txt'):
                open('resultado.txt', 'w').close()
                
            with open('resultado.txt', 'a') as arquivo:
                tempo_atual = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + f".{int(time.time() * 1000) % 1000:03d}"
                linha = f"Processo {self.id_processo} - {tempo_atual}\n"
                arquivo.write(linha)
                arquivo.flush()
                os.fsync(arquivo.fileno())  # Força escrita no disco
            time.sleep(self.atraso)
        except Exception as e:
            print(f"Processo {self.id_processo} erro ao acessar região crítica: {e}")
    
    def iniciar(self):
        """Método principal para execução do processo"""
        print(f"Processo {self.id_processo} iniciando...")
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                # Configura timeout e conecta ao coordenador
                s.settimeout(10.0)
                s.connect((self.host_coordenador, self.porta_coordenador))
                print(f"Processo {self.id_processo} conectado!")
                
                # Envia mensagem de identificação
                s.sendall(self.criar_mensagem(0, self.id_processo))
                time.sleep(0.5)  # Pequeno delay para sincronização
                
                # Loop principal de requisições
                for i in range(self.repeticoes):
                    tentativas = 3
                    while tentativas > 0:
                        try:
                            s.settimeout(8.0)
                            print(f"Processo {self.id_processo} enviando REQUISICAO {i+1}/{self.repeticoes}")
                            s.sendall(self.criar_mensagem(1, self.id_processo))
                            
                            print(f"Processo {self.id_processo} aguardando CONCEDE...")
                            mensagem_concede = s.recv(10).decode()
                            
                            if mensagem_concede.startswith('2|'):  # Mensagem GRANT
                                print(f"Processo {self.id_processo} recebeu CONCEDE")
                                self.acessar_regiao_critica()
                                
                                s.settimeout(4.0)
                                print(f"Processo {self.id_processo} enviando LIBERA")
                                s.sendall(self.criar_mensagem(3, self.id_processo))
                                break  # Sai do loop de tentativas
                            
                            time.sleep(random.uniform(1.0, 2.0))
                            
                        except socket.timeout:
                            tentativas -= 1
                            print(f"Processo {self.id_processo} timeout operação {i+1}, tentativas restantes: {tentativas}")
                            if tentativas == 0:
                                print(f"Processo {self.id_processo} falhou na operação {i+1} após 3 tentativas")
                                break
                            continue
                    
                    if tentativas == 0:
                        break  # Se esgotou todas as tentativas, sai do loop
                    
                    # Intervalo entre requisições bem-sucedidas
                    time.sleep(random.uniform(0.5, 1.5))
                
                print(f"Processo {self.id_processo} concluído com sucesso!")
                
            except Exception as e:
                print(f"Processo {self.id_processo} falhou: {e}")
            
            finally:
                # Encerramento limpo
                try:
                    # Notifica o coordenador sobre a desconexão
                    s.settimeout(2.0)
                    s.sendall(self.criar_mensagem(4, self.id_processo))  # Tipo 4 = DESCONEXAO
                    time.sleep(0.5)
                except:
                    pass
                
                try:
                    # Fecha a conexão de forma adequada
                    s.shutdown(socket.SHUT_RDWR)
                    s.close()
                except:
                    pass


if __name__ == "__main__":
    # Exemplo de uso direto
    processo = Processo(1, repeticoes=3)
    processo.iniciar()