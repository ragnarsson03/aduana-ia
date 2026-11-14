// Elimina los bundles hasheados index-*.js / index-*.css de static/assets antes de compilar.
// Motivo: vite.config.ts usa emptyOutDir=false (static/ guarda .gitkeep y otros activos), así que
// cada build dejaba bundles viejos que seguían siendo servidos y auditados por los tests.
import { readdirSync, rmSync } from 'node:fs'
import { join } from 'node:path'

const assetsDir = join(process.cwd(), 'static', 'assets')
const stale = /^index-[A-Za-z0-9_-]+\.(js|css)$/

let removed = 0
try {
  for (const name of readdirSync(assetsDir)) {
    if (stale.test(name)) {
      rmSync(join(assetsDir, name))
      removed += 1
    }
  }
} catch (error) {
  if (error.code !== 'ENOENT') throw error
}
process.stdout.write(`clean_static_bundles: ${removed} bundle(s) antiguo(s) eliminado(s)\n`)
