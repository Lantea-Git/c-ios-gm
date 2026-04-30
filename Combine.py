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
css_content = css_content.replace('`', '')  # Virer backticks pour le template literal JS

# === 4) Créer le bloc CSS
css_block = f"let CSS = `<style type=\"text/css\" id=\"jvchat-css\">\n{css_content}\n</style>`;\n"


# === 5) Nettoyer l'entête JS grant et ressources
js_content = re.sub(r"^//\s*@grant.*$\n?", "", js_content, flags=re.MULTILINE)
js_content = re.sub(r"^//\s*@resource.*$\n?", "", js_content, flags=re.MULTILINE)

# === 6) Ajouter `@grant none avant la fin
#js_content = re.sub(r"^//\s*==/UserScript==", "// @grant        unsafeWindow\n// ==/UserScript==", js_content, flags=re.MULTILINE)


# === 7) Enlever URLs entete download
js_content = re.sub(r"^//\s*@downloadURL.*$\n?", "", js_content, flags=re.MULTILINE)
js_content = re.sub(r"^//\s*@updateURL.*$\n?", "", js_content, flags=re.MULTILINE)

# === 7B) BOUNDARY TO FORMDATA GreasyMonkey
old = """    let fs_custom_input = Array.from(freshForm.elements).find(e => /^fs_[a-f0-9]{40}$/i.test(e.name));
    if (fs_custom_input && !formData.has(fs_custom_input.name)) {
        formData.set(fs_custom_input.name, fs_custom_input.value);
    }
    if (!formData.has("ajax_hash")) {
        let ajax_hash = freshForm.querySelector('input[name="ajax_hash"]')?.value || freshHash;
        formData.set("ajax_hash", ajax_hash);
    }

    const boundary = "----geckoformboundary" + Math.random().toString(16).slice(2);
    let body = "";
    for (let [key, value] of formData.entries()) {
        body += `--${boundary}\\r\\nContent-Disposition: form-data; name="${key}"\\r\\n\\r\\n${value}\\r\\n`;
    }
    body += `--${boundary}--\\r\\n`;"""
js_content = js_content.replace(old, '    formData.set("ajax_hash", forumPayload.ajaxToken);')

old2 = """                referrer: document.URL,
                body: body,
                mode: "cors\""""
js_content = js_content.replace('                    "Content-Type": `multipart/form-data; boundary=${boundary}`,\n', "")

js_content = js_content.replace(old2, """                referrer: document.URL,
                body: formData,
                mode: "cors\"""")

# === 8) STYLE Supprimer LES APPELS GM et remplacer par le CSS INTEGRE
old = """
    try {
        const jvchatCSS = GM_getResourceText('JVCHAT_CSS');
        if (jvchatCSS && typeof jvchatCSS === 'string' && jvchatCSS.length > 0) {
            GM_addStyle(jvchatCSS);
        } else {
            console.warn('[JVChat] @resource JVCHAT_CSS empty or unavailable.');
        }
    } catch (e) {
        console.warn('[JVChat] GM_getResourceText failed:', e);
    }
"""
js_content = js_content.replace(old, '\n    document.head.insertAdjacentHTML("beforeend", CSS);\n')


# === 9) Injecter le CSS avant let freshHash
js_content = js_content.replace("let freshHash = undefined;", css_block + "\nlet freshHash = undefined;")

# === 10) Extraire la version
version = re.search(r"^//\s*@version\s+(\d+(?:\.\d+)*)", js_content, flags=re.MULTILINE).group(1)

# === 10) Sauvegarder sous JVChat_PremiumM.js à la racine
with open("JVChat_PremiumM.js", "w", encoding="utf-8") as f:
    f.write(js_content)
with open(f"./Old_Merge/JVChat_PremiumM.v{version}.js", "w", encoding="utf-8") as f:
    f.write(js_content)

