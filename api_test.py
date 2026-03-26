import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

# Carrega as variáveis do .env
load_dotenv()
API_KEY = os.getenv("ODDS_API_KEY")

# --- CONFIGURAÇÕES DO NEGÓCIO ---

# Mudamos de Brasileirão para "upcoming" (próximos) ou "soccer" geral
# para garantir que vamos encontrar jogos acontecendo HOJE.
SPORT = "soccer" 
REGIONS = "eu,uk,us"
MARKETS = "h2h"
ODDS_FORMAT = "decimal"

# NOSSA LISTA DE PERMISSÃO (Whitelist)
# Importante: Nem todas as casas brasileiras estão na The Odds API.
# Coloquei aqui as que costumam aparecer (como Betano e Bet365). 
# Você deve escrever exatamente como a API retorna (maiúsculas/minúsculas).
CASAS_PERMITIDAS = ["Betano", "bet365", "SuperSport", "KTO"]

def testar_conexao_api():
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    
    parametros = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT
    }

    print("Buscando jogos e filtrando dados...\n")
    resposta = requests.get(url, params=parametros)

    if resposta.status_code == 200:
        dados = resposta.json()
        
        # Descobrindo que dia é hoje e amanhã no fuso horário do Brasil (UTC-3)
        fuso_brasil = timezone(timedelta(hours=-3))
        hoje_brasil = datetime.now(fuso_brasil).date()
        amanha_brasil = hoje_brasil + timedelta(days=1)
        
        jogos_encontrados_no_periodo = 0

        for jogo in dados:
            # 1. TRATANDO A DATA
            # A API manda a data assim: "2026-03-25T21:30:00Z" (O 'Z' significa UTC)
            # O código abaixo transforma esse texto em uma data real do Python
            data_utc = datetime.strptime(jogo['commence_time'], "%Y-%m-%dT%H:%M:%SZ")
            data_utc = data_utc.replace(tzinfo=timezone.utc) # Avisa o Python que isso é UTC
            
            # Converte para o horário do Brasil
            data_jogo_brasil = data_utc.astimezone(fuso_brasil)
            data_apenas_dia = data_jogo_brasil.date()

            # REGRA DE NEGÓCIO: Só me mostre se o jogo for hoje ou amanhã
            if data_apenas_dia == hoje_brasil or data_apenas_dia == amanha_brasil:
                jogos_encontrados_no_periodo += 1
                
                print(f"⚽ {jogo['home_team']} x {jogo['away_team']}")
                print(f"🕒 Data/Hora (Brasil): {data_jogo_brasil.strftime('%d/%m/%Y %H:%M')}")
                print(f"🏆 Esporte/Liga: {jogo['sport_title']}")
                
                # 2. FILTRANDO AS CASAS DE APOSTAS
                casas_impressas = 0 # Contador para sabermos se achou alguma casa da nossa lista
                
                for casa in jogo['bookmakers']:
                    nome_casa = casa['title']
                    
                    # A MÁGICA DO FILTRO: Se o nome estiver na nossa lista, processa.
                    if nome_casa in CASAS_PERMITIDAS:
                        casas_impressas += 1
                        mercado = casa['markets'][0]
                        odds = mercado['outcomes']
                        
                        print(f"   🏠 {nome_casa}:")
                        # Imprime as odds (Vitória 1, Empate, Vitória 2)
                        for odd in odds:
                            print(f"      -> {odd['name']}: {odd['price']}")
                
                # Se nenhuma casa da nossa lista cobrir esse jogo, avisamos.
                if casas_impressas == 0:
                    print("   ⚠️ Nenhuma das casas que monitoramos tem odds para este jogo ainda.")
                    
                print("-" * 50)
                
                # Para não poluir demais o terminal no nosso teste, vamos parar 
                # o código depois de imprimir os 3 primeiros jogos que baterem com a regra.
                if jogos_encontrados_no_periodo >= 3:
                    break
                    
        if jogos_encontrados_no_periodo == 0:
             print("Nenhum jogo encontrado para hoje ou amanhã nas ligas retornadas.")

    else:
        print(f"Erro na requisição: {resposta.status_code}")

if __name__ == "__main__":
    testar_conexao_api()