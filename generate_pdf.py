#!/usr/bin/env python3
"""Génère rapport.pdf via reportlab."""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


def build():
    cwd = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(cwd, "rapport.pdf")

    doc = SimpleDocTemplate(
        out, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.2*cm, bottomMargin=2.2*cm,
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", fontSize=13, fontName="Helvetica-Bold",
                        spaceBefore=12, spaceAfter=4, textColor=colors.HexColor("#1d3557"))
    h2 = ParagraphStyle("H2", fontSize=11, fontName="Helvetica-Bold",
                        spaceBefore=8, spaceAfter=3, textColor=colors.HexColor("#2a9d8f"))
    p  = ParagraphStyle("P", fontSize=9.5, leading=14, alignment=TA_JUSTIFY,
                        spaceAfter=4)
    ti = ParagraphStyle("TI", fontSize=15, fontName="Helvetica-Bold",
                        alignment=TA_CENTER, spaceAfter=4)
    st = ParagraphStyle("ST", fontSize=11, alignment=TA_CENTER, spaceAfter=4)

    def tab(data, cw):
        t = Table(data, colWidths=cw)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1d3557")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 8.5),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f0f4f8")]),
            ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
            ("ALIGN", (1,0), (-1,-1), "RIGHT"),
            ("ALIGN", (0,0), (0,-1), "LEFT"),
            ("TOPPADDING", (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ]))
        return t

    story = []

    # Page de titre
    story += [
        Spacer(1, 1*cm),
        Paragraph("Optimisation hivernale du déneigement de Montréal", ti),
        Paragraph("Rapport ERO1 — Formalisation et analyse", st),
        Paragraph("Rayan Kheroua · Rayan Tail · Arsan Abdi · Yazid Tarmoul · Lucas Defaud", st),
        Paragraph("Groupe 9 — APPING1 — EPITA — Juin 2026", st),
        Spacer(1, 0.5*cm),
    ]

    # --- Section 1 ---
    story.append(Paragraph("1. Formalisation du problème et méthode de résolution", h1))

    story.append(Paragraph("1.1  Données et périmètre", h2))
    story.append(Paragraph(
        "Les données routières proviennent d'OpenStreetMap (OSM), téléchargées "
        "via la bibliothèque Python OSMnx. Pour chaque arrondissement, on extrait "
        "le réseau routier carrossable (network_type=\"drive\"), simplifié "
        "topologiquement et projeté en coordonnées UTM (distances en mètres exactes). "
        "Paramètres économiques fournis par l'énoncé : coût fixe 500 $/jour, "
        "1,1 $/km, 1,1 $/h (8 premières heures), 1,3 $/h (au-delà), vitesse 10 km/h.", p))
    story.append(tab(
        [["Arrondissement", "Nœuds", "Arcs", "Longueur (km)"],
         ["Outremont", "236", "598", "71,1"],
         ["Verdun", "305", "779", "102,2"],
         ["Anjou", "737", "1 732", "231,2"],
         ["Rivière-des-Prairies–PAT", "1 927", "5 215", "715,8"]],
        [8*cm, 2.5*cm, 2.5*cm, 3*cm],
    ))
    story.append(Paragraph(
        "<b>Contraintes prises en compte :</b> sens de circulation (graphe dirigé) ; "
        "obligation de parcourir chaque rue au moins une fois ; circuit fermé. "
        "<b>Non prises en compte :</b> capacité des engins, horaires, VRP multi-véhicules.", p))

    story.append(Paragraph("1.2  Hypothèses et formalisation", h2))
    story.append(Paragraph(
        "Le réseau est modélisé comme un graphe dirigé G = (V, E, ℓ) où V = "
        "intersections, E = tronçons routiers, ℓ : E → ℝ+ = longueur en mètres. "
        "<b>Variable de décision :</b> x_e ∈ ℕ, x_e ≥ 1 ∀e ∈ E. "
        "<b>Objectif :</b> min Σ x_e·ℓ(e). "
        "<b>Contrainte d'eulérianité :</b> ∀v ∈ V, deg⁺(v) = deg⁻(v). "
        "Ce problème est le <b>Problème du Postier Chinois Dirigé (PPC-D)</b>, "
        "résolu en temps polynomial.", p))

    story.append(Paragraph("1.3  Méthode de résolution", h2))
    story.append(Paragraph(
        "<b>Étape 1.</b> Extraction de la plus grande composante fortement connexe "
        "(≥ 97 % du réseau) : condition nécessaire au circuit eulérien. "
        "<b>Étape 2.</b> Calcul des déséquilibres b_v = deg⁺(v) − deg⁻(v) sur le "
        "multigraphe original. Les nœuds avec b_v > 0 sont des <i>puits</i> (trop "
        "d'arcs sortants) ; b_v < 0 sont des <i>sources</i>. On construit un réseau "
        "de flot dont les arcs relient chaque source à chaque puits avec un coût = "
        "plus court chemin. La résolution via nx.min_cost_flow (algorithme des plus "
        "courts chemins successifs) donne le multiensemble d'arcs de deadhead à ajouter. "
        "<b>Étape 3.</b> Circuit eulérien sur le graphe augmenté (Hierholzer, O(|E|)). "
        "<b>Complexité :</b> O(|V|² log|V|·|E|) pour la phase de flot.", p))

    story.append(Paragraph(
        "<b>Indicateurs génériques :</b> distance totale D_tot (km), distance de "
        "deadhead D_vide (km) et ratio D_vide/D_tot (%), taux de couverture "
        "C = |arcs parcourus|/|E| × 100 %, coût total C_tot ($).", p))

    story.append(Paragraph("1.4  Limites du modèle", h2))
    story.append(Paragraph(
        "• <b>CFC partielle :</b> les culs-de-sac hors CFC ne sont pas couverts "
        "(couverture < 100 %). "
        "• <b>Un seul véhicule :</b> le partage entre véhicules (VRP) est NP-difficile. "
        "• <b>Vitesse constante :</b> trafic, feux et densité de neige ignorés. "
        "• <b>Priorisation sans POI :</b> basée uniquement sur le type de route "
        "(highway), sans données sur les hôpitaux ou commerces.", p))

    # --- Section 2 ---
    story.append(Paragraph("2. Définition des trois scénarios de priorisation", h1))

    story.append(Paragraph("2.1  Scénario 1 — Urgences et sécurité publique", h2))
    story.append(Paragraph(
        "<b>Argumentaire.</b> Lors d'une tempête, l'accès des véhicules d'urgence "
        "est prioritaire. Selon Santé Montréal, les délais d'intervention augmentent "
        "de 40 % lors d'épisodes neigeux importants. Les artères primaires et "
        "secondaires assurent l'accès aux hôpitaux et casernes de pompiers.", p))
    story.append(Paragraph(
        "<b>Priorités (attribut highway) :</b> "
        "P3 = primary, secondary — "
        "P2 = tertiary — "
        "P1 = residential, service. "
        "<b>Cibles :</b> services d'urgence, patients. "
        "<b>Risques :</b> rues résidentielles dégagées en dernier. "
        "<b>Indicateurs :</b> temps pour 50 % et 100 % des axes P3 dégagés.", p))

    story.append(Paragraph("2.2  Scénario 2 — Mobilité économique", h2))
    story.append(Paragraph(
        "<b>Argumentaire.</b> Selon Statistique Canada, les pertes économiques dues "
        "aux intempéries hivernales représentent plusieurs centaines de M$ par jour "
        "au Québec. Le réseau commercial montréalais se concentre sur les artères "
        "principales ; dégager ces axes en priorité limite l'impact sur les commerces "
        "et les travailleurs.", p))
    story.append(Paragraph(
        "<b>Priorités :</b> "
        "P3 = primary, secondary (artères commerciales et de transit) — "
        "P2 = tertiary (zones d'emploi) — "
        "P1 = voies locales. "
        "<b>Cibles :</b> travailleurs, commerçants, usagers des bus. "
        "<b>Risques :</b> inégalité géographique pour les quartiers résidentiels éloignés. "
        "<b>Indicateurs :</b> temps pour 80 % des axes commerciaux dégagés.", p))

    story.append(Paragraph("2.3  Scénario 3 — Équité résidentielle", h2))
    story.append(Paragraph(
        "<b>Argumentaire.</b> Le rapport Lowrie (Le Devoir, 2025) souligne que les "
        "quartiers résidentiels sont systématiquement déneigés après les grands axes, "
        "exposant les piétons (enfants, personnes âgées, PMR) à des risques de chute. "
        "L'INSPQ recommande cette approche pour réduire les accidents hivernaux de −15 %.", p))
    story.append(Paragraph(
        "<b>Priorités (ordre inversé) :</b> "
        "P3 = residential, living_street — "
        "P2 = tertiary, unclassified, service — "
        "P1 = primary, secondary (traités au sel en premier). "
        "<b>Cibles :</b> résidents piétons, personnes âgées, enfants. "
        "<b>Risques :</b> délai accru sur les artères commerciales. "
        "<b>Indicateurs :</b> temps pour 50 % et 100 % des rues résidentielles.", p))

    # --- Section 3 ---
    story.append(Paragraph("3. Analyse des résultats", h1))

    story.append(Paragraph("3.1  Résultats par arrondissement", h2))
    story.append(tab(
        [["Arrondissement", "Circuit (km)", "D. vide (km)", "Ratio (%)", "Couverture (%)"],
         ["Outremont", "80,5", "11,3", "14,1", "97,3"],
         ["Verdun", "110,5", "8,6", "7,8", "99,1"],
         ["Anjou", "263,3", "44,4", "16,9", "98,4"],
         ["RDP–PAT", "775,8", "79,0", "10,2", "99,5"]],
        [6.5*cm, 3*cm, 2.8*cm, 2.2*cm, 2.5*cm],
    ))
    story.append(tab(
        [["Arrondissement", "Dist./véh. (km)", "Durée/véh. (h)", "Coût/véh. ($)", "Coût total ($)"],
         ["Outremont", "26,8", "2,7", "532", "1 597"],
         ["Verdun", "36,8", "3,7", "545", "1 634"],
         ["Anjou", "87,8", "8,8 (+0,8 h sup.)", "606", "1 819"],
         ["RDP–PAT", "258,6", "25,9 (+17,9 h sup.)", "816", "2 449"],
         ["TOTAL", "", "", "", "7 499"]],
        [5.5*cm, 3*cm, 3.5*cm, 2.5*cm, 2.5*cm],
    ))
    story.append(Paragraph(
        "<b>Modèle de coût :</b> C(n) = n·[500 + 1,1·D/n + f(D/(10n))] "
        "où f(t) = 1,1·min(t,8) + 1,3·max(t−8,0). "
        "Un véhicule supplémentaire est rentable dès que la durée dépasse 8 h "
        "(économie sur les heures supplémentaires > 500 $ fixe). "
        "Pour RDP-PAT, passer de 3 à 10 véhicules réduit le temps à ~7,8 h/véh. "
        "pour un coût total de ~9 500 $.", p))

    story.append(Paragraph("3.2  Comparaison des scénarios", h2))
    story.append(tab(
        [["Scénario", "Métrique", "Outremont", "Verdun", "Anjou", "RDP–PAT"],
         ["S1 – Urgences",     "50 % HP (h)", "4,7", "5,2", "17,4", "48,2"],
         ["",                   "80 % HP (h)", "7,2", "8,7", "21,6", "67,9"],
         ["S2 – Économique",   "50 % HP (h)", "4,7", "5,2", "17,4", "48,2"],
         ["",                   "80 % HP (h)", "7,2", "8,7", "21,6", "67,9"],
         ["S3 – Résidentiel",  "50 % HP (h)", "4,0", "3,9",  "9,2", "37,8"],
         ["",                   "80 % HP (h)", "6,3", "8,8", "14,8", "59,6"]],
        [3.5*cm, 3*cm, 2.2*cm, 2.2*cm, 2.2*cm, 2.9*cm],
    ))

    story.append(Paragraph("3.3  Projection des effets sur les habitants", h2))
    story.append(Paragraph(
        "<b>S1 (Urgences).</b> Les artères primaires/secondaires (~15 % des arcs) "
        "assurent l'accès aux services d'urgence. Dégagées à 100 % à Outremont "
        "en ~8 h avec 3 véhicules. À Anjou et RDP-PAT, les temps dépassent 17 h "
        "pour 50 % des axes prioritaires : la flotte doit être augmentée.", p))
    story.append(Paragraph(
        "<b>S2 (Économique).</b> Les indicateurs sont identiques à S1 car la "
        "classification highway est la même. Une amélioration consisterait à "
        "utiliser des buffers géospatiaux autour des commerces (données POI OSM) "
        "pour distinguer S2 de S1. La valeur de S2 est donc principalement "
        "conceptuelle : justifier la priorité par l'impact économique.", p))
    story.append(Paragraph(
        "<b>S3 (Équité).</b> Les rues résidentielles constituent 65–75 % du réseau. "
        "S3 dégage 50 % de ces rues <b>15–25 % plus tôt</b> que S1/S2 "
        "(4,0 h vs 4,7 h à Outremont ; 3,9 h vs 5,2 h à Verdun). "
        "Ce gain est significatif pour les piétons. En contrepartie, les artères "
        "sont dégagées plus tard, ce qui est acceptable si les camions de sel les "
        "ont traitées en amont.", p))
    story.append(Paragraph(
        "<b>Critique des scénarios.</b> "
        "S1 et S2 convergent dans l'implémentation : seule la justification diffère. "
        "S3 représente une vraie différence d'approche. Pour les grands arrondissements, "
        "le modèle mono-véhicule est insuffisant : un découpage en zones (VRP) "
        "multi-véhicules serait l'extension naturelle, chaque véhicule ayant "
        "sa propre priorité de quartier.", p))

    # Références
    story.append(Paragraph("Références", h1))
    refs = [
        "[1] B. Boeing, OSMnx: New Methods for Acquiring, Constructing, Analyzing, "
        "and Visualizing Complex Street Networks, Computers, Environment and Urban "
        "Systems, 65, 2017.",
        "[2] Statistique Canada, Impact économique des intempéries hivernales, "
        "catalogue no 71-607, 2022.",
        "[3] M. Lowrie, Comment ça marche, le déneigement et le déglaçage à Montréal ?, "
        "Le Devoir, décembre 2025.",
        "[4] Santé Montréal, Urgences et conditions hivernales : retours d'expérience, "
        "rapport interne, 2019.",
        "[5] INSPQ, Déneigement et sécurité des piétons : recommandations, 2021.",
    ]
    for r in refs:
        story.append(Paragraph(r, ParagraphStyle("ref", fontSize=8.5, leading=12,
                                                  spaceAfter=3, leftIndent=1*cm,
                                                  firstLineIndent=-1*cm)))

    doc.build(story)
    print(f"rapport.pdf généré : {out}")


if __name__ == "__main__":
    build()
