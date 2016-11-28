#!/bin/bash

[ -z "${CRON_SCHEDULE}" ] && { echo "=> CRON_SCHEDULE cannot be empty" && exit 1; }
[ -z "${HOST}" ] && { echo "=> HOST cannot be empty" && exit 1; }
[ -z "${PORT}" ] && { echo "=> PORT cannot be empty" && exit 1; }
[ -z "${USER}" ] && { echo "=> USER cannot be empty" && exit 1; }
[ -z "${PASS}" ] && { echo "=> PASS cannot be empty" && exit 1; }
[ -z "${BACKUP_TYPE}" ] && { echo "=> BACKUP_TYPE cannot be empty" && exit 1; }
[ -z "${BACKUP_RETENTION_TIME_IN_DAYS}" ] && { echo "=> BACKUP_RETENTION_TIME_IN_DAYS cannot be empty" && exit 1; }

if [ ${BACKUP_TYPE} = "mongo" ]; then
  [ -z "${DB}" ] && { echo "=> DB cannot be empty" && exit 1; }
  USER_STR="--username ${USER}"
  HOST_STR="--host ${HOST}"
  PORT_STR="--port ${PORT}"
  PASS_STR="--password '${PASS}'"
  DB_STR="--db ${DB}"
  CMD_STR="mongodump"
  CMD_SFX="--out /backup/dump && tar -cf /backup/\${BACKUP_NAME} -C /backup dump"
  FILE_SFX="${DB}.dmp.tar"
elif [ ${BACKUP_TYPE} = "mysql" ]; then
  USER_STR="-u ${USER}"
  HOST_STR="-h ${HOST}"
  PORT_STR="-P ${PORT}"
  PASS_STR="--password='${PASS}'"
  DB_STR="--all-databases"
  [[ ( -n "${DB}" ) ]] && DB_STR="--databases ${DB}"
  CMD_STR="mysqldump"
  CMD_SFX="--add-drop-database=TRUE > /backup/"'${BACKUP_NAME}'
  FILE_SFX="sql"
else
  echo "BACKUP_TYPE ${BACKUP_TYPE} unknown. Aborting backup."
  exit 0
fi
# all backup types
[[ ( -n "${DB_STR}" ) ]] && PASS_STR="${PASS_STR} ${DB_STR}"

BACKUP_CMD="${CMD_STR} ${HOST_STR} ${PORT_STR} ${USER_STR} ${PASS_STR} ${CMD_SFX}"

echo "=> Creating backup script"
rm -f /backup.sh
cat <<EOF >> /backup.sh
#!/bin/bash
BACKUP_NAME=${BACKUP_TYPE}-db-${HOST}-\$(date +\%Y.\%m.\%d-\%H.\%M.\%S).${FILE_SFX}
echo "=> Backup started: \${BACKUP_NAME}"

echo "Cleanup any old backup artifacts older than $BACKUP_RETENTION_TIME_IN_DAYS days..."
find /backup -mtime $BACKUP_RETENTION_TIME_IN_DAYS | xargs rm -rfv

if ${BACKUP_CMD} ;then
    echo "=> Backup succeeded"
    echo "${SECRET_PHRASE}" | gpg2 --batch --passphrase-fd 0 --symmetric --cipher-algo AES256 --output /backup/\${BACKUP_NAME}.gpg /backup/\${BACKUP_NAME}
    gcloud auth activate-service-account ${ACCT} --key-file /secrets/key
    gsutil cp  /backup/\${BACKUP_NAME}.gpg ${BUCKET}/${HOST}/
else
    echo "=> Backup failed"
fi
EOF

echo "=> Creating cron job"
chmod +x /backup.sh
echo "${CRON_SCHEDULE} /backup.sh 2>&1 | tee /backup/backup.log" > /crontab.conf
crontab  /crontab.conf
echo "=> Running cron job"
exec cron -f
