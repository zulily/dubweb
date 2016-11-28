#!/bin/bash

[ -z "${HOST}" ] && { echo "=> HOST cannot be empty" && exit 1; }
[ -z "${PORT}" ] && { echo "=> PORT cannot be empty" && exit 1; }
[ -z "${USER}" ] && { echo "=> USER cannot be empty" && exit 1; }
[ -z "${PASS}" ] && { echo "=> PASS cannot be empty" && exit 1; }
[ -z "${BACKUP_TYPE}" ] && { echo "=> BACKUP_TYPE cannot be empty" && exit 1; }

if [ ${BACKUP_TYPE} = "mongo" ]; then
  [ -z "${DB}" ] && { echo "=> DB cannot be empty" && exit 1; }
  USER_STR="--username ${USER}"
  HOST_STR="--host ${HOST}"
  PORT_STR="--port ${PORT}"
  PASS_STR="--password '${PASS}'"
  DB_STR="--db ${DB}"
  CMD_STR="tar -xf /restore/\${RESTOREFILE} -C /restore && mongorestore /restore/dump/${DB}"
  CMD_SFX=""
elif [ ${BACKUP_TYPE} = "mysql" ]; then
  USER_STR="-u ${USER}"
  HOST_STR="-h ${HOST}"
  PORT_STR="-P ${PORT}"
  PASS_STR="--password='${PASS}'"
  [[ ( -n "${DB}" ) ]] && DB_STR="--databases ${DB}"
  CMD_STR="mysql"
  CMD_SFX=" < /restore/"'${RESTOREFILE}'
else
  echo "BACKUP_TYPE ${BACKUP_TYPE} unknown. Aborting restore."
  exit 0
fi
# all backup types
[[ ( -n "${DB_STR}" ) ]] && PASS_STR="${PASS_STR} ${DB_STR}"
CRON_TIME_NONE="#0 0 * * *"
CRON_TIME_ALL="* * * * *"

BACKUP_CMD="${CMD_STR} ${HOST_STR} ${PORT_STR} ${USER_STR} ${PASS_STR} ${CMD_SFX}"

echo "=> Creating restore script"
rm -f /restore.sh
cat <<EOF >> /restore.sh
#!/bin/bash
echo "=> Restore started"
echo "${CRON_TIME_NONE} /restore.sh 2>&1" > /crontab.conf
crontab  /crontab.conf
gcloud auth activate-service-account ${ACCT} --key-file /secrets/key
LATESTPATH=\$(gsutil ls ${BUCKET}/${HOST}/${BACKUP_TYPE}-db-${HOST}*.gpg | tail -n 1)
ENCRFILE=\$(echo \${LATESTPATH} | rev | cut -f 1 -d"/" | rev)
RESTOREFILE=\$(echo \${ENCRFILE} | rev | cut -f 2-  -d"." | rev)
gsutil cp \${LATESTPATH}  /restore/\${ENCRFILE} 
echo "${SECRET_PHRASE}" | gpg2 --batch --passphrase-fd 0 --decrypt  --output /restore/\${RESTOREFILE} /restore/\${ENCRFILE}
if ${BACKUP_CMD} ;then
    echo "=> Restore succeeded"
else
    echo "=> Restore failed"
fi
EOF

echo "=> Creating cron job"
chmod +x /restore.sh
echo "${CRON_TIME_ALL} /restore.sh 2>&1" > /crontab.conf
crontab  /crontab.conf
echo "=> Running cron job"
exec cron -f

