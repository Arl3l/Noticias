# main.py - Bucle principal usando TU CUENTA PERSONAL de Telegram
import asyncio
import os
from telethon import TelegramClient
from noticiasweb import enviar_noticias, cargar_enlaces_enviados, limpiar_cache_antiguo

# ==================== CONFIGURACIÓN ====================
# Tus datos de Telegram (los mismos que tenías)
api_id = 23640746
api_hash = '1523298c3c49a7213c28f7f3ef060b88'
CHAT_ID = -1002629988101
   
# Tu número de teléfono (con código de país)
# REEMPLAZA con tu número real
MI_NUMERO = '+59177701269'  # ← CAMBIA ESTO A TU NÚMERO REAL

# ==================== CÓDIGO PRINCIPAL ====================
async def main():
    """Bucle principal usando tu cuenta personal de Telegram"""
    print("🚀 INICIANDO BOT DE NOTICIAS BOLIVIA (MODO CUENTA PERSONAL)")
    print("📡 Monitoreando: Protestas, bloqueos, conflictos sociales")
    print("=" * 50)
    
    # Cargar enlaces ya enviados
    cargar_enlaces_enviados()
    
    # Conectar usando TU NÚMERO PERSONAL
    # La primera vez pedirá código y contraseña
    # Las siguientes veces NO pedirá nada
    async with TelegramClient('sesion_personal', api_id, api_hash) as client:
        print("✅ Tu cuenta de Telegram conectada exitosamente")
        
        # Asegurarse que estás logueado (esto no pide nada si ya hay sesión)
        await client.start(phone=MI_NUMERO)
        
        # Enviar mensaje de inicio al grupo
        await client.send_message(
            CHAT_ID, 
            "**BOT DE NOTICIAS BOLIVIA ACTIVADO**\n\n"
            # "📰 Monitoreando 40+ fuentes bolivianas\n"
            # "🔍 Buscando: Protestas, bloqueos, conflictos\n"
            # "⏰ Escaneo cada 10 minutos\n\n"
            # "_Los primeros resultados llegarán en segundos..._\n\n"
        )
        print("📨 Mensaje de inicio enviado al grupo")
        
        # Limpiar caché antiguo
        limpiar_cache_antiguo(horas=48)
        
        contador_ejecuciones = 0
        
        # Bucle infinito
        while True:
            try:
                inicio_ciclo = asyncio.get_event_loop().time()
                print(f"\n{'='*50}")
                print(f"🔄 CICLO #{contador_ejecuciones + 1}")
                
                # Buscar y enviar noticias
                noticias_enviadas = await enviar_noticias(client)
                
                tiempo_transcurrido = asyncio.get_event_loop().time() - inicio_ciclo
                
                if contador_ejecuciones == 0:
                    tiempo_espera = max(0, 15 * 60 - tiempo_transcurrido)
                    print(f"⏰ Primera ejecución. Esperando 15 minutos...")
                else:
                    tiempo_espera = max(0, 10 * 60 - tiempo_transcurrido)
                    print(f"⏰ Esperando 10 minutos...")
                
                contador_ejecuciones += 1
                await asyncio.sleep(tiempo_espera)
                
                if contador_ejecuciones % 12 == 0:
                    limpiar_cache_antiguo(horas=48)
                    
            except Exception as e:
                print(f"❌ Error en ciclo: {e}")
                await asyncio.sleep(30)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot detenido manualmente")
    except Exception as e:
        print(f"❌ Error fatal: {e}")