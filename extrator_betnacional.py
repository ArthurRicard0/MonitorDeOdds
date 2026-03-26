from playwright.sync_api import sync_playwright
import time
import pandas as pd 

# Configurações para mostrar a tabela completa no terminal, sem cortes
pd.set_option('display.max_rows', None) 
pd.set_option('display.max_columns', None) 
pd.set_option('display.max_colwidth', None)

def extrair_odds_para_dataframe():

    url = "https://betnacional.bet.br/sport-event/1/2"
    with sync_playwright() as p:
        print(" Iniciando o robô...")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print(f" Acessando {url}...")
        page.goto(url)

        print(" Aguardando o site carregar inicialmente...")
        page.wait_for_load_state("networkidle") 
        time.sleep(3) 

        print("📜 Iniciando a leitura dinâmica (Lendo enquanto rola)...")
        rolagens = 10 
        pixels_por_rolagem = 800 
        
        dados_extraidos = []
        # O 'Set' vai salvar os jogos que o robo ja viu, para evitar repetições.
        jogos_vistos = set() 

        # O loop agora começa ANTES do primeiro scroll. 
        # Lemos a página logo que ela abre para pegar o topo
        for i in range(rolagens + 1): 
            # 1. Pega os jogos que estão na tela EXATAMENTE AGORA
            jogos = page.locator('[data-testid="event-list-item"]').all()
            
            for jogo in jogos:
                try:
                    times = jogo.locator('[data-testid="event-list-item-team"]').all()
                    odds = jogo.locator('[data-testid="event-list-item-odd-text"]').all()
                    
                    if len(times) == 2 and len(odds) == 3:
                        time_casa = times[0].inner_text().strip()
                        time_fora = times[1].inner_text().strip()
                        
                        # Criamos um RG único para o jogo (Ex: "Flamengo-Corinthians")
                        rg_do_jogo = f"{time_casa}-{time_fora}"
                        
                        # Se o jogo ainda não foi visto, processa. Caso contrário, pula para o próximo.
                        if rg_do_jogo not in jogos_vistos:
                            odd_1 = odds[0].inner_text().strip()
                            odd_x = odds[1].inner_text().strip()
                            odd_2 = odds[2].inner_text().strip()
                            
                            jogo_dict = {
                                "Casa": time_casa,
                                "Fora": time_fora,
                                "Odd_1": odd_1,
                                "Odd_X": odd_x,
                                "Odd_2": odd_2,
                                "Casa_Aposta": "Betnacional"
                            }
                            dados_extraidos.append(jogo_dict)
                            # Guarda nos jogos vistos para não repetir no futuro
                            jogos_vistos.add(rg_do_jogo) 
                            
                except Exception as e:
                    continue
            
            # 2. Depois de ler o que estava na tela, simulamos o scroll para a próxima etapa
            if i < rolagens:
                page.evaluate(f"window.scrollBy(0, {pixels_por_rolagem})")
                time.sleep(1.5)

        print(f"✅ Extração concluída. Encontramos {len(dados_extraidos)} jogos ÚNICOS.")
        browser.close()

        print("\n📊 Transformando dados em Tabela (DataFrame)...")
        df = pd.DataFrame(dados_extraidos)

        if not df.empty:
            df['Odd_1'] = pd.to_numeric(df['Odd_1'], errors='coerce')
            df['Odd_X'] = pd.to_numeric(df['Odd_X'], errors='coerce')
            df['Odd_2'] = pd.to_numeric(df['Odd_2'], errors='coerce')
            return df
        else:
            print(" A tabela está vazia. Algo deu errado na extração.")
            return None


#(INTERFACE DE PESQUISA NO TERMINAL)
if __name__ == "__main__":
    print("Bem-vindo ao Monitor de Odds!")
    
    time_pesquisado = input(" Digite o nome do time que deseja pesquisar (ou pressione Enter para ver todos): ").strip()
    
    tabela_completa = extrair_odds_para_dataframe()
    
    if tabela_completa is not None:
        if time_pesquisado == "":
            print("\n Mostrando todos os jogos disponíveis:")
            print(tabela_completa.to_markdown(index=False))
        else:
            print(f"\n Buscando por: '{time_pesquisado}'...")
            
            tabela_filtrada = tabela_completa[
                tabela_completa['Casa'].str.contains(time_pesquisado, case=False, na=False) |
                tabela_completa['Fora'].str.contains(time_pesquisado, case=False, na=False)
            ]
            
            if tabela_filtrada.empty:
                print(f"Nenhum jogo encontrado para '{time_pesquisado}' nas próximas 24h da Betnacional.")
            else:
                print(f"\n Jogo(s) Encontrado(s) para {time_pesquisado}:")
                print(tabela_filtrada.to_markdown(index=False))