"""
Helper para PWA — JAM Soft
Usa st.components.v1.html para executar JavaScript (o st.markdown não executa).
"""
import streamlit as st
import streamlit.components.v1 as components


# ============================================================
# MANIFEST (base64 do static/manifest.json)
# ============================================================
_MANIFEST_B64 = "77u/ewogICJuYW1lIjogIkpBTSBTb2Z0IOKAlCBQbGF0YWZvcm1hIEZhcm3DoWNpYXMiLAogICJzaG9ydF9uYW1lIjogIkpBTSBTb2Z0IiwKICAiZGVzY3JpcHRpb24iOiAiTW9uaXRvcml6YcOnw6NvIGRlIGZhcm3DoWNpYXMgZW0gQW5nb2xhIiwKICAic3RhcnRfdXJsIjogIi8iLAogICJkaXNwbGF5IjogInN0YW5kYWxvbmUiLAogICJvcmllbnRhdGlvbiI6ICJwb3J0cmFpdCIsCiAgImJhY2tncm91bmRfY29sb3IiOiAiI2ZmZmZmZiIsCiAgInRoZW1lX2NvbG9yIjogIiMwZTdjNjYiLAogICJsYW5nIjogInB0LUFPIiwKICAiaWNvbnMiOiBbCiAgICB7CiAgICAgICJzcmMiOiAiL3N0YXRpYy9pY29uLTE5Mi5wbmciLAogICAgICAic2l6ZXMiOiAiMTkyeDE5MiIsCiAgICAgICJ0eXBlIjogImltYWdlL3BuZyIsCiAgICAgICJwdXJwb3NlIjogImFueSBtYXNrYWJsZSIKICAgIH0sCiAgICB7CiAgICAgICJzcmMiOiAiL3N0YXRpYy9pY29uLTUxMi5wbmciLAogICAgICAic2l6ZXMiOiAiNTEyeDUxMiIsCiAgICAgICJ0eXBlIjogImltYWdlL3BuZyIsCiAgICAgICJwdXJwb3NlIjogImFueSBtYXNrYWJsZSIKICAgIH0KICBdCn0NCg=="

# ============================================================
# ICON 192x192 (base64 do static/icon-192.png)
# ============================================================
_ICON192_B64 = "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"

# ============================================================
# ICON 512x512 (base64 do static/icon-512.png)
# ============================================================
_ICON512_B64 = "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"

# ============================================================
# SERVICE WORKER (base64 do static/sw.js)
# ============================================================
_SW_B64 = "Ly8gU2VydmljZSBXb3JrZXIg4oCUIEpBTSBTb2Z0IFBXQQ0KY29uc3QgQ0FDSEVfTkFNRSA9ICJqYW1zb2Z0LXYxIjsNCmNvbnN0IFVSTFNfVE9fQ0FDSEUgPSBbDQogICIvIiwNCiAgIi9zdGF0aWMvbWFuaWZlc3QuanNvbiINCl07DQoNCnNlbGYuYWRkRXZlbnRMaXN0ZW5lcigiaW5zdGFsbCIsIChldmVudCkgPT4gew0KICBldmVudC53YWl0VW50aWwoDQogICAgY2FjaGVzLm9wZW4oQ0FDSEVfTkFNRSkudGhlbigoY2FjaGUpID0+IGNhY2hlLmFkZEFsbChVUkxTX1RPX0NBQ0hFKSkNCiAgKTsNCiAgc2VsZi5za2lwV2FpdGluZygpOw0KfSk7DQoNCnNlbGYuYWRkRXZlbnRMaXN0ZW5lcigiYWN0aXZhdGUiLCAoZXZlbnQpID0+IHsNCiAgZXZlbnQud2FpdFVudGlsKA0KICAgIGNhY2hlcy5rZXlzKCkudGhlbigoa2V5cykgPT4NCiAgICAgIFByb21pc2UuYWxsKA0KICAgICAgICBrZXlzLmZpbHRlcigoaykgPT4gayAhPT0gQ0FDSEVfTkFNRSkubWFwKChrKSA9PiBjYWNoZXMuZGVsZXRlKGspKQ0KICAgICAgKQ0KICAgICkNCiAgKTsNCiAgc2VsZi5jbGllbnRzLmNsYWltKCk7DQp9KTsNCg0Kc2VsZi5hZGRFdmVudExpc3RlbmVyKCJmZXRjaCIsIChldmVudCkgPT4gew0KICBpZiAoZXZlbnQucmVxdWVzdC5tZXRob2QgIT09ICJHRVQiKSByZXR1cm47DQogIA0KICBldmVudC5yZXNwb25kV2l0aCgNCiAgICBmZXRjaChldmVudC5yZXF1ZXN0KQ0KICAgICAgLnRoZW4oKHJlc3BvbnNlKSA9PiB7DQogICAgICAgIGNvbnN0IHJlc3BDbG9uZSA9IHJlc3BvbnNlLmNsb25lKCk7DQogICAgICAgIGNhY2hlcy5vcGVuKENBQ0hFX05BTUUpLnRoZW4oKGNhY2hlKSA9PiB7DQogICAgICAgICAgY2FjaGUucHV0KGV2ZW50LnJlcXVlc3QsIHJlc3BDbG9uZSk7DQogICAgICAgIH0pOw0KICAgICAgICByZXR1cm4gcmVzcG9uc2U7DQogICAgICB9KQ0KICAgICAgLmNhdGNoKCgpID0+IGNhY2hlcy5tYXRjaChldmVudC5yZXF1ZXN0KSkNCiAgKTsNCn0pOw=="


def inject_pwa():
    """Injeta manifest + service worker via st.components.v1.html (executa JS)."""
    html = f"""
    <script>
    (function() {{
        try {{
            const parentDoc = window.parent.document;

            // 1. Manifest dinâmico via Blob
            const manifestB64 = "{_MANIFEST_B64}";
            const manifestBytes = Uint8Array.from(atob(manifestB64), c => c.charCodeAt(0));
            const manifestText = new TextDecoder("utf-8").decode(manifestBytes);
            const manifest = JSON.parse(manifestText);
            manifest.icons = [
                {{
                    src: "data:image/png;base64,{_ICON192_B64}",
                    sizes: "192x192",
                    type: "image/png",
                    purpose: "any maskable"
                }},
                {{
                    src: "data:image/png;base64,{_ICON512_B64}",
                    sizes: "512x512",
                    type: "image/png",
                    purpose: "any maskable"
                }}
            ];

            const manifestBlob = new Blob(
                [JSON.stringify(manifest)],
                {{type: "application/manifest+json"}}
            );
            const manifestURL = URL.createObjectURL(manifestBlob);

            let link = parentDoc.querySelector('link[rel="manifest"]');
            if (!link) {{
                link = parentDoc.createElement("link");
                link.rel = "manifest";
                parentDoc.head.appendChild(link);
            }}
            link.href = manifestURL;
            console.log("[PWA] Manifest OK:", manifestURL);

            // 2. Apple touch icon
            let apple = parentDoc.querySelector('link[rel="apple-touch-icon"]');
            if (!apple) {{
                apple = parentDoc.createElement("link");
                apple.rel = "apple-touch-icon";
                parentDoc.head.appendChild(apple);
            }}
            apple.href = "data:image/png;base64,{_ICON192_B64}";

            // 3. Favicon
            let favicon = parentDoc.querySelector('link[rel="icon"]');
            if (!favicon) {{
                favicon = parentDoc.createElement("link");
                favicon.rel = "icon";
                favicon.type = "image/png";
                parentDoc.head.appendChild(favicon);
            }}
            favicon.href = "data:image/png;base64,{_ICON192_B64}";

            // 4. Theme color
            let theme = parentDoc.querySelector('meta[name="theme-color"]');
            if (!theme) {{
                theme = parentDoc.createElement("meta");
                theme.name = "theme-color";
                theme.content = "#7c3aed";
                parentDoc.head.appendChild(theme);
            }}

            // 5. Service Worker via Blob (só em HTTPS)
            if ("serviceWorker" in navigator && location.protocol === "https:") {{
                const swB64 = "{_SW_B64}";
                const swBytes = Uint8Array.from(atob(swB64), c => c.charCodeAt(0));
                const swText = new TextDecoder("utf-8").decode(swBytes);
                const swBlob = new Blob([swText], {{type: "application/javascript"}});
                const swURL = URL.createObjectURL(swBlob);

                navigator.serviceWorker.register(swURL)
                    .then(function(reg) {{
                        console.log("[PWA] SW registado:", reg.scope);
                    }})
                    .catch(function(err) {{
                        console.warn("[PWA] SW erro:", err.message);
                    }});
            }} else {{
                console.warn("[PWA] SW ignorado (precisa HTTPS):", location.protocol);
            }}

        }} catch (e) {{
            console.error("[PWA] Erro geral:", e);
        }}
    }})();
    </script>
    """

    components.html(html, height=0, width=0)


def mobile_css():
    """CSS para melhorar visualização no telemóvel."""
    st.markdown(
        """
        <style>
        @media (max-width: 768px) {
            [data-testid="column"] {
                min-width: 100% !important;
                flex: 1 1 100% !important;
            }

            .stButton > button {
                width: 100% !important;
                padding: 12px !important;
                font-size: 16px !important;
            }

            [data-testid="stMetricValue"] {
                font-size: 22px !important;
            }

            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}

            .block-container {
                padding-top: 2rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
        }

        footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )