import base64
import json
import random
import threading
import tkinter as tk
import unicodedata
from pathlib import Path
from tkinter import ttk

import requests


class PokemonNoEncontrado(Exception):
    pass


class TipoNoEncontrado(Exception):
    pass


class RecursoNoEncontrado(Exception):
    pass


class ErrorConsultaPokemon(Exception):
    pass


NOMBRES_ESTADISTICAS = {
    "hp": "PS",
    "attack": "Ataque",
    "defense": "Defensa",
    "special-attack": "Ataque especial",
    "special-defense": "Defensa especial",
    "speed": "Velocidad",
}

SPRITES_POKEMON = {
    "Frontal normal": "front_default",
    "Dorsal normal": "back_default",
    "Frontal shiny": "front_shiny",
    "Dorsal shiny": "back_shiny",
    "Frontal femenino": "front_female",
    "Dorsal femenino": "back_female",
    "Frontal shiny femenino": "front_shiny_female",
    "Dorsal shiny femenino": "back_shiny_female",
}

TIPOS_POKEMON = [
    "normal",
    "fire",
    "water",
    "electric",
    "grass",
    "ice",
    "fighting",
    "poison",
    "ground",
    "flying",
    "psychic",
    "bug",
    "rock",
    "ghost",
    "dragon",
    "dark",
    "steel",
    "fairy",
]

TIPOS_EN_ESPANOL = {
    "normal": "normal",
    "fuego": "fire",
    "agua": "water",
    "electrico": "electric",
    "planta": "grass",
    "hierba": "grass",
    "hielo": "ice",
    "lucha": "fighting",
    "veneno": "poison",
    "tierra": "ground",
    "volador": "flying",
    "psiquico": "psychic",
    "bicho": "bug",
    "roca": "rock",
    "fantasma": "ghost",
    "dragon": "dragon",
    "siniestro": "dark",
    "acero": "steel",
    "hada": "fairy",
}

FAVORITOS_PATH = Path(__file__).with_name("pokemon_favoritos.json")
JUEGO_MAX_POKEMON_ID = 151
JUEGO_INTENTOS_MAX = 3

TRIGGERS_EVOLUCION = {
    "level-up": "subir de nivel",
    "trade": "intercambio",
    "use-item": "usar objeto",
    "shed": "shed",
    "spin": "girar",
    "tower-of-darkness": "torre de la oscuridad",
    "tower-of-waters": "torre de las aguas",
    "three-critical-hits": "tres golpes criticos",
    "take-damage": "recibir dano",
    "other": "otro metodo",
}


def consultar_api(url, excepcion_no_encontrado):
    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            raise excepcion_no_encontrado

        response.raise_for_status()
        return response.json()

    except (PokemonNoEncontrado, TipoNoEncontrado, RecursoNoEncontrado):
        raise
    except requests.exceptions.Timeout as e:
        raise ErrorConsultaPokemon("La API tardo demasiado en responder.") from e
    except requests.exceptions.ConnectionError as e:
        raise ErrorConsultaPokemon("No se pudo conectar con la API. Revisa tu conexion a internet.") from e
    except requests.exceptions.HTTPError as e:
        raise ErrorConsultaPokemon(f"La API respondio con un error HTTP: {e}") from e
    except requests.exceptions.RequestException as e:
        raise ErrorConsultaPokemon(f"Ocurrio un error al consultar la API: {e}") from e


def normalizar_tipo(tipo_pokemon):
    tipo = unicodedata.normalize("NFKD", tipo_pokemon.strip().lower())
    tipo = "".join(caracter for caracter in tipo if not unicodedata.combining(caracter))
    tipo = tipo.replace(" ", "-")
    return TIPOS_EN_ESPANOL.get(tipo, tipo)


def normalizar_texto(texto):
    texto_normalizado = unicodedata.normalize("NFKD", texto.strip().lower())
    texto_normalizado = "".join(
        caracter for caracter in texto_normalizado if not unicodedata.combining(caracter)
    )
    return texto_normalizado.replace(" ", "-")


def obtener_pokemon_por_nombre(nombre_pokemon):
    """
    Obtiene informacion de un Pokemon por su nombre usando la PokeAPI.
    """
    nombre = nombre_pokemon.strip().lower()
    url = f"https://pokeapi.co/api/v2/pokemon/{nombre}"
    return consultar_api(url, PokemonNoEncontrado)


def obtener_pokemon_por_tipo(tipo_pokemon):
    """
    Obtiene una lista de nombres de Pokemon asociados a un tipo.
    """
    tipo = normalizar_tipo(tipo_pokemon)
    url = f"https://pokeapi.co/api/v2/type/{tipo}"
    data = consultar_api(url, TipoNoEncontrado)
    nombres = [item["pokemon"]["name"] for item in data["pokemon"]]
    return sorted(nombres)


def obtener_pokemon_aleatorio_juego():
    pokemon_id = random.randint(1, JUEGO_MAX_POKEMON_ID)
    return obtener_pokemon_por_nombre(str(pokemon_id))


def cargar_favoritos():
    try:
        data = json.loads(FAVORITOS_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(data, list):
        return []

    favoritos = {str(nombre).strip().lower() for nombre in data if str(nombre).strip()}
    return sorted(favoritos)


def guardar_favoritos(favoritos):
    favoritos_ordenados = sorted({nombre.strip().lower() for nombre in favoritos if nombre.strip()})
    FAVORITOS_PATH.write_text(json.dumps(favoritos_ordenados, indent=2), encoding="utf-8")


def formatear_nombre_api(nombre):
    return nombre.replace("-", " ")


def obtener_nombre_api(valor):
    if isinstance(valor, dict):
        return valor.get("name", "")
    return ""


def describir_detalles_evolucion(detalles):
    if not detalles:
        return "Metodo no especificado"

    descripciones = []

    for detalle in detalles:
        partes = []
        trigger = obtener_nombre_api(detalle.get("trigger"))

        item = obtener_nombre_api(detalle.get("item"))
        if item:
            partes.append(f"usar {formatear_nombre_api(item)}")
        elif trigger:
            partes.append(TRIGGERS_EVOLUCION.get(trigger, formatear_nombre_api(trigger)))

        held_item = obtener_nombre_api(detalle.get("held_item"))
        if held_item:
            partes.append(f"llevar {formatear_nombre_api(held_item)}")

        known_move = obtener_nombre_api(detalle.get("known_move"))
        if known_move:
            partes.append(f"con movimiento {formatear_nombre_api(known_move)}")

        known_move_type = obtener_nombre_api(detalle.get("known_move_type"))
        if known_move_type:
            partes.append(f"movimiento tipo {formatear_nombre_api(known_move_type)}")

        location = obtener_nombre_api(detalle.get("location"))
        if location:
            partes.append(f"en {formatear_nombre_api(location)}")

        min_level = detalle.get("min_level")
        if min_level is not None:
            partes.append(f"nivel {min_level}")

        min_happiness = detalle.get("min_happiness")
        if min_happiness is not None:
            partes.append(f"felicidad {min_happiness}")

        min_beauty = detalle.get("min_beauty")
        if min_beauty is not None:
            partes.append(f"belleza {min_beauty}")

        min_affection = detalle.get("min_affection")
        if min_affection is not None:
            partes.append(f"afecto {min_affection}")

        time_of_day = detalle.get("time_of_day")
        if time_of_day:
            partes.append(f"durante {time_of_day}")

        if detalle.get("needs_overworld_rain"):
            partes.append("con lluvia")

        if detalle.get("turn_upside_down"):
            partes.append("con la consola boca abajo")

        if not partes:
            partes.append("Metodo no especificado")

        descripciones.append(", ".join(partes))

    return " / ".join(descripciones)


def recopilar_cadena_evolucion(nodo, etapa=1, condicion="Pokemon base", resultado=None):
    if resultado is None:
        resultado = []

    especie = nodo["species"]["name"]
    resultado.append((etapa, especie, condicion))

    for evolucion in nodo.get("evolves_to", []):
        condicion_evolucion = describir_detalles_evolucion(evolucion.get("evolution_details", []))
        recopilar_cadena_evolucion(evolucion, etapa + 1, condicion_evolucion, resultado)

    return resultado


def obtener_evolucion_pokemon(pokemon_data):
    especie_url = pokemon_data.get("species", {}).get("url")

    if not especie_url:
        return []

    especie_data = consultar_api(especie_url, RecursoNoEncontrado)
    cadena_url = especie_data.get("evolution_chain", {}).get("url")

    if not cadena_url:
        return []

    cadena_data = consultar_api(cadena_url, RecursoNoEncontrado)
    return recopilar_cadena_evolucion(cadena_data["chain"])


def recopilar_estadisticas(pokemon_data):
    estadisticas = []

    for stat in pokemon_data["stats"]:
        nombre_api = stat["stat"]["name"]
        nombre = NOMBRES_ESTADISTICAS.get(nombre_api, nombre_api)
        estadisticas.append((nombre, stat["base_stat"], stat["effort"]))

    return estadisticas


def recopilar_habilidades(pokemon_data):
    habilidades = []

    for ability_data in pokemon_data["abilities"]:
        habilidad = ability_data["ability"]["name"]
        tipo = "oculta" if ability_data["is_hidden"] else "normal"
        habilidades.append((habilidad, tipo))

    return habilidades


def crear_pistas_juego(pokemon_data):
    tipos = ", ".join(tipo["type"]["name"] for tipo in pokemon_data["types"])
    habilidades = ", ".join(habilidad for habilidad, _ in recopilar_habilidades(pokemon_data))
    estadisticas = recopilar_estadisticas(pokemon_data)
    mejor_stat = max(estadisticas, key=lambda stat: stat[1])

    return [
        f"Tipo(s): {tipos}",
        f"Altura: {pokemon_data['height'] * 10} cm",
        f"Peso: {pokemon_data['weight'] / 10} kg",
        f"Habilidad(es): {habilidades}",
        f"Su estadistica mas alta es {mejor_stat[0]} ({mejor_stat[1]}).",
    ]


def recopilar_sprites(pokemon_data):
    sprites = pokemon_data["sprites"]
    resultado = []

    for descripcion, clave in SPRITES_POKEMON.items():
        url_sprite = sprites.get(clave)

        if url_sprite:
            resultado.append((descripcion, url_sprite))

    artwork_oficial = sprites.get("other", {}).get("official-artwork", {})

    if artwork_oficial.get("front_default"):
        resultado.append(("Artwork oficial", artwork_oficial["front_default"]))

    if artwork_oficial.get("front_shiny"):
        resultado.append(("Artwork oficial shiny", artwork_oficial["front_shiny"]))

    return resultado


def obtener_url_sprite_principal(pokemon_data):
    sprites = pokemon_data["sprites"]
    artwork_oficial = sprites.get("other", {}).get("official-artwork", {})
    return artwork_oficial.get("front_default") or sprites.get("front_default")


def descargar_imagen_base64(url):
    if not url:
        return None

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return None

    return base64.b64encode(response.content).decode("ascii")


def mostrar_info_pokemon(pokemon_data):
    """
    Muestra la informacion del Pokemon en la consola.
    """
    print(f"Nombre: {pokemon_data['name']}")
    print(f"Tipos: {', '.join(tipo['type']['name'] for tipo in pokemon_data['types'])}")
    print(f"Altura: {pokemon_data['height'] * 10} cm")
    print(f"Peso: {pokemon_data['weight'] / 10} kg")
    print("Estadisticas detalladas:")

    for nombre, valor_base, esfuerzo in recopilar_estadisticas(pokemon_data):
        print(f"  - {nombre}: {valor_base} (EV: {esfuerzo})")

    print("Habilidades:")
    for habilidad, tipo in recopilar_habilidades(pokemon_data):
        print(f"  - {habilidad} ({tipo})")

    print("Sprites:")
    for descripcion, url_sprite in recopilar_sprites(pokemon_data):
        print(f"  - {descripcion}: {url_sprite}")

    print("Movimientos:")
    for move in pokemon_data["moves"]:
        print(f"  - {move['move']['name']}")


class PokemonApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pokedex")
        self.geometry("1080x720")
        self.minsize(900, 620)

        self.nombre_var = tk.StringVar()
        self.tipo_var = tk.StringVar(value="fire")
        self.estado_var = tk.StringVar(value="Listo")
        self.sprite_image = None
        self.current_pokemon_name = None
        self.favoritos = cargar_favoritos()
        self.juego_respuesta_var = tk.StringVar()
        self.juego_pokemon = None
        self.juego_imagen_base64 = None
        self.juego_image = None
        self.juego_intentos = 0
        self.juego_resuelto = False

        self.configurar_estilos()
        self.crear_interfaz()

    def configurar_estilos(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f5f7fb")
        style.configure("Panel.TFrame", background="#ffffff", relief="flat")
        style.configure("TLabel", background="#f5f7fb", foreground="#1f2937", font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background="#ffffff", foreground="#1f2937", font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#f5f7fb", foreground="#111827", font=("Segoe UI", 22, "bold"))
        style.configure("Name.TLabel", background="#ffffff", foreground="#111827", font=("Segoe UI", 20, "bold"))
        style.configure("Status.TLabel", background="#f5f7fb", foreground="#475569", font=("Segoe UI", 9))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=25)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def crear_interfaz(self):
        contenedor = ttk.Frame(self, padding=16)
        contenedor.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        contenedor.columnconfigure(0, weight=1, minsize=320)
        contenedor.columnconfigure(1, weight=2)
        contenedor.rowconfigure(1, weight=1)

        ttk.Label(contenedor, text="Pokedex", style="Title.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")

        panel_busqueda = ttk.Frame(contenedor, style="Panel.TFrame", padding=14)
        panel_busqueda.grid(row=1, column=0, sticky="nsew", pady=(16, 0), padx=(0, 16))
        panel_busqueda.columnconfigure(0, weight=1)
        panel_busqueda.rowconfigure(0, weight=1)

        self.crear_panel_busqueda(panel_busqueda)

        panel_detalle = ttk.Frame(contenedor, style="Panel.TFrame", padding=14)
        panel_detalle.grid(row=1, column=1, sticky="nsew", pady=(16, 0))
        panel_detalle.columnconfigure(0, weight=1)
        panel_detalle.rowconfigure(1, weight=1)

        self.crear_panel_detalle(panel_detalle)

        ttk.Label(contenedor, textvariable=self.estado_var, style="Status.TLabel").grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0)
        )

    def crear_panel_busqueda(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.grid(row=0, column=0, sticky="nsew")

        tab_nombre = ttk.Frame(notebook, padding=12)
        tab_tipo = ttk.Frame(notebook, padding=12)
        tab_favoritos = ttk.Frame(notebook, padding=12)
        tab_juego = ttk.Frame(notebook, padding=12)
        notebook.add(tab_nombre, text="Por nombre")
        notebook.add(tab_tipo, text="Por tipo")
        notebook.add(tab_favoritos, text="Favoritos")
        notebook.add(tab_juego, text="Juego")

        tab_nombre.columnconfigure(0, weight=1)
        ttk.Label(tab_nombre, text="Nombre del Pokemon").grid(row=0, column=0, sticky="w")
        entry_nombre = ttk.Entry(tab_nombre, textvariable=self.nombre_var)
        entry_nombre.grid(row=1, column=0, sticky="ew", pady=(6, 10))
        entry_nombre.bind("<Return>", self.buscar_por_nombre)

        self.boton_nombre = ttk.Button(
            tab_nombre,
            text="Buscar",
            style="Accent.TButton",
            command=self.buscar_por_nombre,
        )
        self.boton_nombre.grid(row=2, column=0, sticky="ew")

        tab_tipo.columnconfigure(0, weight=1)
        tab_tipo.rowconfigure(4, weight=1)
        ttk.Label(tab_tipo, text="Tipo").grid(row=0, column=0, sticky="w")

        self.combo_tipo = ttk.Combobox(tab_tipo, textvariable=self.tipo_var, values=TIPOS_POKEMON)
        self.combo_tipo.grid(row=1, column=0, sticky="ew", pady=(6, 10))
        self.combo_tipo.bind("<Return>", self.buscar_por_tipo)

        self.boton_tipo = ttk.Button(
            tab_tipo,
            text="Buscar tipo",
            style="Accent.TButton",
            command=self.buscar_por_tipo,
        )
        self.boton_tipo.grid(row=2, column=0, sticky="ew")

        ttk.Label(tab_tipo, text="Resultados").grid(row=3, column=0, sticky="w", pady=(16, 6))

        resultados_frame = ttk.Frame(tab_tipo)
        resultados_frame.grid(row=4, column=0, sticky="nsew")
        resultados_frame.columnconfigure(0, weight=1)
        resultados_frame.rowconfigure(0, weight=1)

        self.lista_tipo = tk.Listbox(
            resultados_frame,
            borderwidth=0,
            activestyle="none",
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground="#d8dee9",
            selectbackground="#2563eb",
        )
        self.lista_tipo.grid(row=0, column=0, sticky="nsew")
        self.lista_tipo.bind("<Double-Button-1>", self.buscar_desde_lista_tipo)
        self.lista_tipo.bind("<Return>", self.buscar_desde_lista_tipo)

        scroll_resultados = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.lista_tipo.yview)
        scroll_resultados.grid(row=0, column=1, sticky="ns")
        self.lista_tipo.configure(yscrollcommand=scroll_resultados.set)

        self.crear_tab_favoritos(tab_favoritos)
        self.crear_tab_juego(tab_juego)

    def crear_tab_favoritos(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        ttk.Label(parent, text="Pokemon favoritos").grid(row=0, column=0, sticky="w", pady=(0, 6))

        favoritos_frame = ttk.Frame(parent)
        favoritos_frame.grid(row=1, column=0, sticky="nsew")
        favoritos_frame.columnconfigure(0, weight=1)
        favoritos_frame.rowconfigure(0, weight=1)

        self.lista_favoritos = tk.Listbox(
            favoritos_frame,
            borderwidth=0,
            activestyle="none",
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground="#d8dee9",
            selectbackground="#2563eb",
        )
        self.lista_favoritos.grid(row=0, column=0, sticky="nsew")
        self.lista_favoritos.bind("<Double-Button-1>", self.buscar_desde_lista_favoritos)
        self.lista_favoritos.bind("<Return>", self.buscar_desde_lista_favoritos)

        scroll_favoritos = ttk.Scrollbar(favoritos_frame, orient="vertical", command=self.lista_favoritos.yview)
        scroll_favoritos.grid(row=0, column=1, sticky="ns")
        self.lista_favoritos.configure(yscrollcommand=scroll_favoritos.set)

        botones = ttk.Frame(parent)
        botones.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        botones.columnconfigure(0, weight=1)
        botones.columnconfigure(1, weight=1)

        ttk.Button(botones, text="Abrir", command=self.buscar_desde_lista_favoritos).grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )
        ttk.Button(botones, text="Quitar", command=self.quitar_favorito_seleccionado).grid(
            row=0, column=1, sticky="ew", padx=(6, 0)
        )

        self.actualizar_lista_favoritos()

    def crear_tab_juego(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(3, weight=1)

        self.juego_titulo_label = ttk.Label(
            parent,
            text="Adivina el Pokemon",
            font=("Segoe UI", 14, "bold"),
        )
        self.juego_titulo_label.grid(row=0, column=0, sticky="w")

        self.juego_intentos_label = ttk.Label(parent, text=f"Intentos: 0/{JUEGO_INTENTOS_MAX}")
        self.juego_intentos_label.grid(row=1, column=0, sticky="w", pady=(6, 12))

        self.juego_imagen_label = ttk.Label(parent, text="?", anchor="center", font=("Segoe UI", 32, "bold"))
        self.juego_imagen_label.grid(row=2, column=0, sticky="ew", pady=(0, 12))

        pistas_frame = ttk.Frame(parent)
        pistas_frame.grid(row=3, column=0, sticky="nsew")
        pistas_frame.columnconfigure(0, weight=1)
        pistas_frame.rowconfigure(0, weight=1)

        self.lista_pistas_juego = tk.Listbox(
            pistas_frame,
            borderwidth=0,
            activestyle="none",
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground="#d8dee9",
            selectbackground="#2563eb",
        )
        self.lista_pistas_juego.grid(row=0, column=0, sticky="nsew")

        scroll_pistas = ttk.Scrollbar(pistas_frame, orient="vertical", command=self.lista_pistas_juego.yview)
        scroll_pistas.grid(row=0, column=1, sticky="ns")
        self.lista_pistas_juego.configure(yscrollcommand=scroll_pistas.set)

        self.juego_respuesta_entry = ttk.Entry(parent, textvariable=self.juego_respuesta_var, state="disabled")
        self.juego_respuesta_entry.grid(row=4, column=0, sticky="ew", pady=(12, 8))
        self.juego_respuesta_entry.bind("<Return>", self.comprobar_respuesta_juego)

        botones = ttk.Frame(parent)
        botones.grid(row=5, column=0, sticky="ew")
        botones.columnconfigure(0, weight=1)
        botones.columnconfigure(1, weight=1)

        self.boton_comprobar_juego = ttk.Button(
            botones,
            text="Comprobar",
            command=self.comprobar_respuesta_juego,
            state="disabled",
        )
        self.boton_comprobar_juego.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.boton_rendirse_juego = ttk.Button(
            botones,
            text="Rendirse",
            command=self.rendirse_juego,
            state="disabled",
        )
        self.boton_rendirse_juego.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.boton_nueva_ronda = ttk.Button(
            parent,
            text="Nueva ronda",
            style="Accent.TButton",
            command=self.iniciar_juego,
        )
        self.boton_nueva_ronda.grid(row=6, column=0, sticky="ew", pady=(10, 0))

    def crear_panel_detalle(self, parent):
        resumen = ttk.Frame(parent, style="Panel.TFrame")
        resumen.grid(row=0, column=0, sticky="ew")
        resumen.columnconfigure(1, weight=1)

        self.sprite_label = ttk.Label(resumen, text="Sin imagen", style="Panel.TLabel", anchor="center")
        self.sprite_label.grid(row=0, column=0, rowspan=5, sticky="n", padx=(0, 18))

        self.nombre_label = ttk.Label(resumen, text="Busca un Pokemon", style="Name.TLabel")
        self.nombre_label.grid(row=0, column=1, sticky="w")

        self.tipos_label = ttk.Label(resumen, text="Tipos: -", style="Panel.TLabel")
        self.tipos_label.grid(row=1, column=1, sticky="w", pady=(8, 0))

        self.altura_label = ttk.Label(resumen, text="Altura: -", style="Panel.TLabel")
        self.altura_label.grid(row=2, column=1, sticky="w", pady=(4, 0))

        self.peso_label = ttk.Label(resumen, text="Peso: -", style="Panel.TLabel")
        self.peso_label.grid(row=3, column=1, sticky="w", pady=(4, 0))

        self.boton_favorito = ttk.Button(
            resumen,
            text="Agregar favorito",
            command=self.alternar_favorito_actual,
            state="disabled",
        )
        self.boton_favorito.grid(row=4, column=1, sticky="w", pady=(10, 0))

        detalle_notebook = ttk.Notebook(parent)
        detalle_notebook.grid(row=1, column=0, sticky="nsew", pady=(18, 0))

        tab_estadisticas = ttk.Frame(detalle_notebook, padding=10)
        tab_habilidades = ttk.Frame(detalle_notebook, padding=10)
        tab_sprites = ttk.Frame(detalle_notebook, padding=10)
        tab_evolucion = ttk.Frame(detalle_notebook, padding=10)
        tab_movimientos = ttk.Frame(detalle_notebook, padding=10)

        detalle_notebook.add(tab_estadisticas, text="Estadisticas")
        detalle_notebook.add(tab_habilidades, text="Habilidades")
        detalle_notebook.add(tab_sprites, text="Sprites")
        detalle_notebook.add(tab_evolucion, text="Evolucion")
        detalle_notebook.add(tab_movimientos, text="Movimientos")

        self.tabla_estadisticas = self.crear_tabla(tab_estadisticas, ("estadistica", "valor", "ev"))
        self.tabla_estadisticas.heading("estadistica", text="Estadistica")
        self.tabla_estadisticas.heading("valor", text="Valor base")
        self.tabla_estadisticas.heading("ev", text="EV")

        self.tabla_habilidades = self.crear_tabla(tab_habilidades, ("habilidad", "tipo"))
        self.tabla_habilidades.heading("habilidad", text="Habilidad")
        self.tabla_habilidades.heading("tipo", text="Tipo")

        self.tabla_sprites = self.crear_tabla(tab_sprites, ("descripcion", "url"))
        self.tabla_sprites.heading("descripcion", text="Sprite")
        self.tabla_sprites.heading("url", text="URL")
        self.tabla_sprites.column("url", width=520)

        self.tabla_evolucion = self.crear_tabla(tab_evolucion, ("etapa", "pokemon", "metodo"))
        self.tabla_evolucion.heading("etapa", text="Etapa")
        self.tabla_evolucion.heading("pokemon", text="Pokemon")
        self.tabla_evolucion.heading("metodo", text="Metodo")
        self.tabla_evolucion.column("metodo", width=420)

        self.lista_movimientos = self.crear_lista_con_scroll(tab_movimientos)

    def crear_tabla(self, parent, columnas):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        tabla = ttk.Treeview(parent, columns=columnas, show="headings")
        tabla.grid(row=0, column=0, sticky="nsew")

        for columna in columnas:
            tabla.column(columna, width=140, anchor="w")

        scroll = ttk.Scrollbar(parent, orient="vertical", command=tabla.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        tabla.configure(yscrollcommand=scroll.set)

        return tabla

    def crear_lista_con_scroll(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        lista = tk.Listbox(
            parent,
            borderwidth=0,
            activestyle="none",
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground="#d8dee9",
        )
        lista.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(parent, orient="vertical", command=lista.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        lista.configure(yscrollcommand=scroll.set)

        return lista

    def ejecutar_en_segundo_plano(self, tarea, al_completar, al_fallar):
        def worker():
            try:
                resultado = tarea()
            except Exception as e:
                self.after(0, lambda: al_fallar(e))
            else:
                self.after(0, lambda: al_completar(resultado))

        threading.Thread(target=worker, daemon=True).start()

    def actualizar_lista_favoritos(self):
        self.lista_favoritos.delete(0, tk.END)

        for nombre in self.favoritos:
            self.lista_favoritos.insert(tk.END, nombre)

    def actualizar_boton_favorito(self):
        if not self.current_pokemon_name:
            self.boton_favorito.configure(text="Agregar favorito", state="disabled")
            return

        if self.current_pokemon_name in self.favoritos:
            self.boton_favorito.configure(text="Quitar favorito", state="normal")
        else:
            self.boton_favorito.configure(text="Agregar favorito", state="normal")

    def guardar_y_refrescar_favoritos(self):
        guardar_favoritos(self.favoritos)
        self.favoritos = cargar_favoritos()
        self.actualizar_lista_favoritos()
        self.actualizar_boton_favorito()

    def alternar_favorito_actual(self):
        if not self.current_pokemon_name:
            return

        if self.current_pokemon_name in self.favoritos:
            self.favoritos.remove(self.current_pokemon_name)
            accion = "quitado de favoritos"
        else:
            self.favoritos.append(self.current_pokemon_name)
            accion = "agregado a favoritos"

        try:
            self.guardar_y_refrescar_favoritos()
        except OSError as e:
            self.estado_var.set(f"No se pudieron guardar los favoritos: {e}")
            return

        self.estado_var.set(f"{self.current_pokemon_name} {accion}.")

    def quitar_favorito_seleccionado(self):
        seleccion = self.lista_favoritos.curselection()

        if not seleccion:
            self.estado_var.set("Selecciona un favorito para quitarlo.")
            return

        nombre = self.lista_favoritos.get(seleccion[0])

        if nombre in self.favoritos:
            self.favoritos.remove(nombre)

        try:
            self.guardar_y_refrescar_favoritos()
        except OSError as e:
            self.estado_var.set(f"No se pudieron guardar los favoritos: {e}")
            return

        self.estado_var.set(f"{nombre} quitado de favoritos.")

    def buscar_desde_lista_favoritos(self, event=None):
        seleccion = self.lista_favoritos.curselection()

        if not seleccion:
            return

        nombre = self.lista_favoritos.get(seleccion[0])
        self.nombre_var.set(nombre)
        self.buscar_por_nombre()

    def iniciar_juego(self):
        self.boton_nueva_ronda.configure(state="disabled")
        self.boton_comprobar_juego.configure(state="disabled")
        self.boton_rendirse_juego.configure(state="disabled")
        self.juego_respuesta_entry.configure(state="disabled")
        self.juego_respuesta_var.set("")
        self.juego_pokemon = None
        self.juego_imagen_base64 = None
        self.juego_image = None
        self.juego_intentos = 0
        self.juego_resuelto = False
        self.juego_imagen_label.configure(image="", text="?")
        self.juego_intentos_label.configure(text=f"Intentos: 0/{JUEGO_INTENTOS_MAX}")
        self.lista_pistas_juego.delete(0, tk.END)
        self.lista_pistas_juego.insert(tk.END, "Preparando una nueva ronda...")
        self.estado_var.set("Cargando Pokemon secreto...")

        def tarea():
            pokemon = obtener_pokemon_aleatorio_juego()
            imagen = descargar_imagen_base64(obtener_url_sprite_principal(pokemon))
            return pokemon, imagen

        def al_completar(resultado):
            pokemon, imagen = resultado
            self.juego_pokemon = pokemon
            self.juego_imagen_base64 = imagen
            self.lista_pistas_juego.delete(0, tk.END)

            for pista in crear_pistas_juego(pokemon):
                self.lista_pistas_juego.insert(tk.END, pista)

            self.boton_nueva_ronda.configure(state="normal")
            self.boton_comprobar_juego.configure(state="normal")
            self.boton_rendirse_juego.configure(state="normal")
            self.juego_respuesta_entry.configure(state="normal")
            self.juego_respuesta_entry.focus_set()
            self.estado_var.set("Adivina el Pokemon secreto.")

        def al_fallar(error):
            self.boton_nueva_ronda.configure(state="normal")
            self.lista_pistas_juego.delete(0, tk.END)
            self.lista_pistas_juego.insert(tk.END, "No se pudo iniciar la ronda.")

            if isinstance(error, ErrorConsultaPokemon):
                self.estado_var.set(f"Error de red: {error}")
            else:
                self.estado_var.set(f"Error inesperado: {error}")

        self.ejecutar_en_segundo_plano(tarea, al_completar, al_fallar)

    def comprobar_respuesta_juego(self, event=None):
        if not self.juego_pokemon or self.juego_resuelto:
            return

        respuesta = normalizar_texto(self.juego_respuesta_var.get())

        if not respuesta:
            self.estado_var.set("Escribe una respuesta antes de comprobar.")
            return

        nombre_correcto = normalizar_texto(self.juego_pokemon["name"])

        if respuesta == nombre_correcto:
            self.juego_resuelto = True
            self.revelar_pokemon_juego()
            self.boton_comprobar_juego.configure(state="disabled")
            self.boton_rendirse_juego.configure(state="disabled")
            self.juego_respuesta_entry.configure(state="disabled")
            self.estado_var.set(f"Correcto: era {self.juego_pokemon['name']}!")
            return

        self.juego_intentos += 1
        self.juego_intentos_label.configure(text=f"Intentos: {self.juego_intentos}/{JUEGO_INTENTOS_MAX}")

        if self.juego_intentos >= JUEGO_INTENTOS_MAX:
            self.juego_resuelto = True
            self.revelar_pokemon_juego()
            self.boton_comprobar_juego.configure(state="disabled")
            self.boton_rendirse_juego.configure(state="disabled")
            self.juego_respuesta_entry.configure(state="disabled")
            self.estado_var.set(f"Sin intentos. Era {self.juego_pokemon['name']}.")
            return

        restantes = JUEGO_INTENTOS_MAX - self.juego_intentos
        self.estado_var.set(f"No es correcto. Te quedan {restantes} intento(s).")
        self.juego_respuesta_var.set("")
        self.juego_respuesta_entry.focus_set()

    def rendirse_juego(self):
        if not self.juego_pokemon or self.juego_resuelto:
            return

        self.juego_resuelto = True
        self.revelar_pokemon_juego()
        self.boton_comprobar_juego.configure(state="disabled")
        self.boton_rendirse_juego.configure(state="disabled")
        self.juego_respuesta_entry.configure(state="disabled")
        self.estado_var.set(f"Era {self.juego_pokemon['name']}.")

    def revelar_pokemon_juego(self):
        self.actualizar_imagen_juego(self.juego_imagen_base64)
        self.juego_respuesta_var.set(self.juego_pokemon["name"])

    def actualizar_imagen_juego(self, imagen_base64):
        if not imagen_base64:
            self.juego_image = None
            self.juego_imagen_label.configure(image="", text=self.juego_pokemon["name"].title())
            return

        try:
            imagen = tk.PhotoImage(data=imagen_base64)
        except tk.TclError:
            self.juego_image = None
            self.juego_imagen_label.configure(image="", text=self.juego_pokemon["name"].title())
            return

        factor = max(1, (imagen.width() + 139) // 140, (imagen.height() + 139) // 140)

        if factor > 1:
            imagen = imagen.subsample(factor, factor)

        self.juego_image = imagen
        self.juego_imagen_label.configure(image=self.juego_image, text="")

    def buscar_por_nombre(self, event=None):
        nombre = self.nombre_var.get().strip()

        if not nombre:
            self.estado_var.set("Escribe el nombre de un Pokemon.")
            return

        self.boton_nombre.configure(state="disabled")
        self.estado_var.set(f"Buscando {nombre}...")

        def tarea():
            pokemon = obtener_pokemon_por_nombre(nombre)
            imagen = descargar_imagen_base64(obtener_url_sprite_principal(pokemon))

            try:
                evolucion = obtener_evolucion_pokemon(pokemon)
            except (ErrorConsultaPokemon, RecursoNoEncontrado) as e:
                evolucion = [(0, "No disponible", str(e) or "No se pudo cargar la evolucion.")]

            return pokemon, imagen, evolucion

        def al_completar(resultado):
            self.boton_nombre.configure(state="normal")
            pokemon, imagen, evolucion = resultado
            self.mostrar_pokemon_en_interfaz(pokemon, imagen, evolucion)
            self.estado_var.set(f"{pokemon['name']} cargado.")

        def al_fallar(error):
            self.boton_nombre.configure(state="normal")

            if isinstance(error, PokemonNoEncontrado):
                self.estado_var.set("No se encontro ese Pokemon. Intentalo de nuevo.")
            elif isinstance(error, ErrorConsultaPokemon):
                self.estado_var.set(f"Error de red: {error}")
            else:
                self.estado_var.set(f"Error inesperado: {error}")

        self.ejecutar_en_segundo_plano(tarea, al_completar, al_fallar)

    def buscar_por_tipo(self, event=None):
        tipo = self.tipo_var.get().strip()

        if not tipo:
            self.estado_var.set("Escribe o selecciona un tipo.")
            return

        self.boton_tipo.configure(state="disabled")
        self.lista_tipo.delete(0, tk.END)
        self.estado_var.set(f"Buscando Pokemon de tipo {tipo}...")

        def tarea():
            return obtener_pokemon_por_tipo(tipo)

        def al_completar(nombres):
            self.boton_tipo.configure(state="normal")

            for nombre in nombres:
                self.lista_tipo.insert(tk.END, nombre)

            self.estado_var.set(f"Se encontraron {len(nombres)} Pokemon de tipo {normalizar_tipo(tipo)}.")

        def al_fallar(error):
            self.boton_tipo.configure(state="normal")

            if isinstance(error, TipoNoEncontrado):
                self.estado_var.set("No se encontro ese tipo. Prueba con fire, water, grass...")
            elif isinstance(error, ErrorConsultaPokemon):
                self.estado_var.set(f"Error de red: {error}")
            else:
                self.estado_var.set(f"Error inesperado: {error}")

        self.ejecutar_en_segundo_plano(tarea, al_completar, al_fallar)

    def buscar_desde_lista_tipo(self, event=None):
        seleccion = self.lista_tipo.curselection()

        if not seleccion:
            return

        nombre = self.lista_tipo.get(seleccion[0])
        self.nombre_var.set(nombre)
        self.buscar_por_nombre()

    def mostrar_pokemon_en_interfaz(self, pokemon_data, imagen_base64, evolucion):
        nombre = pokemon_data["name"].title()
        self.current_pokemon_name = pokemon_data["name"]
        tipos = ", ".join(tipo["type"]["name"] for tipo in pokemon_data["types"])

        self.nombre_label.configure(text=nombre)
        self.tipos_label.configure(text=f"Tipos: {tipos}")
        self.altura_label.configure(text=f"Altura: {pokemon_data['height'] * 10} cm")
        self.peso_label.configure(text=f"Peso: {pokemon_data['weight'] / 10} kg")
        self.boton_favorito.configure(state="normal")
        self.actualizar_boton_favorito()
        self.actualizar_imagen(imagen_base64)

        self.limpiar_tabla(self.tabla_estadisticas)
        for nombre_stat, valor_base, esfuerzo in recopilar_estadisticas(pokemon_data):
            self.tabla_estadisticas.insert("", tk.END, values=(nombre_stat, valor_base, esfuerzo))

        self.limpiar_tabla(self.tabla_habilidades)
        for habilidad, tipo in recopilar_habilidades(pokemon_data):
            self.tabla_habilidades.insert("", tk.END, values=(habilidad, tipo))

        self.limpiar_tabla(self.tabla_sprites)
        for descripcion, url_sprite in recopilar_sprites(pokemon_data):
            self.tabla_sprites.insert("", tk.END, values=(descripcion, url_sprite))

        self.limpiar_tabla(self.tabla_evolucion)
        for etapa, pokemon, metodo in evolucion:
            self.tabla_evolucion.insert("", tk.END, values=(etapa, pokemon, metodo))

        self.lista_movimientos.delete(0, tk.END)
        for move in pokemon_data["moves"]:
            self.lista_movimientos.insert(tk.END, move["move"]["name"])

    def actualizar_imagen(self, imagen_base64):
        if not imagen_base64:
            self.sprite_image = None
            self.sprite_label.configure(image="", text="Sin imagen")
            return

        try:
            imagen = tk.PhotoImage(data=imagen_base64)
        except tk.TclError:
            self.sprite_image = None
            self.sprite_label.configure(image="", text="Sin imagen")
            return

        factor = max(1, (imagen.width() + 179) // 180, (imagen.height() + 179) // 180)

        if factor > 1:
            imagen = imagen.subsample(factor, factor)

        self.sprite_image = imagen
        self.sprite_label.configure(image=self.sprite_image, text="")

    @staticmethod
    def limpiar_tabla(tabla):
        for item in tabla.get_children():
            tabla.delete(item)


if __name__ == "__main__":
    app = PokemonApp()
    app.mainloop()
