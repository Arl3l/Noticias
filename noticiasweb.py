# noticiasweb.py - Versión DEFINITIVA CORREGIDA
import asyncio
import aiohttp
import feedparser
import time
import re
import os
import json
from bs4 import BeautifulSoup
from telethon import TelegramClient
from typing import List, Tuple, Set, Dict
from asyncio import Semaphore
from urllib.parse import urljoin
import ssl
from flask import Flask
from threading import Thread


# Forzar SSL seguro
ssl._create_default_https_context = ssl._create_unverified_context

# ==================== CONFIGURACIÓN ====================
CHAT_ID = -1002629988101
ARCHIVO_ENVIADOS = 'enviados.json'
TIEMPO_CACHE_HORAS = 48

# Headers para evitar bloqueos
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
}

HEADERS_BOLIVISION = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://www.redbolivision.tv.bo/',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
}

SEMAFORO = Semaphore(5)

# ==================== PALABRAS CLAVE ====================
PALABRAS_CLAVE = [
    r"\bbloqueo\b", r"\bbloqueos\b", r"\bprotesta\b", r"\bprotestas\b",
    r"\bconflicto\b", r"\bconflictos\b", r"\bmovilizaci[oó]n\b", r"\bmovilizaciones\b",
    r"\bmarcha\b", r"\bmarchas\b", r"\bcacerolazo\b", r"\bcacerolazos\b",
    r"\bparo\b", r"\bparos\b", r"\bparo cívico\b",
    r"\bminero\b", r"\bmineros\b", r"\bevista\b",
    r"\bcampesino\b", r"\bcampesinos\b", r"\bfabril\b", r"\bfabriles\b",
    r"\btransportista\b", r"\btransportistas\b", r"\bchofer\b", r"\bchoferes\b",
    r"\bcomerciante\b", r"\bcomerciantes\b",
    r"\benfrentamiento\b", r"\benfrentamientos\b", r"\bgasificaci[oó]n\b",
    r"\bdetenido\b", r"\bdetenidos\b", r"\baprehendido\b", r"\baprehendidos\b",
    r"\bherido\b", r"\bheridos\b", r"\bm[uú]erto\b", r"\bm[uú]ertos\b",
    r"\bdesabastecimiento\b", r"\bescasez\b", r"\bdesalojo\b",
    r"\bcercada\b", r"\bcercadas\b", r"\bcerco\b", r"\bcercos\b",
    r"\bemergencia\b", r"\bemergencias\b",
    r"\bdin[aá]mita\b", r"\bpetardo\b", r"\bpetardos\b",
    r"\bgas lacrim[oó]geno\b", r"\bperdigón\b", r"\bbalin\b", r"\bbalines\b",
    r"\bpunto de bloqueo\b", r"\bcorte de ruta\b", r"\btranque\b",
    r"\btoma\b", r"\btomas\b",
    r"\bla paz\b", r"\bel alto\b", r"\bcochabamba\b", r"\bsanta cruz\b",
    r"\boruro\b", r"\bpotosí\b", r"\btarija\b", r"\bbeni\b", r"\bpando\b",
    r"\bamenazan\b", r"\bamenaza\b",
    r"\bestado de excepción\b",
    r"\bestado de sitio\b",
    r"\bcrisis política\b",
    r"\bcrisis social\b",
    r"\bmedida de presión\b",
    r"\bmedidas de presión\b",
    r"\bradicalización\b",
    r"\bvías de hecho\b",
    r"\bpolicía herido\b",
    r"\bagresión a periodista\b",
    r"\blibre tránsito\b",
    r"\bdesabastecimiento de alimentos\b",
    r"\bescasez de combustible\b",
    r"\bcerco a la paz\b",
    r"\bpausa humanitaria\b",
    r"\bcorredor humanitario\b",
    r"\bfranja de seguridad\b",
]

# ==================== PALABRAS EXCLUIDAS ====================
PALABRAS_EXCLUIDAS = [
    r"\b1xbet\b", r"\b22bet\b", r"\bpinnacle\b", r"\bduelbits\b", r"\bbetano\b",
    r"\bapuesta\b", r"\bapuestas\b", r"\bcasa de apuestas\b", r"\bcasino\b",
    r"\bfútbol\b", r"\bfutbol\b", r"\bdivisión profesional\b", r"\bcopa sudamericana\b",
    r"\bcopa libertadores\b", r"\bclasificatorias\b", r"\bmundial\b",
    r"\bfederación boliviana de fútbol\b", r"\bfbf\b", r"\bdroga\b", r"\bmascotas\b",
    r"\badopci[oó]n\b", r"\bmuseos\b", r"\bmuseo\b", r"\bc[aá]daver\b", r"\bchile\b",
    r"\bcarnaval\b", r"\bt[ií]tulo\b", r"\bcategor[ií]as\b", r"\bantidrogas\b",
    r"\bantidroga\b", r"\bemprendimiento\b", r"\bfolclore\b", r"\bcorso\b",
    r"\bucrania\b", r"\brusia\b", r"\binvasión rusa\b", r"\bputin\b", r"\bzelenski\b",
    r"\bguerra en ucrania\b", r"\bconflicto ucrania\b", r"\bkiev\b", r"\bmoscú\b",
    r"\bebola\b", r"\báfrica\b", r"\bvirus del ebola\b",
    r"\bodontología\b", r"\bdental\b", r"\bdientes\b", r"\bmuelas\b",
    r"\bdroma\b", r"\benfermedad de droma\b", r"\baccidente\b", r"\bhomicido\b",
    r"\bcorreos\b", r"\bcorreo\b",
    r"\bredes\b", r"\bbicicleta\b", r"\bimportadores\b", r"\bimportador\b",
    r"\beducaci[oó]n\b", r"\bemsa\b",
    r"\bparque\b", r"\bparques\b", r"\bagravadop\b", r"\btrump\b", r"\bparqueo\b",
    r"\bcristiano\b", r"\blewandowski\b", r"\bmané\b", r"\bsalah\b", r"\bibrahimovic\b",
    r"\bmundial de fútbol\b", r"\b champions \b", r"\b champions league\b",
    r"\bla liga\b", r"\bpremier league\b", r"\bserie a\b", r"\bkombat\b",
    r"\bvuelos\b", r"\bfans\b", r"\bfan\b", r"\bTaiw[aá]n\b",
    r"\bfuga\b", r"\bhombre\b", r"\bcolombiana\b", r"\bcolombia\b",
    r"\bhomicidio\b", r"\bpa[ií]ses\b", r"\bSan Jos[eé]\b", r"\bGran poder\b", r"\bjoven\b",r"\bfestividad\b",r"\bcaribe\b",
    r"\btablero\b",r"\bbrasil\b",r"\bconversatorio\b",r"\bperros\b",r"\boriente\b",r"\bBolívar\b"r"\bLibertadores\b",
    r"\bviolaci[oó]n\b",r"\blenocinio\b",r"\bjaguar\b",r"\bhomenaje\b",r"\b[iI]r[aá]n\b",r"\bPolet\b",
    r"\bmicrob[uú]s\b",r"\bBol[ií]var\b",r"\bdiscoteca\b",r"\btren\b",r"\bamazonas\b",r"\bamazon[ií]a\b",
    r"\boso\b",r"\bnarcotr[aá]fico\b",r"\bhallazgo\b",
]

PALABRAS_URGENTES = [
    r"\benfrentamiento\b", r"\benfrentamientos\b", r"\bviolent[oa]s\b",
    r"\bherido\b", r"\bheridos\b", r"\bm[uú]erto\b",
    r"\bdin[aá]mita\b", r"\bgasificaci[oó]n\b", r"\bdesabastecimiento\b",
    r"\baprehendido\b", r"\bdetenido\b", r"\bescasez\b",
    r"\bcercada\b", r"\bcerco\b", r"\bemergencia\b", r"\bfejuve\b",
    r"\bcorredor humanitario\b", r"\bmilitar[es]\b", r"\bmovilizaci[oó]n\b",r"\bcorredor humanitario\b"
]

# ==================== FUENTES RSS ====================
RSS_SOURCES = [
    # =====================================================
    # NUEVOS MEDIOS AGREGADOS (funcionando)
    # =====================================================
    "https://www.erbol.com.bo/rss",                    # ✅ Erbol - funciona
    "https://correodelsur.com/rss",                    # ✅ Correo del Sur
    "https://www.opinion.com.bo/rss",                  # ✅ Opinión
    "https://eju.tv/feed/",                            # ✅ Eju.tv
    "https://radiosangabriel.org.bo/feed/",            # ✅ Radio San Gabriel
    "https://www.noticiasfides.com/rss",               # ✅ Noticias Fides
    "https://www.oxigeno.bo/rss",                      # ✅ Oxígeno
    "https://radiofides.com/rss",                      # ✅ Radio Fides
    "https://www.atb.com.bo/categoria/sociedad/rss",   # ✅ ATB
    "https://urgente.bo/rss",                          # ✅ Urgente.bo
    "https://www.elpaisonline.com/rss",                # ✅ El País (Tarija)
    
    # =====================================================
    # MEDIOS CON URLS CORREGIDAS
    # =====================================================
    "https://www.reduno.com.bo/rss",                   # ⚠️ Red Uno - verificar
    "https://eldeber.com.bo/nacional/rss",             # ⚠️ El Deber
    "https://www.elalteno.com.bo/rss",                 # ⚠️ El Alteño
    "https://www.lostiempos.com/feed/",                # 🔧 CORREGIDO (era /rss, ahora /feed/)
    
    # =====================================================
    # ELIMINADOS (no funcionan)
    # =====================================================
    # "https://www.eldiario.net/portal/feed/",         # ❌ Error - lo manejamos por scraping
    # "https://www.bolivia.com/rss",                   # ❌ Error - lo manejamos por scraping
]

# ==================== SCRAPING SOURCES (CORREGIDO - SIN DUPLICADOS) ====================
SCRAPING_SOURCES = {
    # =====================================================
    # MEDIOS PRINCIPALES
    # =====================================================
    
    # Red Uno
    "https://www.reduno.com.bo/noticias/nacionales/": [
        ".titulo a", ".item-title a", "article h3 a", ".noticia-titulo a", "h2 a"
    ],
    
    # El Deber (scraping porque RSS falla)
    "https://eldeber.com.bo/nacional/": [
        ".card-news a", ".titulo-noticia a", "article h2 a", ".news-title a"
    ],
    
    # Bolivia.com (scraping porque RSS falla)
    "https://www.bolivia.com/noticias/": [
        "article h2 a", ".titulo a", ".news-title a", "h2 a"
    ],
    
    # El Diario (scraping porque RSS falla)
    "https://www.eldiario.net/portal/": [
        ".node-title a", "article h2 a", ".entry-title a", "h2 a", ".post-title a"
    ],
    
    # El Alteño
    "https://www.elalteno.com.bo/ciudad/": [
        ".field-content a", ".views-field-title a"
    ],
    
    # Los Tiempos
    "https://www.lostiempos.com/actualidad/": [
        ".field-content a", "article h2 a", ".node-title a"
    ],
    
    # Eju.tv
    "https://eju.tv/": [
        "article h2 a", ".entry-title a"
    ],
    
    # La Patria
    "https://lapatria.bo/": [
        "article h2 a", ".entry-title a"
    ],
    
    # Radio San Gabriel
    "https://radiosangabriel.org.bo/": [
        "article h2 a", ".entry-title a"
    ],
    
    # Opinión
    "https://www.opinion.com.bo/": [
        "article h2 a", ".card-title a"
    ],
    
    # Radio Fides
    "https://radiofides.com/": [
        ".entry-title a", "h2 a", ".post-title a", "article h2 a"
    ],
    
    # Correo del Sur
    "https://correodelsur.com/": [
        ".node-title a", "article h2 a", "h2 a"
    ],
    
    # =====================================================
    # NUEVOS MEDIOS AGREGADOS
    # =====================================================
    
    # Unitel
    "https://www.unitel.bo/nacional/": [
        "article h2 a", ".entry-title a", ".title a", "h2 a"
    ],
    
    # RTP Bolivia
    "https://rtpbolivia.com/": [
        "article h2 a", ".entry-title a", ".post-title a", "h2 a"
    ],
    
    # El Sol (Oruro)
    "https://www.elsol.com.bo/": [
        "article h2 a", ".post-title a", ".entry-title a", "h2 a"
    ],
    
    # La Razón (si llega a funcionar)
    "https://www.la-razon.com/nacional/": [
        "article h2 a", ".entry-title a", "h2 a"
    ],
    
    # ATB (scraping)
    "https://www.atb.com.bo/categoria/sociedad/": [
        "div.card-content a", "article h3 a", ".news-title a", "h2 a"
    ],
    
    # Página Siete (si responde)
    "https://paginasiete.bo/nacional/": [
        "article h2 a", ".post-title a", ".entry-title a"
    ],
    
    # =====================================================
    # FUENTES GUBERNAMENTALES
    # =====================================================
    
    # ABC
    "https://www.abc.gob.bo/": [
        ".noticia-titulo a", "article h2 a", "h2 a"
    ],
    
    # Ministerio de Salud
    "https://www.minsalud.gob.bo/": [
        ".noticia-titulo a", "article h2 a", "h2 a"
    ],
    
    # Defensoría
    "https://www.defensoria.gob.bo/": [
        ".noticia-titulo a", "article h2 a", "h2 a"
    ],
    
    # Bolivia TV
    "https://www.boliviatv.bo/": [
        ".entry-title a", ".noticia-titulo a", "article h2 a", "h2 a"
    ],
    # =====================================================
    # NUEVAS FUENTES AGREGADAS (27 de mayo 2026)
    # =====================================================

    # El Mundo (Cochabamba)
    "https://elmundo.com.bo/category/nacional/": [
        "article h2 a", ".entry-title a", ".post-title a", 
        "h2 a", ".node-title a", ".title a"
    ],

    # ABI - Agencia Boliviana de Información (Política)
    "https://abi.bo/category/noticas/politica/": [
        "article h2 a", ".entry-title a", ".post-title a", 
        "h2 a", ".node-title a", ".noticia-titulo a"
    ],

    # ABI - Agencia Boliviana de Información (Sociedad)
    "https://abi.bo/category/noticas/sociedad/": [
        "article h2 a", ".entry-title a", ".post-title a", 
        "h2 a", ".node-title a", ".noticia-titulo a"
    ],

    # CNN en Español (Bolivia) - puede tener bloqueo
    "https://cnnespanol.cnn.com/latinoamerica/bolivia": [
        "article h2 a", ".entry-title a", ".post-title a", 
        "h2 a", ".node-title a", ".card__title a"
    ],
}

# ==================== CACHÉ ====================
enlaces_cache: Dict[str, float] = {}

def cargar_enlaces_enviados():
    global enlaces_cache
    if os.path.exists(ARCHIVO_ENVIADOS):
        try:
            with open(ARCHIVO_ENVIADOS, 'r', encoding='utf-8') as f:
                enlaces_cache = json.load(f)
            print(f"📂 [Caché] {len(enlaces_cache)} enlaces cargados")
        except:
            enlaces_cache = {}
    else:
        print("📂 [Caché] Archivo nuevo")
        enlaces_cache = {}

def guardar_enlaces_enviados():
    try:
        with open(ARCHIVO_ENVIADOS, 'w', encoding='utf-8') as f:
            json.dump(enlaces_cache, f, ensure_ascii=False, indent=2)
        print(f"💾 [Caché] {len(enlaces_cache)} enlaces guardados")
    except Exception as e:
        print(f"❌ Error guardando: {e}")

def limpiar_cache_antiguo(horas: int = 48):
    global enlaces_cache
    ahora = time.time()
    limite = ahora - (horas * 3600)
    antiguos = [e for e, ts in enlaces_cache.items() if ts < limite]
    for e in antiguos:
        del enlaces_cache[e]
    if antiguos:
        print(f"🧹 [Caché] Limpiados {len(antiguos)} enlaces")
        guardar_enlaces_enviados()

def es_enlace_nuevo_o_fresco(enlace: str) -> bool:
    if enlace not in enlaces_cache:
        return True
    edad = time.time() - enlaces_cache[enlace]
    return edad > (TIEMPO_CACHE_HORAS * 3600)

def marcar_enlace_como_enviado(enlace: str):
    enlaces_cache[enlace] = time.time()

def calcular_prioridad(titulo: str, resumen: str) -> str:
    texto = (titulo + " " + resumen).lower()
    urgencias = sum(1 for p in PALABRAS_URGENTES if re.search(p, texto))
    if urgencias >= 2:
        return "🚨🔥 **¡URGENTE!** 🔥🚨\n"
    elif urgencias == 1:
        return "⚠️ **IMPORTANTE** ⚠️\n"
    return "📰 "

def es_noticia_relevante(titulo: str, resumen: str, enlace: str) -> bool:
    if not titulo:
        return False
    
    texto = (titulo + " " + (resumen or "")).lower()
    
    for excluido in PALABRAS_EXCLUIDAS:
        if re.search(excluido, texto):
            print(f"🚫 [Filtro] EXCLUIDA: {titulo[:60]}...")
            return False
    
    for patron in PALABRAS_CLAVE:
        if re.search(patron, texto):
            print(f"🔍 [Filtro] ✅ RELEVANTE: {titulo[:80]}...")
            return True
    
    return False

# ==================== OBTENCIÓN DE NOTICIAS ====================
async def procesar_rss(session: aiohttp.ClientSession, url: str) -> List[Tuple[str, str, str]]:
    noticias = []
    try:
        async with session.get(url, timeout=15, headers=HEADERS) as resp:
            if resp.status != 200:
                return []
            content = await resp.text()
            feed = feedparser.parse(content)
            for entry in feed.entries[:20]:
                titulo = entry.get('title', '')
                resumen = entry.get('summary', '') or entry.get('description', '')
                enlace = entry.get('link', '')
                if enlace and es_enlace_nuevo_o_fresco(enlace):
                    if es_noticia_relevante(titulo, resumen, enlace):
                        noticias.append((titulo, resumen, enlace))
                        marcar_enlace_como_enviado(enlace)
    except Exception as e:
        print(f"❌ RSS {url}: {e}")
    return noticias

async def obtener_noticias_rss() -> List[Tuple[str, str, str]]:
    print(f"\n📡 [RSS] Escaneando {len(RSS_SOURCES)} fuentes...")
    async with aiohttp.ClientSession() as session:
        tareas = [procesar_rss(session, url) for url in RSS_SOURCES]
        resultados = await asyncio.gather(*tareas, return_exceptions=True)
        todas = []
        for r in resultados:
            if isinstance(r, list):
                todas.extend(r)
        print(f"📡 [RSS] Encontradas {len(todas)} noticias relevantes")
        return todas

async def obtener_detalle_noticia(session: aiohttp.ClientSession, url: str) -> Tuple[str, str]:
    try:
        async with session.get(url, timeout=10, headers=HEADERS) as resp:
            if resp.status != 200:
                return "", ""
            html = await resp.text()
            soup = BeautifulSoup(html, 'html.parser')
            titulo = soup.title.string.strip() if soup.title else ""
            meta = soup.find("meta", {"name": "description"})
            resumen = meta.get("content", "") if meta else ""
            if not resumen:
                for selector in ['article p', '.entry-content p', '.post-content p', '.contenido p', 'p']:
                    parrafos = soup.select(selector)
                    for p in parrafos[:3]:
                        texto = p.text.strip()
                        if len(texto) > 50:
                            resumen = texto[:300]
                            break
                    if resumen:
                        break
            return titulo, resumen
    except Exception:
        return "", ""

async def procesar_url_scraping(session: aiohttp.ClientSession, url: str, selectores: List[str]) -> Set[str]:
    enlaces = set()
    try:
        headers = HEADERS_BOLIVISION if "redbolivision" in url else HEADERS
        async with session.get(url, timeout=20, headers=headers) as resp:
            if resp.status != 200:
                return enlaces
            html = await resp.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            for selector in selectores:
                try:
                    tags = soup.select(selector)
                    if tags:
                        for tag in tags:
                            href = tag.get("href")
                            if href:
                                if not href.startswith("http"):
                                    href = urljoin(url, href)
                                if not any(skip in href.lower() for skip in ['facebook', 'twitter', 'instagram', 'youtube']):
                                    enlaces.add(href)
                        break
                except:
                    continue
    except Exception as e:
        print(f"❌ Scraping {url}: {e}")
    return enlaces

async def obtener_noticias_scraping() -> List[Tuple[str, str, str]]:
    print(f"\n🔍 [Scraping] Escaneando sitios...")
    
    async with aiohttp.ClientSession() as session:
        todos_enlaces = set()
        for url, selectores in SCRAPING_SOURCES.items():
            enlaces = await procesar_url_scraping(session, url, selectores)
            if enlaces:
                print(f"   📌 {url.split('/')[2]}: {len(enlaces)} enlaces")
                todos_enlaces.update(enlaces)
        
        print(f"\n🔍 [Scraping] Total enlaces únicos: {len(todos_enlaces)}")
        enlaces_nuevos = [e for e in todos_enlaces if es_enlace_nuevo_o_fresco(e)]
        print(f"🔍 [Scraping] Enlaces nuevos: {len(enlaces_nuevos)}")
        
        if not enlaces_nuevos:
            return []
        
        noticias = []
        for url in enlaces_nuevos[:50]:
            titulo, resumen = await obtener_detalle_noticia(session, url)
            if titulo and es_noticia_relevante(titulo, resumen, url):
                noticias.append((titulo, resumen, url))
                marcar_enlace_como_enviado(url)
            await asyncio.sleep(0.3)
        
        print(f"🔍 [Scraping] Relevantes: {len(noticias)}")
        return noticias

# ==================== ENVÍO A TELEGRAM ====================
async def enviar_noticias(client: TelegramClient) -> int:
    print("\n" + "="*60)
    print("📰 BUSCANDO NOTICIAS DE BOLIVIA")
    print("🚫 Excluyendo: Fútbol, apuestas, Ucrania, temas internacionales")
    print("="*60)
    
    tareas = [obtener_noticias_rss(), obtener_noticias_scraping()]
    resultados = await asyncio.gather(*tareas)
    noticias_rss = resultados[0]
    noticias_scraping = resultados[1]
    
    todas = {}
    for titulo, resumen, enlace in noticias_rss + noticias_scraping:
        if enlace not in todas:
            todas[enlace] = (titulo, resumen, enlace)
    
    unicas = list(todas.values())
    
    print(f"\n📊 RSS: {len(noticias_rss)} | Scraping: {len(noticias_scraping)} | Total: {len(unicas)}")
    
    if not unicas:
        print("📭 No hay noticias nuevas")
        guardar_enlaces_enviados()
        return 0
    
    con_prioridad = []
    for titulo, resumen, enlace in unicas:
        prioridad = calcular_prioridad(titulo, resumen)
        con_prioridad.append((prioridad, titulo, resumen, enlace))
    con_prioridad.sort(key=lambda x: 0 if "URGENTE" in x[0] else (1 if "IMPORTANTE" in x[0] else 2))
    
    enviadas = 0
    for prioridad, titulo, resumen, enlace in con_prioridad:
        titulo_limpio = BeautifulSoup(titulo, 'html.parser').get_text()
        mensaje = f"{prioridad}**{titulo_limpio}**\n\n🔗 {enlace}"
        if resumen and len(resumen) < 300 and len(resumen) > 30:
            resumen_limpio = BeautifulSoup(resumen, 'html.parser').get_text()
            mensaje = f"{prioridad}**{titulo_limpio}**\n\n📝 {resumen_limpio[:200]}...\n\n🔗 {enlace}"
        try:
            await client.send_message(CHAT_ID, mensaje)
            print(f"✅ Enviada: {titulo_limpio[:60]}...")
            enviadas += 1
            await asyncio.sleep(1)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n📨 ENVIADAS: {enviadas}")
    guardar_enlaces_enviados()
    return enviadas

app = Flask('')
@app.route('/')
def home():
    return "Bot de Noticias Bolivia está activo!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Llama a keep_alive() al iniciar
keep_alive()