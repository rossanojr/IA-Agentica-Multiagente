# IA-Agentica-Multiagente
Proyecto Final IBM Ingenieria IA - Modelo IA Agentica Multiagente. (Coursera)
Adaptado para usar Qwen

## Configuracion del proyecto. Recomendacion para el entorno

### Usuario Git asociado al proyecto

Para definir la identidad de Git solamente para este repositorio, se deben ejecutar estos comandos desde su carpeta:

```bash
git config --local user.name "Tu nombre"
git config --local user.email "tu-correo@example.com"
```

Comprobar la configuracion con:

```bash
git config --local --list
```

Estos valores se guardan en `.git/config` y no modifican la configuracion global de Git del equipo.

### Token de Hugging Face

Crear el token desde la configuracion de acceso de Hugging Face con estas opciones:

- Tipo de token: `Fine-grained`.
- Permiso: habilitar el acceso de inferencia (`Inference` o `Make calls to Inference Providers`, segun la interfaz).

Usar el token generado en los siguientes comandos como `HF_TOKEN`.

### Token en Linux

Definir el token como variable de entorno para la sesion actual:

```bash
export HF_TOKEN="tu-token"
```

Para dejarlo disponible en nuevas sesiones de Bash, agregar la misma linea a `~/.bashrc` y recargar la configuracion:

```bash
source ~/.bashrc
```

### Token en Windows

En PowerShell, para la sesion actual usar:

```powershell
$env:HF_TOKEN = "tu-token"
```

Para guardarlo en las nuevas sesiones del usuario de Windows:

```powershell
[Environment]::SetEnvironmentVariable("HF_TOKEN", "tu-token", "User")
```

En `cmd.exe`, usa `set` para la sesion actual o `setx` para las nuevas sesiones:

```bat
set HF_TOKEN=tu-token
setx HF_TOKEN "tu-token"
```

Verificar que la variable este definida sin mostrar el token completo:

```bash
echo "${HF_TOKEN:0:4}..."
```

En PowerShell:

```powershell
$env:HF_TOKEN.Substring(0, 4) + "..."
```

¡¡¡RECOMENDACION!!!
No incluir el token en el codigo, en archivos versionados ni en la URL del remoto.

### Preparacion local y base vectorial con ChromaDB

Instalar las dependencias del proyecto:

```powershell
pip install -r requirements.txt
```

Antes de ejecutar cualquier otro notebook, ejecutar completo
`00_configurar_proyecto_y_base_vectorial.ipynb` desde la raiz del repositorio.
El notebook crea las carpetas `data`, `recipe_images` y `datadb` directamente
en esa raiz. Estas carpetas contienen recursos y datos generados localmente,
por lo que estan excluidas de Git y deben crearse de nuevo en cada entorno.

El material original del curso/proyecto esta incluido en el repositorio y coloca en la raiz del
proyecto (en `data/`), los archivos de entrada:

- `structured_restaurant_data.json`
- `augmented_food_recipe.json`
- `synthetic-recipe-images.zip` (opcional; el notebook lo descarga si falta)
- `structured-restaurant-data.json`
- `augmented-user-review.json`
- `California-Culinary-Map.txt`

El notebook prepara los documentos, genera los embeddings y persiste las
colecciones `restaurant_articles` y `food_images` en `datadb`. El archivo 
data/synthetic-recipe-images.zipLas y las carpetas `recipe_images` y `datadb`
estan excluidas para no ser subidas al repositorio.
