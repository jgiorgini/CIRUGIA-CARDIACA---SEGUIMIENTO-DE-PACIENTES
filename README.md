# RCV – Recuperación Cardiovascular

Versión piloto: `RCV-V1.0-PILOT-002`

## Objetivo
Piloto funcional con datos ficticios o anonimizados. No utilizar con pacientes reales hasta contar con infraestructura, seguridad y aprobación institucional.

## Ejecución local
Sin `DATABASE_URL`, la aplicación utiliza SQLite en `data/rcv.db`.

```bash
python server.py
```

## Despliegue cloud
La aplicación acepta `DATABASE_URL` y utiliza PostgreSQL automáticamente.
Incluye `render.yaml` para desplegar un Web Service y una base PostgreSQL desde este repositorio.

En Render:
1. Crear un Blueprint desde este repositorio.
2. Render crea `rcv-pilot` y `rcv-pilot-db`.
3. Esperar a que finalice el deploy.
4. Abrir la URL HTTPS asignada al servicio.

## Seguridad
No subir al repositorio:
- bases SQLite;
- backups clínicos;
- PDFs o imágenes de pacientes;
- `.env`;
- credenciales o tokens.

## Datos
- Cloud: PostgreSQL mediante `DATABASE_URL`.
- Local: SQLite como fallback de desarrollo.
- `/api/backup` permite descargar una copia JSON del estado del piloto.

## Estado del proyecto
La arquitectura actual mantiene el estado funcional del piloto en un registro JSON central. Es adecuada para pruebas con datos ficticios. Antes de producción multiusuario deberá migrarse a un modelo relacional con control de concurrencia, autenticación y auditoría por campo.

## Versión actual
`RCV-V1.0-PILOT-002`

Incluye la actualización de la interfaz quirúrgica, validaciones de completitud/criticidad, ampliación de CRM, válvulas, ETE, CEC, soporte mecánico y generación/bloqueo del informe quirúrgico.
