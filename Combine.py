import re
import os

# === 1) Détection du JS principal ===
try:
    with open("./external_repo/JVChat_Premium.user.js", "r", encoding="utf-8") as f:
        js_content = f.read()
except FileNotFoundError:
    with open("./JVChat_Premium.user.js", "r", encoding="utf-8") as f:
        js_content = f.read()

# === ) Détection du CSS ===
try:
    with open("./external_repo/jvchat-premium.css", "r", encoding="utf-8") as f:
        css_content = f.read()
except FileNotFoundError:
    with open("./jvchat-premium.css", "r", encoding="utf-8") as f:
        css_content = f.read()


# === 3) Corriger Unicode dans le CSS (CSS externe → JS innerHTML-compatible)
def convert_css_unicode_to_js_innerhtml(css_text):
    def replacer(match):
        hex_code = match.group(1)
        if len(hex_code) == 4:
            return f'\\u{hex_code}'  # JS format standard
        else:
            return f'\\u{{{hex_code}}}'  # JS ES6+ format pour >4 ou <4 chiffres
    return re.sub(r'\\([0-9A-Fa-f]{1,6})', replacer, css_text)

css_content = convert_css_unicode_to_js_innerhtml(css_content)
css_content = css_content.replace('`', '\\`')  # Échapper les backticks pour le template literal JS

# === 4) Créer le bloc CSS
css_block = f"let CSS = `<style type=\"text/css\" id=\"jvchat-css\">\n{css_content}\n</style>`;\n"


# === 5) Nettoyer l'entête JS grant et ressources
js_content = re.sub(r"^//\s*@grant.*$\n?", "", js_content, flags=re.MULTILINE)
js_content = re.sub(r"^//\s*@resource.*$\n?", "", js_content, flags=re.MULTILINE)

# === 6) Ajouter `@grant none avant la fin
#js_content = re.sub(r"^//\s*==/UserScript==", "// @grant        unsafeWindow\n// ==/UserScript==", js_content, flags=re.MULTILINE)


# === 7) Corriger URLs entete download
js_content = re.sub(r"^//\s*@downloadURL.*$", "", js_content, flags=re.MULTILINE)
js_content = re.sub(r"^//\s*@updateURL.*$", "", js_content, flags=re.MULTILINE)


# === 8) Supprimer les appels GM et remplacer par le css integre
#js_content = re.sub(r"^.*GM_getResourceText.*$\n?", "", js_content, flags=re.MULTILINE)
#js_content = js_content.replace("GM_addStyle(jvchatCSS);", 'document.head.insertAdjacentHTML("beforeend", CSS);')

# === 8) Supprimer les appels GM et remplacer par le css integre
js_content = re.sub(
    r"(function clearPage\(document\) \{[\s\S]*?)try \{[\s\S]*?GM_getResourceText\('JVCHAT_CSS'\)[\s\S]*?\} catch \(e\) \{[^{}]*\}",
    r'\1document.head.insertAdjacentHTML("beforeend", CSS);',
    js_content,
    flags=re.DOTALL
)

# === 9) Injecter le CSS avant let freshHash
js_content = js_content.replace("let freshHash = undefined;", css_block + "\nlet freshHash = undefined;")

# === 10) Extraire la version
version = re.search(r"^//\s*@version\s+(\d+(?:\.\d+)*)", js_content, flags=re.MULTILINE).group(1)

# === 10) Sauvegarder sous JVChat_PremiumM.js à la racine
with open("JVChat_PremiumM.js", "w", encoding="utf-8") as f:
    f.write(js_content)
with open(f"/Old_Merge/JVChat_PremiumM.v{version}.js", "w", encoding="utf-8") as f:
    f.write(js_content)

