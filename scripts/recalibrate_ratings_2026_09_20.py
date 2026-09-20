from pathlib import Path
import re, json

path = Path("cigar_inventory.html")
html = path.read_text(encoding="utf-8")

updates = {
"04": ("B","Predicted","Chocolate, leather and assertive spice can fit your palate when the spice is integrated rather than dominant. Medium–Full strength adds some uncertainty, but spice itself is now treated as a positive source of complexity when balanced."),
"06": ("B","You rated B","You rated CAO Cameroon L’Anniversaire a B. You liked the initial flavors, but they softened as the cigar progressed and it became somewhat harsh. The direct rating replaces the earlier A prediction."),
"07": ("B","Predicted","Nuts, coffee and sweetness fit your palate, but the lower-intensity profile has not yet shown the flavor prominence and persistence now required for an A prediction."),
"10": ("B","Predicted","Coffee and the cigar’s spice can be positive when integrated with the other flavors. The lingering pepper still creates uncertainty about balance, but pepper is no longer treated as an automatic mismatch."),
"22": ("B","You enjoyed · below A","You enjoyed this Perdomo Habano Connecticut and preferred its flavor profile to the CAO Cameroon L’Anniversaire, but you specifically said it was not an A because the flavors were not prominent enough. Your direct feedback determines the B."),
"23": ("A","Predicted","Earth, wood, stone-fruit sweetness and baking spice combine several traits you enjoy. Balanced spice is a positive, and the profile appears flavorful and layered enough to make this an A candidate."),
"25": ("B","Predicted","Chocolate, earth and pepper-led phases can work well for you when the spice stays integrated. The relatively linear development remains a reservation, but pepper itself no longer justifies a C."),
"32": ("B","Predicted","Toasted nuts and the richer Oscuro profile fit your preferences. Prominent pepper is not automatically negative because you enjoy balanced spice; B reflects uncertainty about whether the pepper integrates with the other flavors."),
"33": ("B","Predicted","Sweet Maduro richness and pepper can be a strong combination for you, especially given your love of Schizo Maduro. B reflects uncertainty about persistence, complexity and whether the pepper stays balanced rather than a general penalty for spice."),
"36": ("B","Predicted","Nutty, toasty flavors fit your palate, and an early pepper phase can add complexity when balanced. The larger format and mixed reports on intensity keep this below A, not the presence of spice itself."),
"37": ("B","Predicted","Almond, toast, cinnamon, coffee and shifting sweetness offer several compatible layers. Lingering black pepper can be enjoyable if integrated; B reflects uncertainty about the final balance rather than a pepper penalty."),
"41": ("A","Predicted","Cocoa, espresso, earth, cedar and noticeable spice strongly overlap with the richer, more prominent flavor profile you now appear to favor. Medium–Full strength remains a consideration, but balanced spice is a positive rather than a deduction."),
"44": ("B","Predicted","Earth, nuts, sweetness and substantial spice can suit you when balanced. The Full rating and reports of thick spicy smoke still create intensity risk, but black pepper alone no longer warrants a C."),
"48": ("A","Predicted","Chocolate, nuts, coffee and dried fruit provide the richer, roasted and naturally sweet flavor cluster that overlaps with CAO Black and Schizo Maduro. Medium to Medium–Full intensity and integrated spice make this a stronger A candidate."),
"56": ("B","Predicted","This cigar’s complexity, balance and substantial spice can all be positives for you. Medium–Full to Full strength keeps some risk, but the earlier C over-penalized a spicy/peppery profile without enough regard for whether the spice is balanced."),
"63": ("A","Predicted","Dark chocolate, almond, espresso and coconut overlap strongly with the rich, roasted, sweet and nutty flavors you enjoy. Its layered complexity and spice make it a stronger A candidate when the pepper remains integrated."),
"68": ("B","Predicted","Coffee, chocolate, oak, leather and spice offer the kind of prominent, layered profile you increasingly appear to favor. Medium–Full strength creates some risk, but spice and pepper are not negatives when balanced."),
"69": ("B","Predicted","The shorter format combines coffee, chocolate, oak and spice in a more manageable smoking length. Medium–Full strength remains a consideration, but balanced pepper can improve rather than diminish the experience."),
"70": ("A","Predicted","Roasted nuts, cocoa, earth and a smaller 42-ring Corona strongly match your flavor preferences. Pepper can add welcome contrast when balanced, so the previous B was too cautious about spice."),
"74": ("A","Predicted","Cocoa, graham-cracker and tropical-fruit sweetness combine with documented complexity and aromatic spice. Those characteristics align well with your preference for prominent, layered flavor with balanced spice.")
}

def update_row(html, num, grade, basis, reason):
    pat = re.compile(r'<tr\b(?=[^>]*\bid="cigar-'+re.escape(num)+r'")[\s\S]*?</tr>')
    m = pat.search(html)
    if not m:
        raise RuntimeError(f"row {num} not found")
    row = m.group(0)
    row = re.sub(r'data-grade="[^"]*"', f'data-grade="{grade}"', row, count=1)
    row = re.sub(r'<span aria-label="Grade [^"]*" class="grade grade-[^"]*">[^<]*</span>',
                 f'<span aria-label="Grade {grade}" class="grade grade-{grade}">{grade}</span>', row, count=1)
    row = re.sub(r'<span class="grade-basis">[\s\S]*?</span>',
                 f'<span class="grade-basis">{basis}</span>', row, count=1)
    row = re.sub(r'<p class="fit-reason">[\s\S]*?</p>',
                 f'<p class="fit-reason">{reason}</p>', row, count=1)
    return html[:m.start()] + row + html[m.end():]

for num, vals in updates.items():
    html = update_row(html, num, *vals)

html = re.sub(r'Research updated [A-Za-z]+ \d{1,2}, \d{4}', 'Preferences recalibrated September 20, 2026', html, count=1)
html = re.sub(r'<p class="update-note">[\s\S]*?</p>',
'''<p class="update-note"><strong>Ratings recalibrated September 20, 2026.</strong> Latest smoking feedback now gives more weight to flavor prominence and persistence, sustained smoothness, roasted/nutty/earthy/sweet flavor combinations, and complexity. Balanced spice is treated as something you enjoy and as a positive contributor; only dominant or poorly integrated pepper/spice is a mismatch. Direct ratings now record CAO Cameroon L’Anniversaire as B and Perdomo Habano Bourbon Barrel-Aged Connecticut as enjoyed but below A because its flavors were not prominent enough. Inventory quantities are unchanged.</p>''', html, count=1)

html = html.replace(
'Spice as an accent is different from pepper dominating the smoke.',
'Balanced spice is a positive attribute you actively enjoy when it complements the other flavors. Dominant or poorly integrated pepper/spice is different and can still reduce fit.'
)

m = re.search(r'(<script id="cigar-preferences" type="application/json">\s*)([\s\S]*?)(\s*</script>)', html)
if not m:
    raise RuntimeError("preference JSON not found")
prefs = json.loads(m.group(2))
prefs["version"] = 9
prefs["updated"] = "2026-09-20"
prefs["strength_preference"] = "Mood-dependent, but Full is rarely enjoyed. Balanced spice is actively enjoyed when it complements the blend; dominant or poorly integrated pepper/spice and excessive nicotine or strength remain mismatches. Mild through Medium–Full may work when balanced, and prominent flavor matters more than mildness."
prefs["complexity_preference"] = "Prefers prominent, persistent, layered flavor that remains smooth through the smoke. Creamy, toasted/nutty, earthy, naturally sweet, cocoa/coffee and related roasted flavors are strong positive directions. Balanced spice is a positive contributor to complexity; dominant or poorly integrated pepper is a risk."
feedback = prefs.setdefault("explicit_current_feedback", [])
for item in [
"Balanced spice is something the user enjoys; do not describe it as merely tolerated.",
"CAO Cameroon L’Anniversaire was directly rated B: good initial flavors, then flavor softened and some harshness developed.",
"Perdomo Habano Bourbon Barrel-Aged Connecticut Churchill was enjoyed more than CAO Cameroon L’Anniversaire, but was explicitly below A because the flavors were not prominent enough.",
"Flavor prominence and persistence now receive more weight in A predictions, alongside sustained smoothness and complexity.",
"CAO Black and Schizo Maduro suggest a strong preference cluster around creamy/toasted/nutty/earthy flavors, natural sweetness or cocoa/coffee, and integrated spice."
]:
    if item not in feedback: feedback.append(item)
prefs["last_recalibration"] = {
    "basis":"Direct September 2026 smoking feedback plus clarification that balanced spice is actively enjoyed",
    "reason":"Reweighted predictions toward prominent and persistent flavor, sustained smoothness, roasted/nutty/earthy/sweet flavor overlap, complexity, and positively integrated spice. Corrected direct ratings for CAO Cameroon L’Anniversaire and Perdomo Habano Connecticut.",
    "grade_changes":{k:[None,v[0]] for k,v in updates.items()},
    "quantities_changed":False,
    "confirmed_favorites_preserved":True
}
new_json = json.dumps(prefs, ensure_ascii=False, indent=2)
html = html[:m.start(2)] + new_json + html[m.end(2):]

path.write_text(html, encoding="utf-8")
print("Updated", len(updates), "rows")
