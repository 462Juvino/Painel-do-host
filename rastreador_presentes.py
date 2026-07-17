import asyncio
import websockets
import json
import os
import sys  # <--- FALTAVA ESSA LINHA AQUI!
from datetime import datetime

# O arquivo onde a mina de ouro vai ser salva
ARQUIVO_JSON = "catalogo_presentes_live.json"

# ... (o resto do código continua igualzinho) ...


def carregar_catalogo():
    """Carrega o arquivo antigo para não perder nada, ou cria um novo se não existir."""
    if os.path.exists(ARQUIVO_JSON):
        try:
            with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Aviso ao ler JSON: {e}")
            return {}
    return {}


def salvar_catalogo(dados):
    """Salva o JSON formatado bonitinho para você conseguir ler."""
    try:
        with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar: {e}")


async def monitorar_tikfinity():
    catalogo = carregar_catalogo()
    print("🕵️  RASTREADOR DE PRESENTES INICIADO!")
    print(f"📁 Salvando tudo no arquivo: {ARQUIVO_JSON}")
    print("🔄 Conectando ao TikFinity (ws://127.0.0.1:21213)...")

    while True:
        try:
            async with websockets.connect("ws://127.0.0.1:21213/") as ws:
                print("✅ Conectado com sucesso! Aguardando a galera mandar presente...\n")

                async for message in ws:
                    try:
                        pacote = json.loads(message)
                        event = pacote.get("event")
                        data = pacote.get("data", {})

                        # Verifica se é um evento de presente
                        if event in ["gift", "sendGift"] and data:
                            gift_name = data.get("giftName", "Desconhecido")
                            moedas = data.get("diamondCount", data.get("coinCount", 0))

                            print(f"🎁 PEGAMOS UM! Nome: [{gift_name}] | Moedas: {moedas}")

                            # Adiciona ou atualiza no catálogo
                            if gift_name not in catalogo:
                                catalogo[gift_name] = {
                                    "nome_original_tiktok": gift_name,
                                    "nome_limpo_pro_jogo": gift_name.lower().strip(),
                                    "valor_moedas": moedas,
                                    "vezes_recebido": 1,
                                    "ultima_vez": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                                    "dados_completos": data  # Salva TODAS as infos cruas que o TikTok manda
                                }
                            else:
                                catalogo[gift_name]["vezes_recebido"] += 1
                                catalogo[gift_name]["ultima_vez"] = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                                catalogo[gift_name]["dados_completos"] = data  # Atualiza para ter sempre o mais recente

                            # Salva no arquivo na mesma hora
                            salvar_catalogo(catalogo)

                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        print(f"Erro ao processar mensagem: {e}")

        except Exception as e:
            print("❌ TikFinity não encontrado. Verifique se ele está aberto.")
            print("⏳ Tentando reconectar em 5 segundos...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    # Garante que caracteres especiais funcionem no terminal
    if sys.stdout is not None and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    try:
        asyncio.run(monitorar_tikfinity())
    except KeyboardInterrupt:
        print("\n🛑 Rastreador parado pelo usuário.")