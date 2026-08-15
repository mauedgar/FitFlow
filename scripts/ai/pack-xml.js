const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Función para interactuar con la terminal si faltan datos
const askQuestion = (query) => {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => rl.question(query, (ans) => { rl.close(); resolve(ans.trim()); }));
};

async function main() {
  // 1. Obtener argumentos (ej: npm run pack:xml src/modules/auth FF-LOCAL-123)
  let targetPath = process.argv[2];
  let taskName = process.argv[3];

  // 2. Validación interactiva si faltan parámetros
  if (!targetPath) {
    targetPath = await askQuestion('📁 ¿Qué carpeta o archivo quieres empaquetar? (ej: src/components/button): ');
  }
  if (!taskName) {
    taskName = await askQuestion('📝 Ingresa el código de la tarea (ej: FF-LOCAL-XXX o FF-TOOL-XXX): ');
  }

  // Validar formato de la tarea (FF-LOCAL-XXX o FF-TOOL-XXX) de manera flexible (insensible a mayúsculas)
  const taskRegex = /^ff-(local|tool)-.+$/i;
  if (!taskRegex.test(taskName)) {
    console.warn('⚠️  Nota: El formato recomendado para la tarea es FF-LOCAL-XXX o FF-TOOL-XXX.');
  }

  // Resolver la ruta absoluta para validar existencia y extraer el nombre del módulo
  const absolutePath = path.resolve(targetPath);
  if (!fs.existsSync(absolutePath)) {
    console.error(`❌ Error: La ruta "${targetPath}" no existe.`);
    process.exit(1);
  }

  // 3. Extraer el nombre del módulo o carpeta compactada
  // Si empaquetas "src/features/auth", el nombre será "auth"
  // Si empaquetas la raíz ".", usará el nombre de la carpeta del proyecto
  let moduleName = path.basename(absolutePath);
  if (moduleName === '.' || moduleName === '') {
    moduleName = path.basename(process.cwd());
  }

  // 4. Definir y crear la estructura de rutas requerida
  const cleanTaskName = taskName.toUpperCase(); // Normalizar a mayúsculas para mantener orden
  const outputDir = path.join('.context', 'repomix', cleanTaskName);

  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // 5. Crear el nombre del archivo XML con un Timestamp preciso
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const outputFileName = `${moduleName}-${timestamp}.xml`;
  const outputFile = path.join(outputDir, outputFileName);

  console.log(`\n📦 [${cleanTaskName}] Empaquetando módulo "${moduleName}" en formato XML...`);

  try {
    // 6. Ejecutar Repomix indicando el path específico y el destino ordenado
    execSync(`npx repomix "${targetPath}" --style xml --output "${outputFile}"`, { stdio: 'inherit' });
    console.log(`\n✅ ¡Éxito! Contexto guardado en:\n👉 ${outputFile}\n`);
  } catch (error) {
    console.error('\n❌ Hubo un error al ejecutar Repomix.');
  }
}

main();