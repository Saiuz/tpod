DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export FLASK_APP=$DIR/app.py
export FLASK_DEBUG=1
export DB_USER='tpod'
export DB_PASSWORD='your-super-secret-key'
export DB_NAME='tpod'
export CONTAINER_REGISTRY_URL='registry.cmusatyalab.org/junjuew/container-registry'
