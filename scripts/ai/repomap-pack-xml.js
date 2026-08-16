const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Función para interactuar con la terminal
const askQuestion = (query) => {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout
    });
    return new Promise((resolve) => rl.question(query, (ans) => {
        rl.close();
        resolve(ans.trim());
    }));
};

async function main() {
    // 1. Obtener argumentos (ej: node scripts/ai/repomap-pack-xml.js FF-LOCAL-123 .ai docs)
    let taskName = process.argv[2];
    // rutas incrustadas desde argv[3+]
    const rawPathsArgs = process.argv.slice(3);
    let embeddedPaths = [];
    if (rawPathsArgs.length > 0) {
        for (const a of rawPathsArgs) {
            if (!a) continue;
            const parts = a.split(/[;,]+/).map(p => p.trim()).filter(Boolean);
            embeddedPaths.push(...parts);
        }
    }

    // 2. Validación interactiva de la tarea si falta
    if (!taskName) {
        taskName = await askQuestion('📝 Ingresa el código de la tarea (ej: FF-LOCAL-XXX o FF-TOOL-XXX): ');
    }

    // Validar formato de la tarea (solo advertencia)
    const taskRegex = /^ff-(local|tool|ai)-.+$/i;
    if (!taskRegex.test(taskName)) {
        console.warn('⚠️ Nota: El formato recomendado para la tarea es FF-LOCAL-XXX, FF-TOOL-XXX o FF-AI-XXX.');
    }

    const cleanTaskName = taskName.toUpperCase();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);

    // 3. Preparar directorio de salida .context/repomap-temp/<TASK>
    const outputDir = path.join('.context', 'repomap-temp', cleanTaskName);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    // 4. Determinar rutas a mapear: si se proveen incrustadas, úsalas; si no, pedir scope y mapear frontend/backend/both
    let pathsToMap = [];
    if (embeddedPaths && embeddedPaths.length > 0) {
        // Normalizar rutas relativas y comprobar existencia antes de mapear
        for (const p of embeddedPaths) {
            const abs = path.resolve(p);
            if (!fs.existsSync(abs)) {
                console.warn(`⚠️ Advertencia: la ruta incrustada "${p}" no existe en el disco (resuelta a ${abs}). Se omitirá.`);
                continue;
            }
            pathsToMap.push({ name: path.basename(abs) || p, path: abs });
        }
    } else {
        // Pedir scope interactivo (frontend/backend/both)
        const validScopes = ['frontend', 'backend', 'both'];
        let scope = await askQuestion('\n🔍 ¿Qué parte del proyecto deseas mapear? (frontend/backend/both): ');
        if (!scope || !validScopes.includes(scope.toLowerCase())) {
            console.log('Opción no válida. Usando "both" por defecto.');
            scope = 'both';
        }
        scope = scope.toLowerCase();
        if (scope === 'frontend' || scope === 'both') {
            const abs = path.resolve('frontend');
            if (fs.existsSync(abs)) pathsToMap.push({ name: 'frontend', path: abs });
            else console.warn(`⚠️ Carpeta frontend no encontrada en ${abs}, se omitirá.`);
        }
        if (scope === 'backend' || scope === 'both') {
            const abs = path.resolve('backend');
            if (fs.existsSync(abs)) pathsToMap.push({ name: 'backend', path: abs });
            else console.warn(`⚠️ Carpeta backend no encontrada en ${abs}, se omitirá.`);
        }
    }

    if (pathsToMap.length === 0) {
        console.error('❌ No se encontraron rutas válidas para mapear. Abortando.');
        process.exit(1);
    }

    // 5. Ejecutar repomap para cada ruta y recopilar salidas. Se guardarán temporalmente y luego se combinarán en un XML único.
    const tempFiles = [];
    for (const target of pathsToMap) {
        const tmpTxt = path.join(outputDir, `${target.name}-${timestamp}.txt`);
        console.log(`\n🗺️ [${cleanTaskName}] Ejecutando repomap en: ${target.path}`);
        try {
            // Ejecutar repomap y volcar a archivo temporal.
            execSync(`npx repomap "${target.path}" --output "${tmpTxt}"`, { stdio: 'inherit' });
            tempFiles.push({ name: target.name, path: tmpTxt });
            console.log(`✅ Repomap temporal guardado en: ${tmpTxt}`);
        } catch (err) {
            console.error(`❌ Error ejecutando repomap en ${target.path}: ${err.message || err}`);
        }
    }

    if (tempFiles.length === 0) {
        console.error('❌ Ningún repomap se generó correctamente. Abortando.');
        process.exit(1);
    }

    // 6. Construir XML combinado con los outputs embebidos en CDATA por target
    const outputXmlFile = path.join(outputDir, `${cleanTaskName}-${timestamp}.xml`);
    let xmlParts = [];
    xmlParts.push('<?xml version="1.0" encoding="UTF-8"?>');
    xmlParts.push(`<repomap task="${cleanTaskName}" generated="${timestamp}">`);

    for (const tf of tempFiles) {
        let content = '';
        try {
            content = fs.readFileSync(tf.path, { encoding: 'utf8' });
        } catch (e) {
            content = `Error leyendo archivo temporal: ${e.message}`;
        }
        xmlParts.push(`  <target name="${tf.name}">`);
        xmlParts.push('    <![CDATA[');
        xmlParts.push(content);
        xmlParts.push('    ]]>');
        xmlParts.push('  </target>');
    }

    xmlParts.push('</repomap>');

    try {
        fs.writeFileSync(outputXmlFile, xmlParts.join('\n'));
        console.log(`\n✅ Repomap combinado guardado en XML:\n👉 ${outputXmlFile}\n`);
    } catch (e) {
        console.error(`\n❌ Error escribiendo XML combinado: ${e.message}`);
        process.exit(1);
    }

    // 7. Limpiar archivos temporales (.txt)
    for (const tf of tempFiles) {
        try { fs.unlinkSync(tf.path); } catch (e) { /* no crítico */ }
    }
}

main();
