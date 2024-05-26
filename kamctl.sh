#!/bin/bash
#>Kamera Steuerung und Überwachung
#uses $WHERE_AM_I
BASH_LIB="${HOME}/devel/bash_scripts/bash_lib"
if [[ -f ${BASH_LIB}/std_lib.sh ]]
	then source ${BASH_LIB}/std_lib.sh
	else echo ERROR ${BASH_LIB}/std_lib.sh; exit 1
fi
         version='1.11'
            this=$0
        hostlist=''
       localhost=0
        allhosts='europa kamera0 kamera1 kamera2 kamera3 kamera4 kamera5 kamera6 kamera8 kamera9 kameraA kameraB kameraC kameraD kameraX'
         dirlist='kamera-server'
    KS_AUTOSTART='KS_AUTOSTART'
       KS_TARGET='kamsvr'
     SENSOR_NAME="sensor-data.txt"	 
   SENSOR_REMOTE="${HOME}/data"
    SENSOR_LOCAL="${HOME}/sensor-data-test"
    DEVEL_SOURCE="${HOME}/devel"
    DEVEL_TARGET="${HOME}/devel"
    CONFIG_LOCAL="${HOME}/devel/kamera-server/ks-config"
   CONFIG_REMOTE="${HOME}"
    RSYNC_DELETE=''
         TIMEOUT=5
         VERBOSE=''
           wsbin='send-command'
     config_name=".ks.conf"
         logfile="${HOME}/.ks.log"
           PROXY="garten"
           rsync="rsync ${VERBOSE} --timeout=${TIMEOUT} ${PROGRESS} -az"
             cmd="cmd_camera_command"
          ks_cmd="status3"
            PORT="4000"

function exit_program { printf "\n${_yellow_}ENDE.\n${_default_}"; exit 1; }

declare -A devices=( #{{{
#          key  = host swnr on-state off-state confirmation
#                   |    |    |      |         |
#                   |    | +--+      |         |
#                   |    | | +-------+         |
#                   |    | | | +---------------+
#                   |    | | | |
	    [sonnen]="esp4   9 0 1 0"
	   [pergola]="esp4   8 0 1 0"
	       [weg]="esp4  10 0 1 0"
       [likette]="esp4  14 0 1 0"
	 [ir-treppe]="esp4   0 0 1 0"
	 [ir-hinter]="esp4   1 0 1 0"
	   [power-0]="esp4   2 1 0 1"
	    [kueche]="esp4   3 0 1 0"
	   [power-6]="esp4   5 1 0 1"
	   [power-8]="esp4   4 1 0 1"
	   [power-x]="esp4   6 1 0 1"
	 [power-bcd]="esp4   7 1 0 1"

	    [ir-weg]="esp3  11 0 1 0"
	[ir-carport]="esp3   8 0 1 0"
	   [power-1]="esp3   0 1 0 1"
	   [power-2]="esp3   1 1 0 1"
	   [power-3]="esp3   2 1 0 1"
	   [power-4]="esp3   4 1 0 1"
	   [power-5]="esp3   3 1 0 1"
	   [power-9]="esp3  15 1 0 1"

	   [power-a]="esp2   0 1 0 1"

	  [esp1x-00]="esp1x  0 1 0 0"
	  [esp1x-01]="esp1x  1 1 0 0"
	  [esp1x-02]="esp1x  2 1 0 0"
	  [esp1x-03]="esp1x  3 1 0 0"
	  [esp1x-04]="esp1x  4 1 0 0"
	  [esp1x-05]="esp1x  5 1 0 0"
	  [esp1x-06]="esp1x  6 1 0 0"
	  [esp1x-07]="esp1x  7 1 0 0"
	  [esp1x-08]="esp1x  8 1 0 0"
	  [esp1x-09]="esp1x  9 1 0 0"
	  [esp1x-0a]="esp1x 10 1 0 0"
	  [esp1x-0b]="esp1x 11 1 0 0"
	  [esp1x-0c]="esp1x 12 1 0 0"
	  [esp1x-0d]="esp1x 13 1 0 0"
	  [esp1x-0e]="esp1x 14 1 0 0"
	  [esp1x-0f]="esp1x 15 1 0 0"
	  [esp1x-10]="esp1x 16 1 0 0"
	  [esp1x-11]="esp1x 17 1 0 0"
	  [esp1x-12]="esp1x 18 1 0 0"
	  [esp1x-13]="esp1x 19 1 0 0"
	  [esp1x-14]="esp1x 20 1 0 0"
	  [esp1x-15]="esp1x 21 1 0 0"
	  [esp1x-16]="esp1x 22 1 0 0"
	  [esp1x-17]="esp1x 23 1 0 0"
	  [esp1x-18]="esp1x 24 1 0 0"
	  [esp1x-19]="esp1x 25 1 0 0"
	  [esp1x-1a]="esp1x 26 1 0 0"
	  [esp1x-1b]="esp1x 27 1 0 0"
	  [esp1x-1c]="esp1x 28 1 0 0"
	  [esp1x-1d]="esp1x 29 1 0 0"
	  [esp1x-1e]="esp1x 30 1 0 0"
	  [esp1x-1f]="esp1x 31 1 0 0"

	  [esp1-00]="esp1  0 1 0 0"
	  [esp1-01]="esp1  1 1 0 0"
	  [esp1-02]="esp1  2 1 0 0"
	  [esp1-03]="esp1  3 1 0 0"
	  [esp1-04]="esp1  4 1 0 0"
	  [esp1-05]="esp1  5 1 0 0"
	  [esp1-06]="esp1  6 1 0 0"
	  [esp1-07]="esp1  7 1 0 0"
	  [esp1-08]="esp1  8 1 0 0"
	  [esp1-09]="esp1  9 1 0 0"
	  [esp1-0a]="esp1 10 1 0 0"
	  [esp1-0b]="esp1 11 1 0 0"
	  [esp1-0c]="esp1 12 1 0 0"
	  [esp1-0d]="esp1 13 1 0 0"
	  [esp1-0e]="esp1 14 1 0 0"
	  [esp1-0f]="esp1 15 1 0 0"
	  [esp1-10]="esp1 16 1 0 0"
	  [esp1-11]="esp1 17 1 0 0"
	  [esp1-12]="esp1 18 1 0 0"
	  [esp1-13]="esp1 19 1 0 0"
	  [esp1-14]="esp1 20 1 0 0"
	  [esp1-15]="esp1 21 1 0 0"
	  [esp1-16]="esp1 22 1 0 0"
	  [esp1-17]="esp1 23 1 0 0"
	  [esp1-18]="esp1 24 1 0 0"
	  [esp1-19]="esp1 25 1 0 0"
	  [esp1-1a]="esp1 26 1 0 0"
	  [esp1-1b]="esp1 27 1 0 0"
	  [esp1-1c]="esp1 28 1 0 0"
	  [esp1-1d]="esp1 29 1 0 0"
	  [esp1-1e]="esp1 30 1 0 0"
	  [esp1-1f]="esp1 31 1 0 0"

	  [esp2-00]="esp2  0 1 0 1"
	  [esp2-01]="esp2  1 1 0 1"
	  [esp2-02]="esp2  2 1 0 1"
	  [esp2-03]="esp2  3 1 0 1"
	  [esp2-04]="esp2  4 1 0 1"
	  [esp2-05]="esp2  5 1 0 1"
	  [esp2-06]="esp2  6 1 0 1"
	  [esp2-07]="esp2  7 1 0 1"
	  [esp2-08]="esp2  8 1 0 1"
	  [esp2-09]="esp2  9 1 0 1"
	  [esp2-0a]="esp2 10 1 0 1"
	  [esp2-0b]="esp2 11 1 0 1"
	  [esp2-0c]="esp2 12 1 0 1"
	  [esp2-0d]="esp2 13 1 0 1"
	  [esp2-0e]="esp2 14 1 0 1"
	  [esp2-0f]="esp2 15 1 0 1"
	  [esp2-10]="esp2 16 1 0 1"
	  [esp2-11]="esp2 17 1 0 1"
	  [esp2-12]="esp2 18 1 0 1"
	  [esp2-13]="esp2 19 1 0 1"
	  [esp2-14]="esp2 20 1 0 1"
	  [esp2-15]="esp2 21 1 0 1"
	  [esp2-16]="esp2 22 1 0 1"
	  [esp2-17]="esp2 23 1 0 1"
	  [esp2-18]="esp2 24 1 0 1"
	  [esp2-19]="esp2 25 1 0 1"
	  [esp2-1a]="esp2 26 1 0 1"
	  [esp2-1b]="esp2 27 1 0 1"
	  [esp2-1c]="esp2 28 1 0 1"
	  [esp2-1d]="esp2 29 1 0 1"
	  [esp2-1e]="esp2 30 1 0 1"
	  [esp2-1f]="esp2 31 1 0 1"

	  [esp3-00]="esp3  0 1 0 1"
	  [esp3-01]="esp3  1 1 0 1"
	  [esp3-02]="esp3  2 1 0 1"
	  [esp3-03]="esp3  3 1 0 1"
	  [esp3-04]="esp3  4 1 0 1"
	  [esp3-05]="esp3  5 1 0 1"
	  [esp3-06]="esp3  6 1 0 1"
	  [esp3-07]="esp3  7 1 0 1"
	  [esp3-08]="esp3  8 1 0 1"
	  [esp3-09]="esp3  9 1 0 1"
	  [esp3-0a]="esp3 10 1 0 1"
	  [esp3-0b]="esp3 11 1 0 1"
	  [esp3-0c]="esp3 12 1 0 1"
	  [esp3-0d]="esp3 13 1 0 1"
	  [esp3-0e]="esp3 14 1 0 1"
	  [esp3-0f]="esp3 15 1 0 1"
	  [esp3-10]="esp3 16 1 0 1"
	  [esp3-11]="esp3 17 1 0 1"
	  [esp3-12]="esp3 18 1 0 1"
	  [esp3-13]="esp3 19 1 0 1"
	  [esp3-14]="esp3 20 1 0 1"
	  [esp3-15]="esp3 21 1 0 1"
	  [esp3-16]="esp3 22 1 0 1"
	  [esp3-17]="esp3 23 1 0 1"
	  [esp3-18]="esp3 24 1 0 1"
	  [esp3-19]="esp3 25 1 0 1"
	  [esp3-1a]="esp3 26 1 0 1"
	  [esp3-1b]="esp3 27 1 0 1"
	  [esp3-1c]="esp3 28 1 0 1"
	  [esp3-1d]="esp3 29 1 0 1"
	  [esp3-1e]="esp3 30 1 0 1"
	  [esp3-1f]="esp3 31 1 0 1"

	  [esp4-00]="esp4  0 1 0 1"
	  [esp4-01]="esp4  1 1 0 1"
	  [esp4-02]="esp4  2 1 0 1"
	  [esp4-03]="esp4  3 1 0 1"
	  [esp4-04]="esp4  4 1 0 1"
	  [esp4-05]="esp4  5 1 0 1"
	  [esp4-06]="esp4  6 1 0 1"
	  [esp4-07]="esp4  7 1 0 1"
	  [esp4-08]="esp4  8 1 0 1"
	  [esp4-09]="esp4  9 1 0 1"
	  [esp4-0a]="esp4 10 1 0 1"
	  [esp4-0b]="esp4 11 1 0 1"
	  [esp4-0c]="esp4 12 1 0 1"
	  [esp4-0d]="esp4 13 1 0 1"
	  [esp4-0e]="esp4 14 1 0 1"
	  [esp4-0f]="esp4 15 1 0 1"
	  [esp4-10]="esp4 16 1 0 1"
	  [esp4-11]="esp4 17 1 0 1"
	  [esp4-12]="esp4 18 1 0 1"
	  [esp4-13]="esp4 19 1 0 1"
	  [esp4-14]="esp4 20 1 0 1"
	  [esp4-15]="esp4 21 1 0 1"
	  [esp4-16]="esp4 22 1 0 1"
	  [esp4-17]="esp4 23 1 0 1"
	  [esp4-18]="esp4 24 1 0 1"
	  [esp4-19]="esp4 25 1 0 1"
	  [esp4-1a]="esp4 26 1 0 1"
	  [esp4-1b]="esp4 27 1 0 1"
	  [esp4-1c]="esp4 28 1 0 1"
	  [esp4-1d]="esp4 29 1 0 1"
	  [esp4-1e]="esp4 30 1 0 1"
	  [esp4-1f]="esp4 31 1 0 1"
) #}}}

function usage { #{{{
	printf "${version}\n"
	printf "${0##*/} [all|local|kam 0123456789abcdekx] [options] [command] [preset]\n"
	printf "${0##*/} device [on|off]\n"
	printf "target: ${KS_TARGET}\n"
	printf "all               all kameras\n"
	printf "local             executes commands on this machine\n"
	printf "0123456789abcdek  shortcut server names\n"
	printf "device            weg|pergola|sonnen|kueche|likette|ir-weg|ir-treppe|ir-hinter|ir-carport\n"
	printf "                  power-[012345689a]|power-bcd]\n"
	printf "                  esp[1234]-xx\n"
	printf "                  test-[00..1f]\n"
	# echo ${!devices[@]}
	printf "esp[1234]         show registers\n"
	printf "esp[1234]-conf    show config\n"
	printf "    +start|+                      start the server\n"
	printf "    +quit                         send 'quit' command\n"
	printf "    +stop |-                      send SIGTERM\n"
	printf "    +kill                         send SIGKILL\n"
	printf "    +disk-free                    disk space usage\n"
	printf "    +show-sensors  |+t            shows latest sensor data\n"
	printf "    +show-log      |+l            shows latest debug messages\n"
	printf "    +sync-devel    |+d            syncronize devel directories\n"
	printf "    +shell-command |+x <command>  runs shell command\n"
	printf "    +camera-command|+c <command>  sends command to kamera-server\n"
	printf "    +status1,2,3   |+s1,2,3       display camera status\n"
	printf "    +config-send   |+cs           send ${config_name} to kamera\n"
	printf "    +config-recv   |+cr           receive\n"
	printf "    +config-load   |+cl           load\n"
	printf "    +config-set    |+ct <name>    set\n"
	printf "presets:\n"
	printf "    ++base|++night|++day|++fps1|++fps2|++fps5|++fps15\n"
	printf "    +osd0|+osd1\n"
	printf "options:\n"
	printf "    --target <kamera-server-prg>\n"
	printf "    --delete                       rsync --delete options\n"
	printf "    --dirs    |-d \"dir1 dir2 ...\"\n"
	# printf "    --hosts   |-h all|\"host1 host2 ...\"\n"
	printf "    --timeout |-t <sec>           timeout in seconds (${TIMEOUT}s)\n"
	printf "    --progress|-P                 rsync progress display\n"
	printf "    -v1,2,3                       ssh verbosity\n"
	printf "    --help\n"
	# printf "  hosts: %s\n" "${allhosts}"
	printf "  devel: %s\n" "${dirlist}"
} #}}}

function confirm { #{{{
	[[ $1 == 0 ]] && return 0
	read -n 1 -p "confirm with [Y] "
	echo
	if [[ $REPLY == "Y" ]];
		then return 0
		else echo ABORT COMMAND; return 1
	fi
	return 1
} #}}}

function switch_state { #{{{
	#$1:assoc-index
	local esp sw on off register
	read esp sw on off <<< ${devices[$1]}
	register=($(${wsbin} ${esp} "READ O"))
	if [[ ${register[2]:$sw:1} == ${on} ]];
	then echo on
	else echo off
	fi
} #}}}

function switch2 { #{{{
	#$1:assoc-index $2:on|off|read
	local esp sw on off confirm
	read esp sw on off confirm <<< ${devices[$1]}
	case $2 in
		 on) onoff=$on;;
		off) onoff=$off;;
		  *) echo ERROR; return 1;;
	esac
	confirm $confirm &&\
	printf "      0123456789ABCDEF0123456789ABCDEF\n" &&\
	${wsbin} ${esp} "READ O" &&\
	${wsbin} ${esp} "WRITEBIT A ${sw} ${onoff}" >/dev/null &&\
	${wsbin} ${esp} "OUT" >/dev/null &&\
	${wsbin} ${esp} "READ O"
} #}}}

trap exit_program SIGINT

if [[ $# < 1 ]];        then usage; exit 1; fi
# if [[ "$1" == [+-]* ]]; then usage; exit 1; fi

if [ ${devices[$1]+_} ]; then
	if [[ -z $2 ]]
		then switch_state $1
		else switch2 $1 $2
	fi
	exit 0
fi

case $1 in
	       --version) printf "${version}\n";        exit 0;;
	 esp1x-reg|esp1x) ${wsbin} esp1x "STATUS-REG";  exit 0;;
	   esp1-reg|esp1) ${wsbin} esp1  "STATUS-REG";  exit 0;;
	   esp2-reg|esp2) ${wsbin} esp2  "STATUS-REG";  exit 0;;
	   esp3-reg|esp3) ${wsbin} esp3  "STATUS-REG";  exit 0;;
	   esp4-reg|esp4) ${wsbin} esp4  "STATUS-REG";  exit 0;;
	      esp1x-conf) ${wsbin} esp1x "STATUS-CONF"; exit 0;;
	       esp1-conf) ${wsbin} esp1  "STATUS-CONF"; exit 0;;
	       esp2-conf) ${wsbin} esp2  "STATUS-CONF"; exit 0;;
	       esp3-conf) ${wsbin} esp3  "STATUS-CONF"; exit 0;;
	       esp4-conf) ${wsbin} esp4  "STATUS-CONF"; exit 0;;
	             all) hostlist=${allhosts}; shift;;
	           local) localhost=1;          shift;;
	             kam) shift
		for (( i=0; i<${#1}; i++))
		do
			case ${1:i:1} in
				0) hostlist="$hostlist kamera0";;
				1) hostlist="$hostlist kamera1";;
				2) hostlist="$hostlist kamera2";;
				3) hostlist="$hostlist kamera3";;
				4) hostlist="$hostlist kamera4";;
				5) hostlist="$hostlist kamera5";;
				6) hostlist="$hostlist kamera6";;
				7) hostlist="$hostlist kamera7";;
				8) hostlist="$hostlist kamera8";;
				9) hostlist="$hostlist kamera9";;
				a) hostlist="$hostlist kameraA";;
				b) hostlist="$hostlist kameraB";;
				c) hostlist="$hostlist kameraC";;
				d) hostlist="$hostlist kameraD";;
				x) hostlist="$hostlist kameraX";;
				e) hostlist="$hostlist europa";;
				k) hostlist="$hostlist merkur";;
			esac
		done
esac
while [[ $# > 0 ]]
do
	case $1 in
		#__commands________________________________________________________________
		+show-sensors|+t)   cmd=cmd_show_sensors;;
		+show-log|+l)       cmd=cmd_shell_command;  sh_cmd="tail -n 100 -f ${logfile}";;
		+sync-devel|+d)     cmd=cmd_sync_devel;;
		+shell-command|+x)  cmd=cmd_shell_command;  sh_cmd=$2;                 shift;;
		+camera-command|+c) cmd=cmd_camera_command; ks_cmd="$2";               shift;;
		+disk-free|+df)     cmd=cmd_shell_command;  sh_cmd="df -h / | awk 'NR>1 {print \$0}'";;
		+config-send|+cs)   cmd=cmd_config_send;                               shift;;
		+config-recv|+cr)   cmd=cmd_config_recv;;
		+config-load|+cl)   cmd=cmd_camera_command; ks_cmd="config-load";      shift;;
		+config-set|+ct)    cmd=cmd_camera_command; ks_cmd="config-set $2";    shift;;
		++base)             cmd=cmd_camera_command; ks_cmd="config-set base";  shift;;
		++day)              cmd=cmd_camera_command; ks_cmd="config-set day";   shift;;
		++night)            cmd=cmd_camera_command; ks_cmd="config-set night"; shift;;
		++fps1)             cmd=cmd_camera_command; ks_cmd="config-set fps1";  shift;;
		++fps2)             cmd=cmd_camera_command; ks_cmd="config-set fps2";  shift;;
		++fps5)             cmd=cmd_camera_command; ks_cmd="config-set fps5";  shift;;
		++fps15)            cmd=cmd_camera_command; ks_cmd="config-set fps15"; shift;;
		+|+start)           cmd=cmd_start;;
		-|+stop)            cmd=cmd_stop;;
		+kill)              cmd=cmd_kill;;
		+quit)              cmd=cmd_quit;;
		+power-on)          cmd=cmd_power_on;;
		+power-off)         cmd=cmd_power_off;;
		+status1|+s1)       cmd=cmd_camera_command; ks_cmd="status1";;
		+status2|+s2)       cmd=cmd_camera_command; ks_cmd="status2";;
		+status3|+s3)       cmd=cmd_camera_command; ks_cmd="status3";;
		+osd1)              cmd=cmd_camera_command; ks_cmd="osd1";;
		+osd0)              cmd=cmd_camera_command; ks_cmd="osd0";;
		+help)              usage; exit;;
		#__options__________________________________________________________________
		# --local) hostlist="$(hostname)";;
		--hosts|-h)
			if [[ $2 = "all" ]]
			then
				hostlist=${allhosts}
			else
				hostlist=${2}
			fi
			shift;;
		--target)         KS_TARGET=${2}; shift;;
		--delete)         RSYNC_DELETE='--delete';;
		--dirs|-d)        dirlist=${2};  shift;;
		--timeout|-t)     TIMEOUT=${2};  shift;;
		--progress)       PROGRESS="--progress";;
		# for ssh command
		-v1|-v)     VERBOSE="-v";;
		-v2|-vv)    VERBOSE="-vv";;
		-v3|-vvv)   VERBOSE="-vvv";;
	esac
	shift
done

SSH="ssh ${VERBOSE} -o ConnectTimeout=${TIMEOUT} "

if [[ $localhost == 1 ]]
then
	case $cmd in
		cmd_start)
			pgrep --exact "${KS_TARGET}" >/dev/null
			if [[ $? == 0 ]]
			then
				echo ${KS_TARGET} is already running
				exit 1
			else
				nohup ~/bin/${KS_TARGET} &>>${logfile} </dev/null &
				echo START ${KS_TARGET}
			fi
			;;
		cmd_stop)
			pgrep --exact "${KS_TARGET}" >/dev/null
			if [[ $? == 0 ]]
			then
				pkill --signal SIGTERM --exact ${KS_TARGET}
				echo SIGTERM sent to ${KS_TARGET}
			else
				echo not running
			fi
			;;
		cmd_kill)
			pgrep --exact "${KS_TARGET}" >/dev/null
			if [[ $? == 0 ]]
			then
				pkill --signal SIGKILL --exact ${KS_TARGET}
				echo SIGKILL sent to ${KS_TARGET}
			else
				echo "${KS_TARGET}" not running
			fi
			;;
		cmd_quit)
			pgrep --exact "${KS_TARGET}" >/dev/null
			if [[ $? == 0 ]]
			then
				echo QUIT command sent to ${KS_TARGET}
				ws localhost quit
			else
				echo "${KS_TARGET}" not running
			fi
			;;
		*)
			;;
	esac
	exit 1
fi

for HOST in ${hostlist}
do
	if nc -z -w 1 $HOST 22 2>/dev/null
	then
		case $cmd in
			cmd_sync_devel)
				for DIR in ${dirlist}; do
					if [[ ${HOST} != $(hostname) ]]
					then
						printf "${_fg_green_}${HOST}:${_reset_} --->${DEVEL_TARGET}/${DIR}\n";
						${rsync} ${RSYNC_DELETE} ${DEVEL_SOURCE}/${DIR}/ ${HOST}:${DEVEL_TARGET}/${DIR};
					fi
				done
				;;
			cmd_config_send)
				printf "${_fg_green_}%7s: ${_reset_}CONFIG SEND\n" ${HOST}
				${rsync} ${CONFIG_LOCAL}/${config_name}-${HOST}.config ${HOST}:${CONFIG_REMOTE}/${config_name}
				;;
			cmd_config_recv)
				printf "${_fg_green_}%7s: ${_reset_}CONFIG RECEIVE\n" ${HOST}
				${rsync} ${HOST}:${CONFIG_REMOTE}/${config_name} ${CONFIG_LOCAL}/${config_name}-${HOST}.config
				;;
			cmd_config_show)
				;;
			cmd_start) printf "${_fg_green_}%7s:${_reset_} " ${HOST}; ${SSH} ${HOST} "${this} local +start";;
			cmd_stop)  printf "${_fg_green_}%7s:${_reset_} " ${HOST}; ${SSH} ${HOST} "${this} local +stop";;
			cmd_kill)  printf "${_fg_green_}%7s:${_reset_} " ${HOST}; ${SSH} ${HOST} "${this} local +kill";;
			cmd_quit)  printf "${_fg_green_}%7s:${_reset_} " ${HOST}; ${wsbin} ${HOST} "quit";;
			cmd_autostart);;
			cmd_show_sensors)
				printf "\n____DATE________1min____5min____15min___T_cpu___T_gpu___LUX_____hPa______T0______T1______T2___\n"
				${SSH} europa "tail -n 45 ~/data-kameras/${HOST}/sensor-data/sensor-data2.txt";
				printf "______________________________________________________________________________________________\n";
				;;
			cmd_shell_command)
				printf "${_fg_green_}%7s:${_reset_} " ${HOST}
				${SSH} ${HOST} ${sh_cmd}
				;;
			cmd_camera_command)
				# printf " ${ks_cmd}\n";
				printf "${_fg_green_}%7s:${_reset_} " ${HOST}
				${wsbin} ${HOST} "${ks_cmd}"
				;;
			*)
				;;
		esac
	else
		printf "${_red_}${HOST} is offline.${_reset_}\n"
	fi
done

printf "\nENDE.\n"
