from playwright.sync_api import sync_playwright
import time
import pandas as pd


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)

def extrair_odds_superbet():
    url = "https://superbet.bet.br/apostas/futebol/hoje"

    with sync_playwright() as p:
        print("Iniciando o robô na Superbet...")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print(f"Acessando {url}...")
        page.goto(url)

        
        print("⏳ Aguardando os jogos aparecerem na tela...")
        try:
            # O robô fica vigiando o HTML. Assim que o primeiro time aparecer, ele avança
            # timeout=15000 significa que ele desiste se a página ficar em branco por 15 segundos
            page.wait_for_selector('.e2e-event-team1-name', timeout=15000)
            
            print("Fechando pop-ups")
            page.keyboard.press("Escape")
            time.sleep(2) 
            
        except Exception as e:
            print("Demorou muito para carregar ou a Superbet mudou o layout.")
            browser.close()
            return None

        print("📜 Iniciando a leitura dinâmica (Lendo enquanto rola)...")
        rolagens = 20 
        pixels_por_rolagem = 1000
        
        dados_extraidos = []
        jogos_vistos = set() 

        for i in range(rolagens + 1): 
            # 1. Encontramos todas as partes "filhas" que sabemos que existem com certeza
            cards_principais = page.locator('.event-card__main-content').all()
            
            for card in cards_principais:
                try:
                    # Mandamos o Playwright subir um nível (xpath=..) para pegar a "Caixa Pai",
                    bloco = card.locator('xpath=..')
                    
                    time_casa = bloco.locator('.e2e-event-team1-name').inner_text().strip()
                    time_fora = bloco.locator('.e2e-event-team2-name').inner_text().strip()
                    
                    rg_do_jogo = f"{time_casa}-{time_fora}"
                    
                    if rg_do_jogo not in jogos_vistos:
                        botoes_odds = bloco.locator('.e2e-odd-pick').all()
                        
                        if len(botoes_odds) >= 3:
                            odd_1 = botoes_odds[0].locator('.odd-button__odd-value').inner_text().strip()
                            odd_x = botoes_odds[1].locator('.odd-button__odd-value').inner_text().strip()
                            odd_2 = botoes_odds[2].locator('.odd-button__odd-value').inner_text().strip()
                            
                            dados_extraidos.append({
                                "Casa": time_casa,
                                "Fora": time_fora,
                                "Odd_1": odd_1,
                                "Odd_X": odd_x,
                                "Odd_2": odd_2,
                                "Casa_Aposta": "Superbet" 
                            })
                            jogos_vistos.add(rg_do_jogo) 
                            
                except Exception as e:
                    continue
            
            if i < rolagens:
                page.evaluate(f"window.scrollBy(0, {pixels_por_rolagem})")
                time.sleep(1.5)

        print(f"Extração concluída. Encontramos {len(dados_extraidos)} jogos ÚNICOS na Superbet.")
        browser.close()

        print("\nMontando a tabela de dados...")
        df = pd.DataFrame(dados_extraidos)

        if not df.empty:
            df['Odd_1'] = pd.to_numeric(df['Odd_1'], errors='coerce')
            df['Odd_X'] = pd.to_numeric(df['Odd_X'], errors='coerce')
            df['Odd_2'] = pd.to_numeric(df['Odd_2'], errors='coerce')
            return df
        else:
            print(" A tabela está vazia. Algo deu errado na extração.")
            return None

if __name__ == "__main__":
    tabela_superbet = extrair_odds_superbet()
    if tabela_superbet is not None:
        print("\nJogos capturados da Superbet:")
        print(tabela_superbet.to_markdown(index=False))