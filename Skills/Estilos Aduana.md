---
name: sovereign-precision-react-ux
description: Sistema de diseño UX/UI de alta precisión, gobernanza institucional y GovTech ("Sovereign Precision") optimizado para React (JSX/TSX) y Tailwind CSS. Garantiza interfaces totalmente responsivas (Mobile, Tablet, Desktop), tipografía dual (Inter + JetBrains Mono), paleta cromática sobria y componentes modulares.
---

# Skill: Sovereign Precision UX/UI (React + Tailwind CSS)

## 1. Principios de Diseño y Arquitectura React
- **Estética:** Minimalismo ejecutivo, autoridad, orden estricto, ausencia de decoraciones innecesarias, bordes tipo "hairline" y amplio espaciado interno.
- **Arquitectura de Componentes:** Generar componentes funcionales de React limpios, modulares y tipados (o listos para JSX/TSX), utilizando hooks estándar (`useState`, `useEffect`) para estados interactivos (menús móviles, modales, filtros, modo oscuro).
- **Iconografía:** Utilizar `lucide-react` (preferido en React) o iconos SVG limpios con trazo fino (`strokeWidth={1.75}`).

## 2. Sistema Responsivo Obligatorio (Mobile-First)
Toda vista generada debe adaptarse fluidamente a cualquier tamaño de pantalla siguiendo estas reglas de grilla y navegación:
- **Teléfonos (`< 640px` / default):**
  - Layout de 1 columna (`grid-cols-1`), márgenes exteriores compactos (`px-4` o `px-margin-mobile`), espaciado vertical `gap-4`.
  - Navegación colapsada en un menú hamburguesa desplegable o drawer móvil (`md:hidden`).
  - Tablas o listas densas deben envolverse en contenedores con scroll horizontal (`overflow-x-auto`) o transformarse en tarjetas apiladas (Dossier Cards).
  - Textos de titulares adaptados (`text-display-lg-mobile` / `text-2xl`).
- **Tabletas (`768px - 1024px` / `md:`):**
  - Grillas de 2 columnas (`md:grid-cols-2`) para métricas y tarjetas secundarias.
  - Márgenes intermedios (`md:px-7`), visualización completa de la barra de navegación superior (`hidden md:flex`).
- **Computadoras y Monitores Grandes (`1280px+` / `lg:` y `xl:`):**
  - Grilla fluida de 12 columnas (`lg:grid-cols-12`), márgenes amplios (`lg:px-margin` / `40px`), contenedores máximos centrados (`max-w-[1600px] mx-auto`).
  - Vistas divididas asimétricas (ej. `lg:col-span-6` o `lg:col-span-7` + `lg:col-span-5`) para paneles de auditoría y telemetría simultánea.

## 3. Paleta de Referencia (Tokens Tailwind)
- **Superficies:** `bg-surface` (`#fbf8ff`), tarjetas elevadas `bg-surface-container-lowest` (`#ffffff`), contenedores secundarios `bg-surface-container-low` (`#f4f2fd`).
- **Primario (Acciones):** `bg-primary` (`#3525cd`), hover `hover:bg-primary-container` (`#4f46e5`), texto `text-on-primary` (`#ffffff`).
- **Secundario (Verificado / Éxito):** `text-secondary` (`#006c49`), fondos suaves `bg-secondary-container/40`.
- **Terciario y Errores (PII / Alertas):** `bg-tertiary-fixed` (`#ffddb8`) con `text-on-tertiary-fixed-variant` (`#653e00`); errores críticos con `bg-error-container` y `text-error`.
- **Bordes:** Líneas finas `border border-outline-variant/40`.

## 4. Tipografía Dual Obligatoria
- **UI General:** Familia `Inter` (`font-sans`, `text-headline-sm`, `text-body-md`, `text-label-md`).
- **Datos Técnicos y Tabulares:** Familia `JetBrains Mono` (`font-mono`, `text-code-md`, `text-code-sm`) obligatoria para hashes SHA-256, IDs, cédulas ocultas, latencias, porcentajes de paridad y marcas de tiempo.

## 5. Instrucciones de Generación de Código
1. Entregar código React autocontenido y funcional, listo para copiar y pegar.
2. Incluir siempre estados interactivos reales (ej. toggle de menú móvil, tabs funcionales o simulación de estados).
3. Asegurar que ningún elemento desborde horizontalmente en pantallas de `360px` de ancho (usar `truncate`, `break-all` para hashes largos, y `flex-wrap` en tiras de etiquetas).
4. Incluir clases `dark:` compatibles si se solicita soporte de tema oscuro.