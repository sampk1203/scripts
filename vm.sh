#!/bin/bash
#Creates a windows docker.
#alias win='flatpak run com.freerdp.FreeRDP /v:localhost:3389 /u:SameerKulkarni /p:docker /dynamic-resolution /f /sound:sys:pulse /microphone -decorations'
# Default flags
GPU_FLAG=false

# GPU device IDs
GPU="0000:01:00.0"
AUDIO="0000:01:00.1"

# Parse command line arguments
for arg in "$@"; do
  case $arg in
    -gpu) GPU_FLAG=true ;;
  esac
done

compose_file="docker-compose.yml"
container_name="windows"

# Function to setup GPU passthrough
setup_gpu() {
    echo "Setting up GPU passthrough..."
    sudo fuser -k /dev/nvidia* 2>/dev/null
    sudo modprobe vfio
    sudo modprobe vfio-pci
    [[ -e /sys/bus/pci/devices/$GPU/driver/unbind ]] && echo $GPU | sudo tee /sys/bus/pci/devices/$GPU/driver/unbind
    [[ -e /sys/bus/pci/devices/$AUDIO/driver/unbind ]] && echo $AUDIO | sudo tee /sys/bus/pci/devices/$AUDIO/driver/unbind
    echo vfio-pci | sudo tee /sys/bus/pci/devices/$GPU/driver_override
    echo vfio-pci | sudo tee /sys/bus/pci/devices/$AUDIO/driver_override
    echo $GPU | sudo tee /sys/bus/pci/drivers_probe
    echo $AUDIO | sudo tee /sys/bus/pci/drivers_probe
}

# Function to reset GPU passthrough
reset_gpu() {
    echo "Resetting GPU passthrough..."
    echo $GPU | sudo tee /sys/bus/pci/devices/$GPU/driver/unbind
    echo $AUDIO | sudo tee /sys/bus/pci/devices/$AUDIO/driver/unbind
    echo "" | sudo tee /sys/bus/pci/devices/$GPU/driver_override
    echo "" | sudo tee /sys/bus/pci/devices/$AUDIO/driver_override
    echo $GPU | sudo tee /sys/bus/pci/drivers_probe
    echo $AUDIO | sudo tee /sys/bus/pci/drivers_probe
}

# Check if container is running
is_container_running() {
    docker ps --filter "name=^/${container_name}$" --format '{{.Names}}' | grep -w "$container_name" &>/dev/null
    return $?
}

# Function to get available RAM in GB (rounded, leave safety buffer)
get_available_ram_gb() {
    # Extract values from free -m (to get more precise numbers)
    read total used free shared buff_cache available <<< $(free -m | awk '/^Mem:/ {print $2, $3, $4, $5, $6, $7}')

    total_gb=$((total / 1024))
    used_gb=$((used / 1024))
    free_gb=$((free / 1024))
    avail_gb=$((available / 1024))

    # Print system info to stderr
    echo "System memory status:" >&2
    echo "  Total: ${total_gb}G" >&2
    echo "  Used:  ${used_gb}G" >&2
    echo "  Free:  ${free_gb}G" >&2
    echo "  Avail: ${avail_gb}G" >&2

    # Subtract safety margin (1 GB)
    assignable=$((avail_gb - 1))
    if [ "$assignable" -lt 1 ]; then
        assignable=1
    fi

    echo "  Assigning to container: ${assignable}G" >&2

    echo "$assignable"
}

# Generate docker-compose.yml
generate_compose() {
    echo "Generating docker-compose.yml..."

    RAM_SIZE=$(get_available_ram_gb)
    echo "Setting RAM_SIZE to ${RAM_SIZE}G"

    if [ "$GPU_FLAG" = true ]; then
cat > $compose_file <<EOF
services:
  windows:
    image: dockurr/windows
    container_name: windows
    privileged: true
    environment:
      VERSION: "11l"
      DISK_SIZE: "250G"
      RAM_SIZE: "${RAM_SIZE}G"
      CPU_CORES: "16"
      USERNAME: "SameerKulkarni"
      PASSWORD: "docker"
      ARGUMENTS: >
        -device vfio-pci,host=01:00.0,multifunction=on
        -device vfio-pci,host=01:00.1,multifunction=on
        -machine type=q35,kernel_irqchip=on
        -rtc clock=host,base=utc,driftfix=slew
        -global kvm-pit.lost_tick_policy=discard
    devices:
      - /dev/kvm
      - /dev/net/tun
      - /dev/vfio/10
      - /dev/vfio/vfio
    cap_add:
      - NET_ADMIN
    ports:
      - 8006:8006
      - 3389:3389/tcp
      - 3389:3389/udp
    volumes:
      - ./windows:/storage
      - /home/sampk:/data
      - /media/sampk/350GB:/data2
      - /media/sampk/512GB:/data3
    restart: always
    stop_grace_period: 2m
EOF
    else
cat > $compose_file <<EOF
services:
  windows:
    image: dockurr/windows
    container_name: windows
    privileged: true
    environment:
      VERSION: "11l"
      DISK_SIZE: "250G"
      RAM_SIZE: "${RAM_SIZE}G"
      CPU_CORES: "16"
      USERNAME: "SameerKulkarni"
      PASSWORD: "docker"
    devices:
      - /dev/kvm
      - /dev/net/tun
    cap_add:
      - NET_ADMIN
    ports:
      - 8006:8006
      - 3389:3389/tcp
      - 3389:3389/udp
    volumes:
      - ./windows:/storage
      - /home/sampk:/data
      - /media/sampk/350GB:/data2
      - /media/sampk/512GB:/data3
    restart: always
    stop_grace_period: 2m
EOF
    fi
}

# Main toggle logic
if is_container_running; then
    echo "Container '$container_name' is running. Stopping it..."
    docker compose down
    if [ "$GPU_FLAG" = true ]; then
        reset_gpu
    fi
else
    echo "Container '$container_name' is not running. Starting it..."
    if [ "$GPU_FLAG" = true ]; then
        setup_gpu
    fi
    generate_compose
    docker compose up -d
fi
