"""
banderas.py — Mapea nombres de selecciones a códigos de bandera (flagcdn.com, gratis).
Para clubes (ligas) no hay bandera de país útil: el frontend dibuja un monograma
con las iniciales, y si está API-Football se usa el logo real del club.
"""

# nombre (en minúsculas) -> código flagcdn (ISO 3166-1 alpha-2, o gb-eng/sct/wls)
ISO = {
    "mexico":"mx","méxico":"mx","south africa":"za","sudáfrica":"za","sudafrica":"za",
    "canada":"ca","canadá":"ca","bosnia":"ba","bosnia and herzegovina":"ba",
    "usa":"us","united states":"us","estados unidos":"us","paraguay":"py",
    "brazil":"br","brasil":"br","morocco":"ma","marruecos":"ma","haiti":"ht","haití":"ht",
    "spain":"es","españa":"es","cape verde":"cv","cabo verde":"cv",
    "france":"fr","francia":"fr","senegal":"sn","argentina":"ar","algeria":"dz","argelia":"dz",
    "england":"gb-eng","inglaterra":"gb-eng","croatia":"hr","croacia":"hr",
    "portugal":"pt","dr congo":"cd","rd congo":"cd","congo dr":"cd",
    "colombia":"co","uzbekistan":"uz","uzbekistán":"uz",
    "germany":"de","alemania":"de","ivory coast":"ci","costa de marfil":"ci","côte d'ivoire":"ci",
    "curacao":"cw","curaçao":"cw","ecuador":"ec","jordan":"jo","jordania":"jo",
    "austria":"at","uruguay":"uy","saudi arabia":"sa","arabia saudí":"sa","arabia saudita":"sa",
    "netherlands":"nl","países bajos":"nl","holanda":"nl","belgium":"be","bélgica":"be",
    "italy":"it","italia":"it","switzerland":"ch","suiza":"ch","scotland":"gb-sct","escocia":"gb-sct",
    "wales":"gb-wls","gales":"gb-wls","japan":"jp","japón":"jp","south korea":"kr","corea del sur":"kr",
    "korea republic":"kr","australia":"au","iran":"ir","irán":"ir","qatar":"qa","ghana":"gh",
    "cameroon":"cm","camerún":"cm","nigeria":"ng","egypt":"eg","egipto":"eg","tunisia":"tn","túnez":"tn",
    "denmark":"dk","dinamarca":"dk","poland":"pl","polonia":"pl","serbia":"rs","turkey":"tr","turquía":"tr",
    "peru":"pe","perú":"pe","chile":"cl","venezuela":"ve","bolivia":"bo","panama":"pa","panamá":"pa",
    "costa rica":"cr","honduras":"hn","new zealand":"nz","nueva zelanda":"nz","norway":"no","noruega":"no",
    "sweden":"se","suecia":"se","greece":"gr","grecia":"gr","ukraine":"ua","ucrania":"ua",
    "czech republic":"cz","czechia":"cz","república checa":"cz","republica checa":"cz",
}


def iso_de(nombre: str) -> str | None:
    if not nombre:
        return None
    return ISO.get(nombre.strip().lower())


def flag_url(nombre: str) -> str | None:
    iso = iso_de(nombre)
    return f"https://flagcdn.com/w160/{iso}.png" if iso else None
