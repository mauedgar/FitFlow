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
    // 1. Obtener argumentos iniciales si existen
    let taskName = process.argv[2];
    let scope = process.argv[3]; 

    // 2. Validación interactiva de la tarea
    if (!taskName) {
        taskName = await askQuestion('📝 Ingresa el código de la tarea (ej: FF-LOCAL-XXX o FF-TOOL-XXX): ');
    }

    const taskRegex = /^ff-(local|tool)-.+$/i;
    if (!taskRegex.test(taskName)) {
        console.warn('⚠️ Nota: El formato recomendado para la tarea es FF-LOCAL-XXX o FF-TOOL-XXX.');
    }

    const cleanTaskName = taskName.toUpperCase();
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);

    // ==========================================
    // FASE 1: GENERACIÓN DE REPOMAP (ESTRUCTURA)
    // ==========================================
    
    const validScopes = ['frontend', 'backend', 'both'];
    if (!scope || !validScopes.includes(scope.toLowerCase())) {
        console.log('\n🔍 ¿De qué entorno necesitas generar primero el mapa de arquitectura (Repomap)?');
        console.log('1. Frontend (Carpeta ./frontend)');
        console.log('2. Backend  (Carpeta ./backend)');
        console.log('3. Ambos    (Mapear ambos por separado)');
        
        const option = await askQuestion('Selecciona una opción (1, 2 o 3): ');
        if (option === '1') scope = 'frontend';
        else if (option === '2') scope = 'backend';
        else if (option === '3') scope = 'both';
        else {
            console.error('❌ Opción no válida. Abortando.');
            process.exit(1);
        }
    }

    scope = scope.toLowerCase();

    const mapOutputDir = path.join('.context', 'repomap-temp', cleanTaskName);
    if (!fs.existsSync(mapOutputDir)) {
        fs.mkdirSync(mapOutputDir, { recursive: true });
    }

    const mapTargets = [];
    if (scope === 'frontend' || scope === 'both') mapTargets.push({ name: 'frontend', path: path.resolve('frontend') });
    if (scope === 'backend' || scope === 'both') mapTargets.push({ name: 'backend', path: path.resolve('backend') });

    for (const target of mapTargets) {
        if (!fs.existsSync(target.path)) {
            console.error(`❌ Error: La carpeta "${target.path}" no existe.`);
            continue;
        }

        const mapOutputFile = path.join(mapOutputDir, `${target.name}-${timestamp}.txt`);
        console.log(`\n🗺️ [${cleanTaskName}] Generando mapa estructural para ${target.name.toUpperCase()}...`);
        
        try {
            execSync(`npx repomap "${target.path}" --output "${mapOutputFile}"`, { stdio: 'inherit' });
            console.log(`✅ Mapa guardado en: ${mapOutputFile}`);
        } catch (error) {
            console.error(`❌ Error al ejecutar repomap para ${target.name}.`);
        }
    }

    // ==========================================
    // FASE 2: EMPAQUETADO DE CÓDIGO FUENTE (REPOMIX)
    // ==========================================
    
    console.log('\n--------------------------------------------------');
    console.log('📦 Preparando el empaquetado del código fuente completo.');
    console.log('Identifica en tu mapa qué módulos o directorios específicos intervienen.');
    console.log('--------------------------------------------------\n');

    console.log('¿Cómo prefieres empaquetar tus fuentes?');
    console.log('1. Archivos individuales (Cada ruta genera su propio XML)');
    console.log('2. Archivo combinado    (Múltiples rutas dentro de un único XML)');
    
    const packingMode = await askQuestion('Selecciona el modo (1 o 2): ');
    if (packingMode !== '1' && packingMode !== '2') {
        console.error('❌ Opción no válida. Abortando.');
        process.exit(1);
    }

    const mixOutputDir = path.join('.context', 'repomix', cleanTaskName);
    if (!fs.existsSync(mixOutputDir)) {
        fs.mkdirSync(mixOutputDir, { recursive: true });
    }

    const ignoreFlags = '--ignore "**/node_modules/**,**/uvicorn-venv_backend/**"';

    if (packingMode === '1') {
        // --- MODO 1: ARCHIVOS SEPARADOS ---
        let dynamicTimestampCounter = 1;
        let addingMore = true;

        while (addingMore) {
            const targetPath = await askQuestion('📁 Especifica la ruta de la carpeta o archivo a empaquetar: ');

            if (!targetPath) {
                console.log('⚠️ No ingresaste una ruta.');
            } else {
                const absoluteTargetPath = path.resolve(targetPath);
                if (!fs.existsSync(absoluteTargetPath)) {
                    console.error(`❌ Error: La ruta ingresada "${targetPath}" no existe.`);
                } else {
                    let moduleName = path.basename(absoluteTargetPath);
                    if (moduleName === '.' || moduleName === '') moduleName = path.basename(process.cwd());

                    const mixOutputFile = path.join(mixOutputDir, `${moduleName}-${timestamp}-${dynamicTimestampCounter}.xml`);
                    console.log(`\n📦 [${cleanTaskName}] Empaquetando "${moduleName}" individualmente...`);

                    try {
                        execSync(`npx repomix "${targetPath}" --style xml --output "${mixOutputFile}" ${ignoreFlags}`, { stdio: 'inherit' });
                        console.log(`\n✅ ¡Éxito! Guardado en:\n👉 ${mixOutputFile}\n`);
                        dynamicTimestampCounter++;
                    } catch (error) {
                        console.error('\n❌ Hubo un error al ejecutar Repomix.');
                    }
                }
            }

            const answer = await askQuestion('➕ ¿Deseas empaquetar otro directorio o archivo por separado? (s/n): ');
            if (answer.toLowerCase() !== 's' && answer.toLowerCase() !== 'si' && answer.toLowerCase() !== 'y') {
                addingMore = false;
            }
            console.log('');
        }
    } else {
        // --- MODO 2: ARCHIVO COMBINADO ---
        const gatheredPaths = [];
        let addingMore = true;

        console.log('\n📥 Introduce las rutas una por una. Presiona Enter sin escribir nada cuando termines de agregar.');

        while (addingMore) {
            const targetPath = await askQuestion(`📁 Ingresa ruta #${gatheredPaths.length + 1}: `);
            
            if (!targetPath) {
                if (gatheredPaths.length === 0) {
                    console.log('⚠️ No has añadido ninguna ruta todavía.');
                    const quit = await askQuestion('¿Deseas salir del script? (s/n): ');
                    if (quit.toLowerCase() === 's' || quit.toLowerCase() === 'si' || quit.toLowerCase() === 'y') {
                        process.exit(0);
                    }
                } else {
                    addingMore = false;
                }
            } else {
                const absoluteTargetPath = path.resolve(targetPath);
                if (!fs.existsSync(absoluteTargetPath)) {
                    console.error(`❌ Error: La ruta "${targetPath}" no existe en el disco. No se añadirá.`);
                } else {
                    gatheredPaths.push(targetPath);
                    console.log(`✅ Añadida: ${targetPath} (Total acumulado: ${gatheredPaths.length})`);
                }
            }
        }

        if (gatheredPaths.length > 0) {
            // El nombre del archivo reflejará el primer módulo de la lista seguido de un indicador "combined"
            let baseModuleName = path.basename(path.resolve(gatheredPaths[0]));
            if (baseModuleName === '.' || baseModuleName === '') baseModuleName = path.basename(process.cwd());

            const mixOutputFile = path.join(mixOutputDir, `${baseModuleName}-combined-${timestamp}.xml`);
            
            // Unimos todas las rutas separadas por espacios para pasárselas a repomix juntas
            // ej: npx repomix "ruta1" "ruta2" "ruta3" ...
            const formattedPathsString = gatheredPaths.map(p => `"${p}"`).join(' ');

            console.log(`\n📦 [${cleanTaskName}] Combinando y empaquetando ${gatheredPaths.length} rutas en un solo archivo XML...`);

            try {
                execSync(`npx repomix ${formattedPathsString} --style xml --output "${mixOutputFile}" ${ignoreFlags}`, { stdio: 'inherit' });
                console.log(`\n✅ ¡Éxito absoluto! Contexto combinado guardado en:\n👉 ${mixOutputFile}\n`);
            } catch (error) {
                console.error('\n❌ Hubo un error al ejecutar el empaquetado combinado de Repomix.');
            }
        }
    }

    console.log('🏁 Proceso finalizado. Todos los contextos seleccionados han sido estructurados.');
}

main();
