#!/bin/bash
#################################
# gce_up.sh
# usage: gce_up.sh machine-001.txt

# load the settings file passed on the command line
source ./$1

if [ -n ${DATADRIVENAME} ]; then
  # Create external data drive
  DATADISK=" --disk=name=${DATADRIVENAME},device-name=${DATADRIVENAME},mode=rw,boot=no"
  DATAFMTNAME="sudo -u root mkfs.ext4 -F -E lazy_itable_init=0,lazy_journal_init=0,discard /dev/disk/by-id/google-${DATADRIVENAME}"
  DATADIRCMD="sudo -u root mkdir ${DATADRIVEMOUNT}"
  DATAMNTCMD="sudo -u root mount -o discard,defaults /dev/disk/by-id/google-${DATADRIVENAME} ${DATADRIVEMOUNT}"
  # create utility disk
  if 
  gcloud compute disks create $machine_data_disk_name --project=$project \
   --type=$machine_data_disk_type --size=$machine_data_disk_sz --zone=$zone

else
  DATADISK=""
fi


# create machine node with disk
gcloud compute instances create $machine_name \
 --project=$project --image=$machine_image --zone=$zone \
 --boot-disk-type=$machine_boot_disk_type --boot-disk-size=$machine_boot_disk_sz \
 --boot-disk-device-name=$machine_name --machine-type=$machine_type \
 --can-ip-forward --scopes compute-rw --tags=$tags \
 --disk=$disk
# format disk
echo "Sleep 60 seconds before ssh to server"
sleep 60
# format disk
gcloud compute ssh $machine_name --zone=$zone \
 --command="$fmtcmd"
# mkdir & mount disk
gcloud compute ssh $machine_name --zone=$zone \
 --command="$mkdircmd"
gcloud compute ssh $machine_name --zone=$zone \
 --command="$mntcmd"

else
# Create machine without external disk
gcloud compute instances create $machine_name \
 --project=$project --image=$machine_image --zone=$zone \
 --boot-disk-type=$machine_boot_disk_type --boot-disk-size=$machine_boot_disk_sz \
 --boot-disk-device-name=$machine_name --machine-type=$machine_type \
 --can-ip-forward --scopes compute-rw --tags=$tags 
fi
#
# bundle up any install stuff you want pushed and send it over using the below command
#sleep 30
#gcloud beta compute scp ../install.tar.gz $machine_name:~/ --project=$project --zone=$zone

