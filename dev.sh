NAME=simple-metagenomics
DOCKER_IMAGE=quay.io/txyliu/$NAME
echo image: $DOCKER_IMAGE
echo ""
# echo ""

HERE=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

case $1 in
    --build|-b)
        cd docker 
        sudo docker build -t $DOCKER_IMAGE .
    ;;
    --sif)
        sudo singularity build $NAME.sif docker-daemon://$DOCKER_IMAGE
    ;;
    --run|-r)
        docker run -it --rm \
            -e XDG_CACHE_HOME="/ws"\
            --mount type=bind,source="$HERE/scratch",target="/ws" \
            --mount type=bind,source="$HERE/scratch/res",target="/ref"\
            --mount type=bind,source="$HERE/scratch/res/.ncbi",target="/.ncbi" \
            --mount type=bind,source="$HERE/docker/load/",target="/app" \
            --workdir="/ws" \
            -u $(id -u):$(id -g) \
            $DOCKER_IMAGE \
            mamba run -n main ${*: 2:99}
    ;;
    --shell|-s)
        docker run -i --rm -a stdout -a stderr \
            -e XDG_CACHE_HOME="/ws/scratch" \
            --mount type=bind,source="$HERE",target="/ws" \
            --workdir="/ws" \
            -u $(id -u):$(id -g) \
            $DOCKER_IMAGE
    ;;
    -tget)
        docker run $DOCKER_IMAGE \
            mamba run -n main fasterq-dump \
            -t $3 -O $3  ${*: 2:99}
    ;;
    -t)
        cd $HERE/src
        # python -m simple_meta setup -ref $HERE/scratch/test1/ref -c docker
        python -m simple_meta run -ref $HERE/scratch/test1/ref -i SRR22508334 -o $HERE/scratch/test1/ws -t 16

        # python -m simple_meta setup -ref $HERE/scratch/test1/ref -c singularity
    ;;
    *)
        echo "bad option"
        echo $1
    ;;
esac
