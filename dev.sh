NAME=simple-metagenomics
DOCKER_IMAGE=quay.io/txyliu/$NAME
echo image: $DOCKER_IMAGE

HERE=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

case $1 in
    --build|-b)
        sudo docker build -t $DOCKER_IMAGE .
    ;;
    --sif)
        sudo singularity build $NAME.sif docker-daemon://$DOCKER_IMAGE
    ;;
    --run|-r)
        docker run -it --rm \
            -e XDG_CACHE_HOME="/app/scratch" \
            --mount type=bind,source="$HERE",target="/app" \
            --workdir="/app" \
            -u $(id -u):$(id -g) \
            $DOCKER_IMAGE \
            mamba run -n main ${*: 2:99}
    ;;
    --shell|-s)
        docker run -i --rm -a stdout -a stderr \
            -e XDG_CACHE_HOME="/app/scratch" \
            --mount type=bind,source="$HERE",target="/app" \
            --workdir="/app" \
            -u $(id -u):$(id -g) \
            $DOCKER_IMAGE
    ;;
    -tget)
        docker run $DOCKER_IMAGE \
            mamba run -n main fasterq-dump \
            -t $3 -O $3  ${*: 2:99}
    ;;
    *)
        echo "bad option"
        echo $1
    ;;
esac
